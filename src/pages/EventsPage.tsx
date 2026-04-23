import { useState } from 'react';
import { useStore } from '../store/useStore';
import type { Event } from '../types';
import { Calendar, MapPin, Users, CheckCircle } from 'lucide-react';

const TYPE_MAP: Record<Event['type'], { label: string; color: string; emoji: string }> = {
  social: { label: 'Social', color: 'bg-blue-100 text-blue-600', emoji: '🎉' },
  religious: { label: 'Religioso', color: 'bg-purple-100 text-purple-600', emoji: '✝️' },
  volunteer: { label: 'Voluntariado', color: 'bg-green-100 text-green-600', emoji: '🤝' },
  business: { label: 'Negócios', color: 'bg-amber-100 text-amber-600', emoji: '💼' },
};

function formatDate(d: Date) {
  return d.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: 'short' });
}

export default function EventsPage() {
  const { events, currentUser, joinEvent, users } = useStore();
  const [filter, setFilter] = useState<Event['type'] | 'all'>('all');

  const filtered = filter === 'all' ? events : events.filter(e => e.type === filter);
  const sorted = [...filtered].sort((a, b) => a.date.getTime() - b.date.getTime());

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Filters */}
      <div className="bg-white px-4 py-3 border-b border-slate-100">
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {(['all', 'social', 'religious', 'volunteer', 'business'] as const).map(t => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                filter === t ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {t === 'all' ? '📅 Todos' : `${TYPE_MAP[t].emoji} ${TYPE_MAP[t].label}`}
            </button>
          ))}
        </div>
      </div>

      {/* Events list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {sorted.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <p className="text-4xl mb-2">📅</p>
            <p className="text-sm">Nenhum evento encontrado</p>
          </div>
        )}
        {sorted.map(event => {
          const joined = currentUser ? event.attendees.includes(currentUser.id) : false;
          const typeInfo = TYPE_MAP[event.type];
          const organizer = users.find(u => u.id === event.organizerId);

          return (
            <div key={event.id} className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
              {/* Date banner */}
              <div className={`px-4 py-2 flex items-center gap-2 ${typeInfo.color}`}>
                <Calendar size={14} />
                <span className="text-xs font-semibold uppercase">{formatDate(event.date)}</span>
                <span className={`ml-auto text-xs font-semibold px-2 py-0.5 rounded-full bg-white/60`}>
                  {typeInfo.emoji} {typeInfo.label}
                </span>
              </div>

              <div className="p-4">
                <h3 className="font-bold text-slate-800">{event.title}</h3>
                <p className="text-sm text-slate-500 mt-1 line-clamp-2">{event.description}</p>

                <div className="mt-3 space-y-1.5">
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <MapPin size={12} className="text-blue-500" /> {event.location.address}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Users size={12} className="text-blue-500" />
                    <span>{event.attendees.length} participante{event.attendees.length !== 1 ? 's' : ''}</span>
                    {organizer && <span className="text-slate-400">• por {organizer.name}</span>}
                  </div>
                </div>

                {/* Attendee avatars */}
                {event.attendees.length > 0 && (
                  <div className="flex -space-x-2 mt-3">
                    {event.attendees.slice(0, 5).map(aid => {
                      const att = users.find(u => u.id === aid);
                      return att ? (
                        <img key={aid} src={att.avatar} alt={att.name}
                          className="w-7 h-7 rounded-full border-2 border-white object-cover" />
                      ) : null;
                    })}
                    {event.attendees.length > 5 && (
                      <div className="w-7 h-7 rounded-full bg-slate-200 border-2 border-white flex items-center justify-center">
                        <span className="text-[10px] text-slate-600">+{event.attendees.length - 5}</span>
                      </div>
                    )}
                  </div>
                )}

                <button
                  onClick={() => currentUser && joinEvent(event.id)}
                  className={`mt-4 w-full py-2.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${
                    joined
                      ? 'bg-green-50 text-green-600 border border-green-200 hover:bg-green-100'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {joined ? <><CheckCircle size={14} /> Confirmado</> : 'Participar'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
