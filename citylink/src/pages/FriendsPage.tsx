import { useState } from 'react';
import { useStore } from '../store/useStore';
import type { User } from '../types';
import VisitRequestModal from '../components/VisitRequestModal';
import { Search, UserPlus, UserMinus, MapPin, CheckCircle, MessageCircle } from 'lucide-react';

export default function FriendsPage() {
  const { users, currentUser, addFriend, setActiveTab } = useStore();
  const [search, setSearch] = useState('');
  const [tab, setTab] = useState<'friends' | 'discover'>('friends');
  const [selected, setSelected] = useState<User | null>(null);

  const friendIds = currentUser?.friends ?? [];
  const friends = users.filter(u => friendIds.includes(u.id) && u.id !== currentUser?.id);
  const others = users.filter(u => !friendIds.includes(u.id) && u.id !== currentUser?.id);

  const filtered = (tab === 'friends' ? friends : others).filter(u =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    u.profession?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="bg-white px-4 py-3 border-b border-slate-100">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar pessoas..."
            className="w-full pl-9 pr-4 py-2 bg-slate-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        <div className="flex gap-2 mt-3">
          <button
            onClick={() => setTab('friends')}
            className={`flex-1 py-2 rounded-xl text-sm font-semibold transition-colors ${tab === 'friends' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}
          >
            Meus Amigos ({friends.length})
          </button>
          <button
            onClick={() => setTab('discover')}
            className={`flex-1 py-2 rounded-xl text-sm font-semibold transition-colors ${tab === 'discover' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}
          >
            Descobrir
          </button>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <p className="text-4xl mb-2">👥</p>
            <p className="text-sm">{tab === 'friends' ? 'Você ainda não tem amigos' : 'Nenhuma pessoa encontrada'}</p>
          </div>
        )}
        {filtered.map(user => (
          <div key={user.id} className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 flex gap-3">
            <div className="relative flex-shrink-0">
              <img src={user.avatar} alt={user.name} className="w-14 h-14 rounded-full object-cover" />
              <div className={`absolute bottom-0 right-0 w-4 h-4 rounded-full border-2 border-white ${user.isOnline ? 'bg-green-500' : 'bg-slate-300'}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="font-semibold text-slate-800 truncate">{user.name}</p>
                  <p className="text-xs text-slate-500">{user.profession}</p>
                  {user.homeLocation && (
                    <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                      <MapPin size={10} /> {user.homeLocation.address}
                    </p>
                  )}
                </div>
                {user.openToVisits && (
                  <span className="flex-shrink-0 flex items-center gap-1 text-xs bg-green-100 text-green-600 px-2 py-0.5 rounded-full">
                    <CheckCircle size={10} /> Aberto
                  </span>
                )}
              </div>
              <div className="flex gap-2 mt-3">
                {tab === 'friends' && (
                  <>
                    <button
                      onClick={() => setSelected(user)}
                      className="flex-1 py-2 text-xs font-semibold bg-blue-600 text-white rounded-xl flex items-center justify-center gap-1 hover:bg-blue-700 transition-colors"
                    >
                      <MapPin size={12} /> Visitar
                    </button>
                    <button
                      onClick={() => { setActiveTab('chat'); }}
                      className="flex items-center justify-center w-9 h-9 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
                    >
                      <MessageCircle size={16} />
                    </button>
                    <button
                      onClick={() => addFriend(user.id)}
                      className="flex items-center justify-center w-9 h-9 rounded-xl bg-red-50 text-red-400 hover:bg-red-100 transition-colors"
                      title="Remover amigo"
                    >
                      <UserMinus size={16} />
                    </button>
                  </>
                )}
                {tab === 'discover' && (
                  <button
                    onClick={() => addFriend(user.id)}
                    className="flex-1 py-2 text-xs font-semibold bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center gap-1 hover:bg-blue-100 transition-colors"
                  >
                    <UserPlus size={12} /> Adicionar Amigo
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {selected && <VisitRequestModal user={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
