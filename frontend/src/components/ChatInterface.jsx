import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, User, PanelLeft, Quote, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '../utils/api';
import { useToast } from './ui/use-toast';
import veritasIcon from '../assets/veritas-nobg.svg';

const ChatInterface = ({ chatId, setChatId, isSidebarOpen, toggleSidebar }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [status, setStatus] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const [selectionRect, setSelectionRect] = useState(null);
    const [selectedText, setSelectedText] = useState('');
    const [quotedText, setQuotedText] = useState('');
    const [quotedMessageId, setQuotedMessageId] = useState(null);
    const [selectedMessageId, setSelectedMessageId] = useState(null);

    const ws = useRef(null);
    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);
    const isCreatingChatRef = useRef(false);
    const { toast } = useToast();

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [input]);



    // Fetch messages when chatId changes
    useEffect(() => {
        if (chatId) {
            if (isCreatingChatRef.current) {
                isCreatingChatRef.current = false;
            } else {
                setMessages([]);
                fetchMessages(chatId);
            }
        } else {
            setMessages([]);
        }
    }, [chatId]);

    const fetchMessages = async (id) => {
        setIsLoadingHistory(true);
        try {
            const res = await api.get(`/conversations/${id}`);
            setMessages(res.data.messages);
        } catch (error) {
            console.error("Failed to fetch messages", error);
            toast({
                variant: "destructive",
                title: "Error",
                description: "Failed to load messages.",
            });
        } finally {
            setIsLoadingHistory(false);
        }
    };

    // WebSocket Connection
    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (!token) return;

        const wsBaseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
        const wsUrl = `${wsBaseUrl}/ai-service/ws/chat?token=${token}&session_id=${chatId || 'temp'}`;
        ws.current = new WebSocket(wsUrl);

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleWsMessage(data);
        };

        return () => {
            if (ws.current) ws.current.close();
        };
    }, [chatId]);

    const handleWsMessage = (data) => {
        if (data.type === 'status_update') {
            setStatus(data.payload.message);
        } else if (data.type === 'assistant_chunk') {
            setStatus('');
            setIsTyping(false);
            setMessages((prev) => {
                const lastMsg = prev[prev.length - 1];
                if (lastMsg && lastMsg.role === 'assistant') {
                    return [
                        ...prev.slice(0, -1),
                        { ...lastMsg, content: lastMsg.content + data.payload.chunk }
                    ];
                } else {
                    return [...prev, { id: data.payload.message_id, role: 'assistant', content: data.payload.chunk }];
                }
            });
        } else if (data.type === 'message_update') {
            setIsTyping(false); // Stop thinking on update too
            // Handle in-place update
            const { message_id, content } = data.payload;
            setMessages((prev) => prev.map(msg =>
                msg.id === message_id ? { ...msg, content: content } : msg
            ));
        }
    };

    // Scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, status]);

    // Handle Text Selection
    useEffect(() => {
        const handleSelection = () => {
            const selection = window.getSelection();
            if (!selection || selection.isCollapsed) {
                setSelectionRect(null);
                setSelectedText('');
                setSelectedMessageId(null);
                return;
            }

            const text = selection.toString().trim();
            if (!text) return;

            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();

            // Find which message was selected
            let node = selection.anchorNode;
            while (node && node.nodeType !== 1) {
                node = node.parentNode;
            }
            const messageNode = node?.closest('[data-id]');
            const msgId = messageNode?.getAttribute('data-id');

            // Only show if selection is inside the chat area AND belongs to a message
            if (rect.width > 0 && rect.height > 0 && msgId) {
                setSelectionRect({
                    top: rect.top - 40,
                    left: rect.left + (rect.width / 2) - 50,
                });
                setSelectedText(text);
                setSelectedMessageId(msgId);
            }
        };

        document.addEventListener('mouseup', handleSelection);
        return () => document.removeEventListener('mouseup', handleSelection);
    }, []);

    const handleQuote = () => {
        setQuotedText(selectedText);
        setQuotedMessageId(selectedMessageId);
        setSelectionRect(null);
        window.getSelection().removeAllRanges();
    };

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMsg = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        setQuotedText('');
        setQuotedMessageId(null);
        setSelectedMessageId(null);
        setIsTyping(true);

        // If no chat ID, create one first
        let currentId = chatId;
        if (!currentId) {
            try {
                const res = await api.post('/conversations', { title: input.substring(0, 30) });
                currentId = res.data.id;
                isCreatingChatRef.current = true;
                setChatId(currentId);
            } catch (err) {
                console.error("Failed to create chat", err);
                toast({
                    variant: "destructive",
                    title: "Error",
                    description: "Failed to create new chat.",
                });
                return;
            }
        }

        // Send to WS
        setTimeout(() => {
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                const payload = {
                    type: 'user_message',
                    payload: {
                        text: userMsg.content,
                        selected_text: quotedText,
                        source_message_id: quotedText ? quotedMessageId : null
                    }
                };
                ws.current.send(JSON.stringify(payload));
            } else {
                console.error("WS not open");
                toast({
                    variant: "destructive",
                    title: "Connection Error",
                    description: "AI service is disconnected. Please refresh.",
                });
            }
        }, 500);
    };

    return (
        <div className="flex-1 flex flex-col h-screen bg-gray-950 relative">
            {/* Floating Edit Button */}
            {selectionRect && (
                <div
                    className="fixed z-50 bg-gray-800 text-white px-3 py-1.5 rounded-lg shadow-xl cursor-pointer hover:bg-gray-700 transition-all flex items-center gap-2 border border-gray-700 animate-in"
                    style={{ top: selectionRect.top, left: selectionRect.left }}
                    onMouseDown={(e) => {
                        e.preventDefault(); // Prevent losing selection
                        handleQuote();
                    }}
                >
                    <Quote size={14} />
                    <span className="text-sm font-medium">Edit with Veritas</span>
                </div>
            )}

            {/* Header / Toggle Button */}
            <div className="absolute top-4 left-4 z-10">
                <button
                    onClick={toggleSidebar}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
                    title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
                >
                    <PanelLeft size={24} />
                </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 pt-16 space-y-8 scroll-smooth">
                {!chatId && messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500 opacity-50">
                        <img src={veritasIcon} alt="Veritas" className="w-10 h-10 mb-4" />
                        <p className="text-lg font-medium">Start a new research session with Veritas</p>
                    </div>
                )}

                {isLoadingHistory && (
                    <div className="flex justify-center py-10">
                        <Loader2 className="animate-spin text-gray-500" size={24} />
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        data-id={msg.id}
                        className={`flex gap-6 max-w-3xl mx-auto animate-in group ${msg.role === 'assistant' ? '' : 'flex-row-reverse'}`}
                    >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 shadow-md ${msg.role === 'assistant'
                            ? 'bg-transparent'
                            : 'bg-gray-700'
                            }`}>
                            {msg.role === 'assistant' ? <img src={veritasIcon} alt="Veritas" className="w-8 h-8" /> : <User size={16} className="text-gray-300" />}
                        </div>

                        <div className={`prose prose-invert max-w-none flex-1 ${msg.role === 'user' ? 'text-right' : ''
                            }`}>
                            <div className={`inline-block rounded-2xl px-6 py-4 shadow-sm ${msg.role === 'user'
                                ? 'bg-gray-800 text-gray-100 rounded-tr-sm text-left max-w-[80%] ml-auto'
                                : 'bg-transparent text-gray-300 pl-0'
                                }`}>
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                        h1: ({ node, ...props }) => <h1 className="text-2xl font-bold text-white mb-4 mt-6" {...props} />,
                                        h2: ({ node, ...props }) => <h2 className="text-xl font-semibold text-gray-100 mb-3 mt-5" {...props} />,
                                        h3: ({ node, ...props }) => <h3 className="text-lg font-medium text-gray-200 mb-2 mt-4" {...props} />,
                                        p: ({ node, ...props }) => <p className="mb-4 leading-relaxed" {...props} />,
                                        ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2" {...props} />,
                                        ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2" {...props} />,
                                        li: ({ node, ...props }) => <li className="text-gray-300" {...props} />,
                                        a: ({ node, ...props }) => <a className="text-blue-400 hover:text-blue-300 underline transition-colors" target="_blank" rel="noopener noreferrer" {...props} />,
                                        code: ({ node, inline, className, children, ...props }) => {
                                            return inline ? (
                                                <code className="bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono text-pink-400" {...props}>
                                                    {children}
                                                </code>
                                            ) : (
                                                <div className="bg-gray-900 rounded-lg p-4 my-4 overflow-x-auto border border-gray-800">
                                                    <code className="text-sm font-mono text-gray-200 block" {...props}>
                                                        {children}
                                                    </code>
                                                </div>
                                            );
                                        },
                                        table: ({ node, ...props }) => (
                                            <div className="overflow-x-auto my-6 rounded-lg border border-gray-800">
                                                <table className="min-w-full divide-y divide-gray-800" {...props} />
                                            </div>
                                        ),
                                        thead: ({ node, ...props }) => <thead className="bg-gray-900" {...props} />,
                                        th: ({ node, ...props }) => <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider" {...props} />,
                                        tbody: ({ node, ...props }) => <tbody className="bg-gray-950 divide-y divide-gray-800" {...props} />,
                                        tr: ({ node, ...props }) => <tr className="hover:bg-gray-900/50 transition-colors" {...props} />,
                                        td: ({ node, ...props }) => <td className="px-4 py-3 text-sm text-gray-300 whitespace-nowrap" {...props} />,
                                        blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-gray-700 pl-4 italic text-gray-400 my-4" {...props} />,
                                    }}
                                >
                                    {msg.content}
                                </ReactMarkdown>
                            </div>
                        </div>
                    </div>
                ))}

                {/* Thinking Animation */}
                {isTyping && !status && (
                    <div className="flex gap-6 max-w-3xl mx-auto animate-in">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 shadow-md bg-transparent">
                            <img src={veritasIcon} alt="Veritas" className="w-8 h-8" />
                        </div>
                        <div className="flex items-center h-full py-4">
                            <div className="flex space-x-1">
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                            </div>
                            <span className="ml-3 text-sm text-gray-400 font-medium">Thinking...</span>
                        </div>
                    </div>
                )}

                {/* Status Indicator */}
                {status && (
                    <div className="flex items-center gap-3 text-gray-400 text-sm max-w-3xl mx-auto pl-14 animate-pulse">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                        {status}
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-6 bg-gray-950/80 backdrop-blur-sm border-t border-gray-800/50">
                <div className="max-w-3xl mx-auto relative">
                    {/* Quoted Text Preview */}
                    {quotedText && (
                        <div className="mb-4 p-3 bg-gray-800/50 rounded-lg border-l-4 border-green-500 flex justify-between items-start animate-in">
                            <div className="text-sm text-gray-300 line-clamp-3 italic">
                                "{quotedText}"
                            </div>
                            <button
                                onClick={() => setQuotedText('')}
                                className="text-gray-500 hover:text-white transition-colors ml-2"
                            >
                                <X size={16} />
                            </button>
                        </div>
                    )}

                    <form onSubmit={sendMessage} className="relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-green-500 to-blue-600 rounded-xl opacity-20 group-hover:opacity-40 transition duration-500 blur"></div>
                        <textarea
                            ref={textareaRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    sendMessage(e);
                                }
                            }}
                            placeholder={quotedText ? "How should I edit this text?" : "Ask Veritas to research anything..."}
                            className="relative w-full bg-gray-900 text-white rounded-xl pl-6 pr-14 py-4 shadow-2xl focus:outline-none focus:ring-0 placeholder-gray-500 text-lg resize-none min-h-[60px] max-h-[200px] overflow-y-auto"
                            rows={1}
                        />
                        <button
                            type="submit"
                            disabled={!input.trim()}
                            className="absolute right-3 top-3 p-2 bg-gray-800 text-gray-400 rounded-lg hover:text-white hover:bg-gray-700 transition-all disabled:opacity-50 disabled:hover:bg-gray-800"
                        >
                            <Send size={20} />
                        </button>
                    </form>
                    <div className="text-xs text-center text-gray-600 mt-3 font-medium tracking-wide">
                        VERITAS AI CAN MAKE MISTAKES. VERIFY IMPORTANT INFORMATION.
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
