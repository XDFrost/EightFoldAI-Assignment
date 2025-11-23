import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';

const Home = () => {
    const [currentChatId, setCurrentChatId] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    const handleSelectChat = (id) => {
        setCurrentChatId(id);
    };

    const handleNewChat = () => {
        setCurrentChatId(null);
    };

    return (
        <div className="flex h-screen bg-gray-950">
            <div className={`${isSidebarOpen ? 'w-64' : 'w-0'} transition-all duration-300 ease-in-out overflow-hidden`}>
                <Sidebar
                    currentChatId={currentChatId}
                    onSelectChat={handleSelectChat}
                    onNewChat={handleNewChat}
                />
            </div>
            <ChatInterface
                chatId={currentChatId}
                setChatId={setCurrentChatId}
                isSidebarOpen={isSidebarOpen}
                toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
            />
        </div>
    );
};

export default Home;
