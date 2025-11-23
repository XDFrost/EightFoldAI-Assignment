import { useEffect, useState } from 'react';
import { MessageSquare, Plus, LogOut } from 'lucide-react';
import api from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useToast } from './ui/use-toast';
import veritasIcon from '../assets/veritas-nobg.svg';

const Sidebar = ({ currentChatId, onSelectChat, onNewChat }) => {
    const [conversations, setConversations] = useState([]);
    const { logout, user } = useAuth();
    const navigate = useNavigate();
    const { toast } = useToast();

    useEffect(() => {
        fetchConversations();
    }, [currentChatId]); // Refresh when chat changes (e.g. new title)

    const fetchConversations = async () => {
        try {
            const res = await api.get('/conversations');
            setConversations(res.data);
        } catch (error) {
            console.error("Failed to fetch conversations", error);
            toast({
                variant: "destructive",
                title: "Error",
                description: "Failed to load history.",
            });
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="w-64 bg-gray-950 flex flex-col h-screen border-r border-gray-800">
            {/* Branding */}
            <div className="p-6 flex items-center gap-2 text-white font-bold text-xl tracking-tight">
                <img src={veritasIcon} alt="Veritas" className="w-8 h-8" />
                Veritas
            </div>

            <div className="px-4 pb-4">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center gap-2 bg-white text-black rounded-md p-3 hover:bg-gray-200 transition font-medium text-sm shadow-sm"
                >
                    <Plus size={16} />
                    New Chat
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2 py-2">
                <div className="text-xs font-semibold text-gray-500 px-4 py-2 uppercase tracking-wider">History</div>
                {conversations.map((chat) => (
                    <button
                        key={chat.id}
                        onClick={() => onSelectChat(chat.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-md cursor-pointer text-sm mb-1 transition-all ${currentChatId === chat.id ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200'
                            }`}
                    >
                        <MessageSquare size={16} className="opacity-70" />
                        <span className="truncate">{chat.title || 'New Chat'}</span>
                    </button>
                ))}
            </div>

            <div className="p-4 border-t border-gray-800 bg-gray-950">
                <div className="flex items-center gap-3 mb-4 px-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-xs shadow-md">
                        {user?.email[0].toUpperCase()}
                    </div>
                    <div className="text-sm text-gray-300 truncate w-32 font-medium">{user?.email}</div>
                </div>
                <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 text-gray-500 hover:text-red-400 transition text-sm px-2 w-full"
                >
                    <LogOut size={16} />
                    Log out
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
