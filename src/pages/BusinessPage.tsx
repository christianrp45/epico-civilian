import { useState } from 'react';
import { useStore } from '../store/useStore';
import type { BusinessCategory } from '../types';
import { Search, Star, MapPin, Phone, Clock, Tag, ChevronRight } from 'lucide-react';

const CATEGORIES: { id: BusinessCategory | 'all'; label: string; emoji: string }[] = [
  { id: 'all', label: 'Todos', emoji: '🏪' },
  { id: 'restaurante', label: 'Alimentação', emoji: '🍽️' },
  { id: 'saude', label: 'Saúde', emoji: '🏥' },
  { id: 'mercado', label: 'Mercado', emoji: '🛒' },
  { id: 'educacao', label: 'Educação', emoji: '📚' },
  { id: 'servicos', label: 'Serviços', emoji: '🔧' },
  { id: 'religioso', label: 'Religioso', emoji: '✝️' },
];

export default function BusinessPage() {
  const { businesses } = useStore();
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<BusinessCategory | 'all'>('all');
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = businesses.filter(b => {
    const matchSearch = b.name.toLowerCase().includes(search.toLowerCase()) ||
      b.description.toLowerCase().includes(search.toLowerCase());
    const matchCat = category === 'all' || b.category === category;
    return matchSearch && matchCat;
  });

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Header */}
      <div className="bg-white px-4 py-3 border-b border-slate-100">
        <div className="relative mb-3">
          <Search size={16} className="absolute left-3 top-2.5 text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar empresas..."
            className="w-full pl-9 pr-4 py-2 bg-slate-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
        {/* Category chips */}
        <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar">
          {CATEGORIES.map(c => (
            <button
              key={c.id}
              onClick={() => setCategory(c.id)}
              className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors ${
                category === c.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {c.emoji} {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <p className="text-4xl mb-2">🏪</p>
            <p className="text-sm">Nenhuma empresa encontrada</p>
          </div>
        )}
        {filtered.map(business => (
          <div key={business.id} className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div
              className="p-4 cursor-pointer"
              onClick={() => setExpanded(expanded === business.id ? null : business.id)}
            >
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-xl">
                    {CATEGORIES.find(c => c.id === business.category)?.emoji ?? '🏪'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-semibold text-slate-800">{business.name}</p>
                    <ChevronRight size={16} className={`text-slate-300 flex-shrink-0 transition-transform ${expanded === business.id ? 'rotate-90' : ''}`} />
                  </div>
                  <div className="flex items-center gap-1 mt-0.5">
                    <Star size={12} className="text-amber-400 fill-amber-400" />
                    <span className="text-xs font-semibold text-slate-700">{business.rating}</span>
                    <span className="text-xs text-slate-400">({business.reviewCount} avaliações)</span>
                  </div>
                  <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                    <MapPin size={10} /> {business.location.address}
                  </p>
                </div>
              </div>

              {expanded === business.id && (
                <div className="mt-4 space-y-2 pt-4 border-t border-slate-100 fade-in">
                  <p className="text-sm text-slate-600">{business.description}</p>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Phone size={12} className="text-blue-500" /> {business.phone}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock size={12} className="text-blue-500" /> {business.hours}
                  </div>
                  {business.loyaltyPoints && (
                    <div className="flex items-center gap-2 text-xs bg-amber-50 text-amber-700 px-3 py-2 rounded-xl">
                      <Tag size={12} /> Programa de fidelidade: ganhe {business.loyaltyPoints} pontos por visita
                    </div>
                  )}
                  <div className="flex gap-2 mt-3">
                    <button className="flex-1 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition-colors">
                      Ver no Mapa
                    </button>
                    <button className="flex-1 py-2 bg-slate-100 text-slate-700 text-xs font-semibold rounded-xl hover:bg-slate-200 transition-colors">
                      Ligar
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
