import { useStore } from '../store/useStore';
import type { AppTab } from '../types';
import { MapPin, Users, Building2, Calendar, MessageCircle, User, Church, Bell } from 'lucide-react';
import NotificationPanel from './NotificationPanel';
import { useState } from 'react';

const NAV_ITEMS: { tab: AppTab; label: string; icon: React.ReactNode }[] = [
  { tab: 'map', label: 'Mapa', icon: <MapPin size={22} /> },
  { tab: 'friends', label: 'Amigos', icon: <Users size={22} /> },
  { tab: 'business', label: 'Empresas', icon: <Building2 size={22} /> },
  { tab: 'events', label: 'Eventos', icon: <Calendar size={22} /> },
  { tab: 'chat', label: 'Chat', icon: <MessageCircle size={22} /> },
  { tab: 'community', label: 'Igreja', icon: <Church size={22} /> },
  { tab: 'profile', label: 'Perfil', icon: <User size={22} /> },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { activeTab, setActiveTab, notifications } = useStore();
  const unread = notifications.filter(n => !n.read).length;
  const [showNotif, setShowNotif] = useState(false);

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-blue-600 text-white px-4 py-3 flex items-center justify-between shadow-lg flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
            <span className="text-blue-600 font-bold text-sm">CL</span>
          </div>
          <span className="font-bold text-lg tracking-tight">CityLink</span>
        </div>
        <button
          onClick={() => setShowNotif(!showNotif)}
          className="relative p-2 rounded-full hover:bg-blue-700 transition-colors"
        >
          <Bell size={22} />
          {unread > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </button>
      </header>

      {showNotif && <NotificationPanel onClose={() => setShowNotif(false)} />}

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      {/* Bottom Navigation */}
      <nav className="bg-white border-t border-slate-200 flex-shrink-0 shadow-[0_-2px_12px_rgba(0,0,0,0.08)]">
        <div className="flex">
          {NAV_ITEMS.map(({ tab, label, icon }) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 flex flex-col items-center py-2 px-1 transition-colors ${
                activeTab === tab
                  ? 'text-blue-600'
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              {icon}
              <span className="text-[10px] mt-0.5 font-medium">{label}</span>
              {activeTab === tab && (
                <div className="absolute bottom-0 w-8 h-0.5 bg-blue-600 rounded-full" />
              )}
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
}
