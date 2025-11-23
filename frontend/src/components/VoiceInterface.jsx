import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Mic, MicOff } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const VoiceInterface = ({ isOpen, onClose }) => {
    const [isListening, setIsListening] = useState(false);
    const [transcription, setTranscription] = useState('');
    const [aiResponse, setAiResponse] = useState('');
    const [status, setStatus] = useState('Connecting...');
    const ws = useRef(null);
    const mediaRecorder = useRef(null);
    const audioContext = useRef(null);
    const analyser = useRef(null);
    const source = useRef(null);
    const [volume, setVolume] = useState(0);

    useEffect(() => {
        if (isOpen) {
            startVoiceSession();
        } else {
            stopVoiceSession();
        }
        return () => stopVoiceSession();
    }, [isOpen]);

    const startVoiceSession = async () => {
        try {
            const token = localStorage.getItem('accessToken');
            if (!token) {
                setStatus('Authentication missing');
                return;
            }

            const wsBaseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
            ws.current = new WebSocket(`${wsBaseUrl}/ai-service/ws/voice?token=${token}`);
            ws.current.binaryType = 'arraybuffer';

            ws.current.onopen = () => {
                setStatus('Listening...');
                startRecording();
            };

            ws.current.onmessage = async (event) => {
                const data = event.data;
                if (typeof data === 'string') {
                    const message = JSON.parse(data);
                    if (message.type === 'transcription') {
                        setTranscription(message.text);
                        setStatus('Processing...');
                    } else if (message.type === 'ai_response') {
                        setAiResponse(message.text);
                        setStatus('Speaking...');
                    } else if (message.type === 'status_update') {
                        setStatus(message.text);
                    }
                } else if (data instanceof ArrayBuffer) {
                    // Audio data
                    playAudio(data);
                }
            };

            ws.current.onerror = (error) => {
                console.error('WebSocket Error:', error);
                setStatus('Connection Error');
            };

            ws.current.onclose = () => {
                setStatus('Disconnected');
                stopRecording();
            };

        } catch (error) {
            console.error('Failed to start voice session:', error);
            setStatus('Error starting session');
        }
    };

    const isPlaying = useRef(false);
    const playbackSource = useRef(null);
    const playbackContext = useRef(null);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Audio Context for visualization & VAD
            audioContext.current = new (window.AudioContext || window.webkitAudioContext)();
            analyser.current = audioContext.current.createAnalyser();
            source.current = audioContext.current.createMediaStreamSource(stream);
            source.current.connect(analyser.current);
            analyser.current.fftSize = 256;

            const dataArray = new Uint8Array(analyser.current.frequencyBinCount);
            const updateVolume = () => {
                if (!analyser.current) return;
                analyser.current.getByteFrequencyData(dataArray);
                const avg = dataArray.reduce((a, b) => a + b) / dataArray.length;
                setVolume(avg);

                // VAD for Interruption
                // Threshold 10 is more sensitive for interruption
                if (avg > 10 && isPlaying.current) {
                    console.log("Interruption detected! Volume:", avg);
                    stopPlayback();
                    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                        ws.current.send(JSON.stringify({ type: "interrupt" }));
                    }
                }

                requestAnimationFrame(updateVolume);
            };
            updateVolume();

            // MediaRecorder for streaming
            let mimeType = 'audio/webm;codecs=opus';
            if (!MediaRecorder.isTypeSupported(mimeType)) {
                console.warn(`${mimeType} not supported, falling back to audio/webm`);
                mimeType = 'audio/webm';
            }

            mediaRecorder.current = new MediaRecorder(stream, { mimeType });

            mediaRecorder.current.ondataavailable = (event) => {
                if (event.data.size > 0 && ws.current && ws.current.readyState === WebSocket.OPEN) {
                    ws.current.send(event.data);
                }
            };

            mediaRecorder.current.start(250);
            setIsListening(true);

        } catch (error) {
            console.error('Error accessing microphone:', error);
            setStatus('Microphone Error');
        }
    };

    const stopPlayback = () => {
        if (playbackSource.current) {
            try {
                playbackSource.current.stop();
            } catch (e) {
                // Ignore if already stopped
            }
            playbackSource.current = null;
        }
        isPlaying.current = false;
        setStatus('Listening...');
    };

    const playAudio = async (arrayBuffer) => {
        try {
            if (!playbackContext.current) {
                playbackContext.current = new (window.AudioContext || window.webkitAudioContext)();
            }

            // If already playing, queue or stop?
            // For now, let's stop previous (barge-in on itself?) or just play.
            // Usually we want to play chunks sequentially.
            // But here we receive the full TTS response or chunks.
            // Let's assume sequential for now.

            const buffer = await playbackContext.current.decodeAudioData(arrayBuffer);
            const source = playbackContext.current.createBufferSource();
            source.buffer = buffer;
            source.connect(playbackContext.current.destination);

            playbackSource.current = source;
            isPlaying.current = true;

            source.onended = () => {
                isPlaying.current = false;
                setStatus('Listening...');
            };

            source.start(0);

        } catch (error) {
            console.error('Error playing audio:', error);
            isPlaying.current = false;
        }
    };

    const stopRecording = () => {
        stopPlayback();
        if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
            mediaRecorder.current.stop();
        }
        if (ws.current) {
            ws.current.close();
        }
        if (audioContext.current) {
            audioContext.current.close();
        }
        if (playbackContext.current) {
            playbackContext.current.close();
            playbackContext.current = null;
        }
        setIsListening(false);
        setVolume(0);
    };

    const stopVoiceSession = () => {
        stopRecording();
        setTranscription('');
        setAiResponse('');
        setStatus('Disconnected');
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/90 backdrop-blur-sm"
                >
                    <button
                        onClick={onClose}
                        className="absolute top-6 right-6 p-2 text-white/50 hover:text-white transition-colors"
                    >
                        <X size={32} />
                    </button>

                    <div className="flex flex-col items-center gap-8 w-full max-w-4xl px-6">
                        <div className="text-white/80 text-xl font-medium tracking-wide">
                            {status}
                        </div>

                        {/* Visualizer */}
                        <div className="relative flex items-center justify-center w-64 h-64 shrink-0">
                            {/* Base Circle */}
                            <motion.div
                                animate={{
                                    scale: 1 + (volume / 255) * 1.2,
                                    opacity: 0.1 + (volume / 255) * 0.2,
                                }}
                                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                className="absolute w-40 h-40 bg-white rounded-full blur-2xl opacity-10"
                            />
                            <motion.div
                                animate={{
                                    scale: 1 + (volume / 255) * 0.8,
                                    opacity: 0.2 + (volume / 255) * 0.3,
                                }}
                                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                                className="absolute w-32 h-32 bg-white rounded-full blur-xl opacity-20"
                            />
                            <motion.div
                                animate={{
                                    scale: 1 + (volume / 255) * 0.4,
                                }}
                                transition={{ type: "spring", stiffness: 400, damping: 15 }}
                                className="w-24 h-24 bg-white/90 rounded-full shadow-[0_0_30px_rgba(255,255,255,0.3)]"
                            />
                        </div>

                        {/* Transcription & Response */}
                        <div className="flex flex-col gap-6 text-center w-full">
                            {transcription && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                >
                                    <p className="text-2xl text-white/70 font-light leading-relaxed">
                                        "{transcription}"
                                    </p>
                                </motion.div>
                            )}

                            {aiResponse && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="prose prose-invert max-w-full break-words max-h-[40vh] overflow-y-auto px-4 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent"
                                >
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            p: ({ node, ...props }) => <p className="text-xl text-blue-400 font-medium leading-relaxed" {...props} />,
                                            strong: ({ node, ...props }) => <span className="font-bold text-blue-300" {...props} />,
                                            em: ({ node, ...props }) => <span className="italic text-blue-300" {...props} />,
                                            li: ({ node, ...props }) => <li className="text-blue-400 ml-4" {...props} />,
                                            ul: ({ node, ...props }) => <ul className="list-disc text-left inline-block" {...props} />,
                                            ol: ({ node, ...props }) => <ol className="list-decimal text-left inline-block" {...props} />
                                        }}
                                    >
                                        {aiResponse}
                                    </ReactMarkdown>
                                </motion.div>
                            )}
                        </div>

                        {/* Controls */}
                        <div className="flex gap-6 mt-8">
                            <button
                                onClick={() => {
                                    if (isListening) stopRecording();
                                    else startRecording();
                                }}
                                className={`p-4 rounded-full transition-all ${isListening
                                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                    : 'bg-white/10 text-white hover:bg-white/20'
                                    }`}
                            >
                                {isListening ? <Mic size={24} /> : <MicOff size={24} />}
                            </button>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default VoiceInterface;
