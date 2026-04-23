import { useStore } from '../store/useStore';
import { X, CheckCircle, XCircle, MessageCircle, MapPin, Calendar, Bell } from 'lucide-react';
import type { Notification } from '../types';

const ICON_MAP: Record<Notification['type'], React.ReactNode> = {
  visit_request: <MapPin size={16} className="text-blue-500" />,
  visit_accepted: <CheckCircle size={16} className="text-green-500" />,
  visit_declined: <XCircle size={16} className="text-red-500" />,
  message: <MessageCircle size={16} className="text-purple-500" />,
  event: <Calendar size={16} className="text-orange-500" />,
  nearby: <MapPin size={16} className="text-blue-500" />,
};

export default function NotificationPanel({ onClose }: { onClose: () => void }) {
  const { notifications, markNotificationsRead } = useStore();

  const handleOpen = () => {
    markNotificationsRead();
  };

  return (
    <div className="absolute top-14 right-2 z-50 w-80 bg-white rounded-xl shadow-2xl border border-slate-200 fade-in">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
        <div className="flex items-center gap-2 font-semibold text-slate-700">
          <Bell size={16} /> Notificações
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
          <X size={18} />
        </button>
      </div>
      <div className="max-h-96 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-sm">
            Nenhuma notificação
          </div>
        ) : (
          [...notifications].reverse().map(n => (
            <div
              key={n.id}
              onClick={handleOpen}
              className={`px-4 py-3 border-b border-slate-50 flex gap-3 cursor-pointer hover:bg-slate-50 ${!n.read ? 'bg-blue-50' : ''}`}
            >
              <div className="mt-0.5 flex-shrink-0">{ICON_MAP[n.type]}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800">{n.title}</p>
                <p className="text-xs text-slate-500 mt-0.5">{n.body}</p>
                <p className="text-xs text-slate-400 mt-1">
                  {n.createdAt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              {!n.read && <div className="w-2 h-2 bg-blue-500 rounded-full mt-1 flex-shrink-0" />}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
