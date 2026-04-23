import { useState } from 'react';
import type { User } from '../types';
import { useStore } from '../store/useStore';
import { MapPin, X, Send, CheckCircle, XCircle } from 'lucide-react';

interface Props {
  user: User;
  onClose: () => void;
}

export default function VisitRequestModal({ user, onClose }: Props) {
  const { sendVisitRequest, visitRequests, currentUser } = useStore();
  const [message, setMessage] = useState('');
  const [sent, setSent] = useState(false);

  const existingReq = visitRequests.find(
    r => r.fromUserId === currentUser?.id && r.toUserId === user.id
  );

  const handleSend = () => {
    sendVisitRequest(user.id, message || undefined);
    setSent(true);
  };

  if (sent || existingReq) {
    const req = existingReq || visitRequests.find(r => r.fromUserId === currentUser?.id && r.toUserId === user.id);
    const status = req?.status ?? 'pending';
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-end justify-center p-4">
        <div className="bg-white rounded-2xl w-full max-w-md slide-up">
          <div className="p-6 text-center">
            {status === 'accepted' && (
              <>
                <CheckCircle size={56} className="text-green-500 mx-auto mb-3" />
                <h3 className="text-xl font-bold text-slate-800 mb-1">Visita Confirmada!</h3>
                <p className="text-slate-500">
                  {user.openToVisits
                    ? `${user.name} aceita visitas livremente. Pode ir!`
                    : `${user.name} aceitou sua visita!`}
                </p>
                <div className="mt-4 bg-green-50 rounded-xl p-3 flex items-center gap-2">
                  <MapPin size={16} className="text-green-600" />
                  <span className="text-sm text-green-700">{user.homeLocation?.address ?? 'Localização no mapa'}</span>
                </div>
              </>
            )}
            {status === 'declined' && (
              <>
                <XCircle size={56} className="text-red-400 mx-auto mb-3" />
                <h3 className="text-xl font-bold text-slate-800 mb-1">Visita Recusada</h3>
                <p className="text-slate-500">{user.name} não pode receber visitas agora. Tente mais tarde.</p>
              </>
            )}
            {status === 'pending' && (
              <>
                <div className="w-14 h-14 rounded-full border-4 border-blue-300 border-t-blue-600 animate-spin mx-auto mb-3" />
                <h3 className="text-xl font-bold text-slate-800 mb-1">Aguardando resposta…</h3>
                <p className="text-slate-500">Enviamos a solicitação para {user.name}.</p>
              </>
            )}
            <button
              onClick={onClose}
              className="mt-6 w-full py-3 rounded-xl bg-slate-100 text-slate-700 font-semibold hover:bg-slate-200 transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-end justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md slide-up">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h3 className="font-bold text-slate-800 text-lg">Solicitar Visita</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>

        <div className="p-5">
          <div className="flex items-center gap-3 mb-4">
            <img src={user.avatar} alt={user.name} className="w-14 h-14 rounded-full object-cover" />
            <div>
              <p className="font-semibold text-slate-800">{user.name}</p>
              <p className="text-sm text-slate-500">{user.profession}</p>
              {user.homeLocation && (
                <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                  <MapPin size={11} /> {user.homeLocation.address}
                </p>
              )}
            </div>
          </div>

          {user.openToVisits ? (
            <div className="bg-green-50 border border-green-200 rounded-xl p-3 mb-4 flex items-start gap-2">
              <CheckCircle size={16} className="text-green-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-green-700">
                <strong>{user.name}</strong> está com visitas abertas — sem necessidade de confirmação!
              </p>
            </div>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4">
              <p className="text-sm text-amber-700">
                Você enviará uma solicitação de visita. {user.name} precisará aceitar.
              </p>
            </div>
          )}

          <label className="block text-sm font-medium text-slate-700 mb-1">
            Mensagem (opcional)
          </label>
          <textarea
            value={message}
            onChange={e => setMessage(e.target.value)}
            placeholder={`Olá ${user.name.split(' ')[0]}! Estou passando na sua área…`}
            className="w-full rounded-xl border border-slate-200 p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 h-20"
          />

          <button
            onClick={handleSend}
            className="mt-4 w-full py-3 rounded-xl bg-blue-600 text-white font-semibold flex items-center justify-center gap-2 hover:bg-blue-700 transition-colors"
          >
            <Send size={16} />
            {user.openToVisits ? 'Ir Visitar!' : 'Enviar Solicitação'}
          </button>
        </div>
      </div>
    </div>
  );
}
