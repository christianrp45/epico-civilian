import { useState } from 'react';
import { useStore } from '../store/useStore';
import type { User } from '../types';
import { Send, ArrowLeft, MessageCircle } from 'lucide-react';

function ConversationList({ onSelect }: { onSelect: (user: User) => void }) {
  const { conversations, users, currentUser } = useStore();
  const friends = users.filter(u => currentUser?.friends.includes(u.id) && u.id !== currentUser.id);

  const convUsers = conversations.map(c => {
    const u = users.find(x => x.id === c.userId);
    return u ? { user: u, conv: c } : null;
  }).filter(Boolean) as { user: User; conv: typeof conversations[0] }[];

  const withoutConv = friends.filter(f => !conversations.find(c => c.userId === f.id));

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 bg-white border-b border-slate-100">
        <h2 className="font-bold text-slate-800">Mensagens</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {convUsers.length === 0 && withoutConv.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <MessageCircle size={40} className="mx-auto mb-2 text-slate-200" />
            <p className="text-sm">Nenhuma conversa ainda</p>
            <p className="text-xs mt-1">Adicione amigos para conversar</p>
          </div>
        )}

        {/* Conversations */}
        {convUsers.map(({ user, conv }) => (
          <button
            key={user.id}
            onClick={() => onSelect(user)}
            className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 border-b border-slate-50 text-left"
          >
            <div className="relative flex-shrink-0">
              <img src={user.avatar} alt={user.name} className="w-12 h-12 rounded-full object-cover" />
              <div className={`absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full border-2 border-white ${user.isOnline ? 'bg-green-500' : 'bg-slate-300'}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-slate-800 text-sm">{user.name}</p>
                <p className="text-xs text-slate-400">
                  {conv.lastMessage.createdAt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              <div className="flex items-center justify-between mt-0.5">
                <p className="text-xs text-slate-500 truncate max-w-[180px]">
                  {conv.lastMessage.fromUserId === currentUser?.id ? 'Você: ' : ''}{conv.lastMessage.content}
                </p>
                {conv.unreadCount > 0 && (
                  <span className="flex-shrink-0 bg-blue-600 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                    {conv.unreadCount}
                  </span>
                )}
              </div>
            </div>
          </button>
        ))}

        {/* Friends without conversations */}
        {withoutConv.length > 0 && (
          <>
            <p className="px-4 py-2 text-xs font-semibold text-slate-400 uppercase tracking-wide bg-slate-50">Amigos</p>
            {withoutConv.map(user => (
              <button
                key={user.id}
                onClick={() => onSelect(user)}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 border-b border-slate-50 text-left"
              >
                <div className="relative flex-shrink-0">
                  <img src={user.avatar} alt={user.name} className="w-12 h-12 rounded-full object-cover" />
                  <div className={`absolute bottom-0 right-0 w-3.5 h-3.5 rounded-full border-2 border-white ${user.isOnline ? 'bg-green-500' : 'bg-slate-300'}`} />
                </div>
                <div>
                  <p className="font-semibold text-slate-800 text-sm">{user.name}</p>
                  <p className="text-xs text-slate-400">{user.isOnline ? 'Online' : 'Offline'}</p>
                </div>
              </button>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function ChatThread({ partner, onBack }: { partner: User; onBack: () => void }) {
  const { messages, currentUser, sendMessage } = useStore();
  const [text, setText] = useState('');

  const thread = messages
    .filter(m => (m.fromUserId === currentUser?.id && m.toUserId === partner.id) ||
      (m.fromUserId === partner.id && m.toUserId === currentUser?.id))
    .sort((a, b) => a.createdAt.getTime() - b.createdAt.getTime());

  const handleSend = () => {
    if (!text.trim()) return;
    sendMessage(partner.id, text.trim());
    setText('');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-slate-100 px-4 py-3 flex items-center gap-3 flex-shrink-0">
        <button onClick={onBack} className="text-slate-400 hover:text-slate-600">
          <ArrowLeft size={20} />
        </button>
        <div className="relative">
          <img src={partner.avatar} alt={partner.name} className="w-9 h-9 rounded-full object-cover" />
          <div className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${partner.isOnline ? 'bg-green-500' : 'bg-slate-300'}`} />
        </div>
        <div>
          <p className="font-semibold text-slate-800 text-sm">{partner.name}</p>
          <p className="text-xs text-slate-400">{partner.isOnline ? 'Online' : 'Offline'}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50">
        {thread.length === 0 && (
          <div className="text-center py-8 text-slate-400 text-sm">
            Nenhuma mensagem ainda. Diga olá!
          </div>
        )}
        {thread.map(msg => {
          const isMe = msg.fromUserId === currentUser?.id;
          return (
            <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                isMe ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-white text-slate-800 shadow-sm border border-slate-100 rounded-bl-sm'
              }`}>
                <p className="text-sm">{msg.content}</p>
                <p className={`text-[10px] mt-1 ${isMe ? 'text-blue-200' : 'text-slate-400'}`}>
                  {msg.createdAt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Input */}
      <div className="bg-white border-t border-slate-100 px-4 py-3 flex items-center gap-2 flex-shrink-0">
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Digite uma mensagem..."
          className="flex-1 px-4 py-2.5 bg-slate-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <button
          onClick={handleSend}
          disabled={!text.trim()}
          className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [partner, setPartner] = useState<User | null>(null);

  if (partner) {
    return <ChatThread partner={partner} onBack={() => setPartner(null)} />;
  }
  return <ConversationList onSelect={setPartner} />;
}
