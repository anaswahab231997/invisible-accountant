import { useState, useEffect, useRef } from 'react';
import type { FormEvent } from 'react';
import MessageBubble from './MessageBubble';

interface Message {
  id: string;
  text: string;
  isSent: boolean;
}

export default function ChatSimulator() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: "Hi! I'm Emma, your Invisible Accountant. 👋 Just text me your business expenses or snap a picture of your receipts, and I'll make sure they are perfectly sorted for HMRC!", isSent: false }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [turnCount, setTurnCount] = useState(1);
  const [currentIntakeId, setCurrentIntakeId] = useState<number | null>(null);
  
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    const handleWsUpdate = (e: Event) => {
      const { detail } = e as CustomEvent;
      if (detail.type === 'INTAKE_UPDATE' && detail.intake_id === currentIntakeId) {
        setIsTyping(false);
        const latest = detail.result;
        
        if (latest.is_ambiguous) {
            const question = latest.auditor_question || "Could you clarify if this was for business? 🤔";
            setMessages(prev => [...prev, { id: Date.now().toString(), text: question, isSent: false }]);
            setTurnCount(prev => prev + 1);
        } else {
            setMessages(prev => [...prev, { 
                id: Date.now().toString(), 
                text: `✅ All sorted! I've logged £${latest.amount} at ${latest.vendor} under '${latest.category}'.`, 
                isSent: false 
            }]);
            setTurnCount(1);
        }
      }
    };

    window.addEventListener('ws-update', handleWsUpdate);
    return () => window.removeEventListener('ws-update', handleWsUpdate);
  }, [currentIntakeId]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const text = inputValue.trim();
    if (!text) return;

    setMessages(prev => [...prev, { id: Date.now().toString(), text, isSent: true }]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch('/api/simulate_whatsapp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender_id: 'user_local_tester',
          message: text,
          turn_count: turnCount
        })
      });
      const data = await response.json();
      if (data.intake_id) {
        setCurrentIntakeId(data.intake_id);
      }
    } catch (err) {
      console.error(err);
      setIsTyping(false);
      setMessages(prev => [...prev, { id: Date.now().toString(), text: "Error: Could not connect to the server.", isSent: false }]);
    }
  };

  return (
    <div className="w-full max-w-md bg-white rounded-xl shadow-lg overflow-hidden flex flex-col h-[80vh] border border-gray-200">
      <header className="bg-green-600 text-white p-4 flex items-center shadow-md">
        <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center text-xl font-bold mr-3 overflow-hidden">
          <img src="https://i.pravatar.cc/150?img=47" alt="Emma Profile" className="w-full h-full object-cover" />
        </div>
        <div>
          <h2 className="font-bold text-lg leading-tight">Emma</h2>
          <p className="text-xs text-green-200" aria-live="polite">Online</p>
        </div>
      </header>

      <div className="flex-1 bg-[#e5ddd5] p-4 overflow-y-auto flex flex-col" aria-label="Chat messages">
        {messages.map(msg => (
          <MessageBubble key={msg.id} text={msg.text} isSent={msg.isSent} />
        ))}
        {isTyping && <MessageBubble text="typing..." isSent={false} isTyping={true} />}
        <div ref={endOfMessagesRef} />
      </div>

      <form onSubmit={handleSubmit} className="bg-gray-100 p-3 flex items-center border-t border-gray-200">
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type a message..." 
          aria-label="Message input"
          className="flex-1 px-4 py-2 rounded-full border border-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500 shadow-sm"
        />
        <button 
          type="submit" 
          aria-label="Send message"
          className="ml-3 bg-green-500 hover:bg-green-600 text-white rounded-full p-2 h-10 w-10 flex items-center justify-center shadow-md transition-colors focus:outline-none focus:ring-2 focus:ring-green-700"
        >
          ➤
        </button>
      </form>
    </div>
  );
}
