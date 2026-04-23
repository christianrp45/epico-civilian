import { useStore } from '../store/useStore';
import { MapPin, Check, X } from 'lucide-react';

export default function IncomingVisitModal() {
  const { pendingVisitRequest, users, respondToVisitRequest } = useStore();
  if (!pendingVisitRequest) return null;

  const visitor = users.find(u => u.id === pendingVisitRequest.fromUserId);
  if (!visitor) return null;

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm fade-in shadow-2xl">
        <div className="p-6 text-center">
          <div className="relative inline-block mb-4">
            <img src={visitor.avatar} alt={visitor.name} className="w-20 h-20 rounded-full object-cover mx-auto ring-4 ring-blue-100" />
            <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white pulse-green" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-1">Visita Solicitada!</h3>
          <p className="text-blue-600 font-semibold">{visitor.name}</p>
          <p className="text-slate-500 text-sm mt-1">{visitor.profession}</p>

          {pendingVisitRequest.message && (
            <div className="mt-4 bg-slate-50 rounded-xl p-3 text-sm text-slate-600 text-left">
              "{pendingVisitRequest.message}"
            </div>
          )}

          {pendingVisitRequest.location && (
            <div className="mt-3 flex items-center justify-center gap-1 text-xs text-slate-400">
              <MapPin size={12} />
              <span>Está a menos de 2km de você</span>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => respondToVisitRequest(pendingVisitRequest.id, false)}
              className="flex-1 py-3 rounded-xl bg-slate-100 text-slate-700 font-semibold flex items-center justify-center gap-2 hover:bg-slate-200 transition-colors"
            >
              <X size={16} /> Recusar
            </button>
            <button
              onClick={() => respondToVisitRequest(pendingVisitRequest.id, true)}
              className="flex-1 py-3 rounded-xl bg-green-500 text-white font-semibold flex items-center justify-center gap-2 hover:bg-green-600 transition-colors"
            >
              <Check size={16} /> Aceitar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
