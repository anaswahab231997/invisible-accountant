import { useState, useEffect } from 'react';
import ChatSimulator from './components/ChatSimulator';
import Dashboard from './components/Dashboard';

export default function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'dashboard'>('chat');

  useEffect(() => {
    // Basic WebSocket connection to receive updates
    const wsUrl = (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws/queue';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => console.log('WebSocket connected');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("WebSocket event:", data);
        // We dispatch a custom event so child components can react
        window.dispatchEvent(new CustomEvent('ws-update', { detail: data }));
      } catch (e) {
        console.error(e);
      }
    };
    ws.onclose = () => console.log('WebSocket disconnected');

    return () => {
      ws.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
      <header className="bg-white shadow-sm px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Invisible Accountant</h1>
        <nav className="space-x-4">
          <button 
            onClick={() => setActiveTab('chat')}
            aria-current={activeTab === 'chat' ? 'page' : undefined}
            className={`px-4 py-2 rounded-md transition-colors ${activeTab === 'chat' ? 'bg-green-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            WhatsApp Simulator
          </button>
          <button 
            onClick={() => setActiveTab('dashboard')}
            aria-current={activeTab === 'dashboard' ? 'page' : undefined}
            className={`px-4 py-2 rounded-md transition-colors ${activeTab === 'dashboard' ? 'bg-green-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            Queue Dashboard
          </button>
        </nav>
      </header>

      <main className="flex-1 p-6 flex justify-center items-start">
        {activeTab === 'chat' ? <ChatSimulator /> : <Dashboard />}
      </main>
    </div>
  );
}
