import { useState } from 'react';
import { useStore } from '../store/useStore';
import { MapPin, Phone, Mail, Briefcase, Church, LogOut, Edit3, Check, HandHeart } from 'lucide-react';

export default function ProfilePage() {
  const { currentUser, logout, toggleOpenToVisits } = useStore();
  const [editing, setEditing] = useState(false);
  const [helpOffer, setHelpOffer] = useState(currentUser?.helpOffer ?? '');

  if (!currentUser) return null;

  const isMesaPosta = currentUser.openToVisits;

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-slate-50">
      {/* Header banner */}
      <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 h-32 relative flex-shrink-0">
        <div className="absolute -bottom-12 left-1/2 -translate-x-1/2">
          <img
            src={currentUser.avatar}
            alt={currentUser.name}
            className="w-24 h-24 rounded-full object-cover border-4 border-white shadow-lg"
          />
        </div>
      </div>

      <div className="pt-16 px-4 pb-8">
        {/* Nome e profissão */}
        <div className="text-center mb-4">
          <h2 className="text-xl font-bold text-slate-800">{currentUser.name}</h2>
          <p className="text-slate-500 text-sm">{currentUser.profession}</p>
          {currentUser.churchId && (
            <p className="text-xs text-indigo-500 mt-0.5 flex items-center justify-center gap-1">
              <Church size={11} /> Igreja Comunidade da Graça
            </p>
          )}
        </div>

        {/* Toggle Mesa Posta / Requer Aviso */}
        <button
          onClick={toggleOpenToVisits}
          className={`w-full flex items-center justify-between px-4 py-3 rounded-2xl mb-4 transition-all ${
            isMesaPosta
              ? 'bg-emerald-50 border-2 border-emerald-400 text-emerald-700'
              : 'bg-amber-50 border-2 border-amber-300 text-amber-700'
          }`}
        >
          <div className="text-left">
            <p className="font-bold text-base">
              {isMesaPosta ? '🟢 Mesa Posta' : '🟡 Requer Aviso'}
            </p>
            <p className="text-xs font-normal opacity-75 mt-0.5">
              {isMesaPosta ? 'Portas abertas — pode vir sem avisar' : 'Envie uma solicitação antes de visitar'}
            </p>
          </div>
          <div className={`w-12 h-6 rounded-full transition-colors relative flex-shrink-0 ${isMesaPosta ? 'bg-emerald-400' : 'bg-slate-300'}`}>
            <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${isMesaPosta ? 'translate-x-6' : 'translate-x-0.5'}`} />
          </div>
        </button>

        {/* Como posso ajudar — Meus Talentos */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-indigo-100 mb-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <HandHeart size={18} className="text-indigo-600" />
              <span className="text-sm font-bold text-indigo-700">Como posso ajudar?</span>
            </div>
            <button onClick={() => setEditing(!editing)} className="text-indigo-400 hover:text-indigo-600">
              {editing ? <Check size={16} /> : <Edit3 size={16} />}
            </button>
          </div>
          {editing ? (
            <textarea
              value={helpOffer}
              onChange={e => setHelpOffer(e.target.value)}
              placeholder="Ex: Ajudo com pequenos consertos, dou aulas de violão..."
              className="w-full text-sm text-slate-700 border border-indigo-200 rounded-xl p-3 resize-none h-24 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          ) : (
            <p className="text-sm text-slate-600 leading-relaxed">
              {helpOffer || (
                <span className="text-slate-400 italic">Toque no lápis e conte como você pode servir a comunidade.</span>
              )}
            </p>
          )}
        </div>

        {/* Informações de contato */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 divide-y divide-slate-50 mb-4">
          {[
            { icon: <Mail size={16} />, label: 'E-mail', value: currentUser.email },
            { icon: <Phone size={16} />, label: 'Telefone', value: currentUser.phone },
            { icon: <Briefcase size={16} />, label: 'Profissão', value: currentUser.profession },
            currentUser.homeLocation ? { icon: <MapPin size={16} />, label: 'Endereço', value: currentUser.homeLocation.address } : null,
          ].filter(Boolean).map((item, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3">
              <span className="text-indigo-500">{item!.icon}</span>
              <div>
                <p className="text-xs text-slate-400">{item!.label}</p>
                <p className="text-sm text-slate-700">{item!.value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-white rounded-2xl p-3 shadow-sm border border-slate-100 text-center">
            <p className="text-2xl font-bold text-indigo-600">{currentUser.friends.length}</p>
            <p className="text-xs text-slate-500 mt-0.5">Amigos na comunidade</p>
          </div>
          <div className="bg-white rounded-2xl p-3 shadow-sm border border-slate-100 text-center">
            <p className="text-2xl font-bold text-emerald-600">12</p>
            <p className="text-xs text-slate-500 mt-0.5">Visitas realizadas</p>
          </div>
        </div>

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
