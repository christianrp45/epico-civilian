import { useState } from 'react';
import { useStore } from '../store/useStore';
import { MapPin, Phone, Mail, Briefcase, Church, LogOut, Edit3, Check, ToggleLeft, ToggleRight } from 'lucide-react';

export default function ProfilePage() {
  const { currentUser, logout, toggleOpenToVisits } = useStore();
  const [editing, setEditing] = useState(false);
  const [bio, setBio] = useState(currentUser?.bio ?? '');

  if (!currentUser) return null;

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-slate-50">
      {/* Header banner */}
      <div className="bg-gradient-to-br from-blue-600 to-blue-800 h-32 relative flex-shrink-0">
        <div className="absolute -bottom-12 left-1/2 -translate-x-1/2">
          <img
            src={currentUser.avatar}
            alt={currentUser.name}
            className="w-24 h-24 rounded-full object-cover border-4 border-white shadow-lg"
          />
        </div>
      </div>

      <div className="pt-16 px-4 pb-8">
        {/* Name and profession */}
        <div className="text-center mb-1">
          <h2 className="text-xl font-bold text-slate-800">{currentUser.name}</h2>
          <p className="text-slate-500 text-sm">{currentUser.profession}</p>
        </div>

        {/* Open to visits toggle */}
        <div className="flex items-center justify-center gap-3 my-4">
          <button
            onClick={toggleOpenToVisits}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm transition-colors ${
              currentUser.openToVisits
                ? 'bg-green-100 text-green-700 border border-green-200'
                : 'bg-slate-100 text-slate-500 border border-slate-200'
            }`}
          >
            {currentUser.openToVisits
              ? <><ToggleRight size={18} /> Aberto para visitas</>
              : <><ToggleLeft size={18} /> Fechado para visitas</>}
          </button>
        </div>

        {/* Bio */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Sobre mim</span>
            <button onClick={() => setEditing(!editing)} className="text-blue-500">
              {editing ? <Check size={16} /> : <Edit3 size={16} />}
            </button>
          </div>
          {editing ? (
            <textarea
              value={bio}
              onChange={e => setBio(e.target.value)}
              className="w-full text-sm text-slate-700 border border-slate-200 rounded-xl p-2 resize-none h-20 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          ) : (
            <p className="text-sm text-slate-600">{bio || 'Nenhuma descrição ainda.'}</p>
          )}
        </div>

        {/* Info */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 divide-y divide-slate-50 mb-4">
          {[
            { icon: <Mail size={16} />, label: 'E-mail', value: currentUser.email },
            { icon: <Phone size={16} />, label: 'Telefone', value: currentUser.phone },
            { icon: <Briefcase size={16} />, label: 'Profissão', value: currentUser.profession },
            currentUser.homeLocation ? { icon: <MapPin size={16} />, label: 'Endereço', value: currentUser.homeLocation.address } : null,
          ].filter(Boolean).map((item, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3">
              <span className="text-blue-500">{item!.icon}</span>
              <div>
                <p className="text-xs text-slate-400">{item!.label}</p>
                <p className="text-sm text-slate-700">{item!.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Church */}
        {currentUser.churchId && (
          <div className="bg-white rounded-2xl p-4 shadow-sm border border-slate-100 mb-4 flex items-center gap-3">
            <Church size={20} className="text-purple-500" />
            <div>
              <p className="text-xs text-slate-400">Igreja</p>
              <p className="text-sm font-semibold text-slate-700">Igreja Comunidade da Graça</p>
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          {[
            { label: 'Amigos', value: currentUser.friends.length },
            { label: 'Visitas', value: 12 },
            { label: 'Pontos', value: 340 },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-2xl p-3 shadow-sm border border-slate-100 text-center">
              <p className="text-2xl font-bold text-blue-600">{s.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className="w-full py-3 rounded-xl bg-red-50 text-red-500 font-semibold flex items-center justify-center gap-2 hover:bg-red-100 transition-colors border border-red-100"
        >
          <LogOut size={16} /> Sair da Conta
        </button>
      </div>
    </div>
  );
}
