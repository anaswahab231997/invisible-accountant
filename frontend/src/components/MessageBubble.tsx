interface MessageBubbleProps {
    text: string;
    isSent: boolean;
    isTyping?: boolean;
  }
  
  export default function MessageBubble({ text, isSent, isTyping }: MessageBubbleProps) {
    return (
      <div 
        className={`px-4 py-2 rounded-lg shadow-sm max-w-[80%] text-sm mb-3 ${isSent ? 'self-end bg-[#dcf8c6]' : 'self-start bg-white'}`}
        role="log"
        aria-live="polite"
      >
        {isTyping ? (
          <span className="italic text-gray-500">{text}</span>
        ) : (
          <span className="text-gray-800">{text}</span>
        )}
      </div>
    );
  }
