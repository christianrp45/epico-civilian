import { useState } from 'react';
import { useStore } from '../store/useStore';
import { Church, Users, Heart, HandHeart, BookOpen, ChevronRight, MapPin, Phone, CheckCircle, Plus, ThumbsUp, MessageCircle } from 'lucide-react';

type CommunityTab = 'churches' | 'prayer' | 'testimonials' | 'volunteer';

export default function CommunityPage() {
  const [tab, setTab] = useState<CommunityTab>('churches');

  const tabs: { id: CommunityTab; label: string; icon: React.ReactNode }[] = [
    { id: 'churches', label: 'Igrejas', icon: <Church size={14} /> },
    { id: 'prayer', label: 'Oração', icon: <BookOpen size={14} /> },
    { id: 'testimonials', label: 'Testemunhos', icon: <Heart size={14} /> },
    { id: 'volunteer', label: 'Voluntário', icon: <HandHeart size={14} /> },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Tabs */}
      <div className="bg-white border-b border-slate-100 px-4 py-3">
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                tab === t.id ? 'bg-purple-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === 'churches' && <ChurchesTab />}
        {tab === 'prayer' && <PrayerGroupsTab />}
        {tab === 'testimonials' && <TestimonialsTab />}
        {tab === 'volunteer' && <VolunteerTab />}
      </div>
    </div>
  );
}

function ChurchesTab() {
  const { churches } = useStore();
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="p-4 space-y-3">
      <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide">
        {churches.length} igrejas cadastradas
      </p>
      {churches.map(church => (
        <div key={church.id} className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <button
            className="w-full p-4 text-left"
            onClick={() => setExpanded(expanded === church.id ? null : church.id)}
          >
            <div className="flex items-start gap-3">
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <Church size={22} className="text-purple-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-bold text-slate-800">{church.name}</p>
                <p className="text-xs text-purple-600 font-semibold">{church.denomination}</p>
                <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                  <MapPin size={10} /> {church.location.address}
                </p>
              </div>
              <ChevronRight size={16} className={`text-slate-300 flex-shrink-0 transition-transform ${expanded === church.id ? 'rotate-90' : ''}`} />
            </div>

            {expanded === church.id && (
              <div className="mt-4 pt-4 border-t border-slate-100 space-y-2 fade-in">
                <p className="text-sm text-slate-600">{church.description}</p>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Phone size={12} className="text-purple-500" /> {church.phone}
                </div>
                <div className="bg-purple-50 rounded-xl p-3">
                  <p className="text-xs font-semibold text-purple-700 mb-1">Horários de Culto</p>
                  <p className="text-xs text-purple-600">{church.schedule}</p>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  {church.pastor && <span>Pastor(a): <strong>{church.pastor}</strong></span>}
                  <span><Users size={12} className="inline mr-1" />{church.members} membros</span>
                </div>
                <button className="w-full py-2 bg-purple-600 text-white rounded-xl text-xs font-semibold hover:bg-purple-700 transition-colors">
                  Ver no Mapa
                </button>
              </div>
            )}
          </button>
        </div>
      ))}
    </div>
  );
}

function PrayerGroupsTab() {
  const { prayerGroups, currentUser, joinPrayerGroup } = useStore();

  return (
    <div className="p-4 space-y-3">
      <button className="w-full py-3 border-2 border-dashed border-purple-300 rounded-2xl text-purple-600 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-purple-50 transition-colors">
        <Plus size={16} /> Criar Grupo de Oração
      </button>

      {prayerGroups.map(group => {
        const joined = currentUser ? group.members.includes(currentUser.id) : false;
        return (
          <div key={group.id} className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
                <BookOpen size={18} className="text-purple-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-bold text-slate-800 text-sm">{group.name}</p>
                  {group.isOnline && (
                    <span className="flex-shrink-0 text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">Online</span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{group.description}</p>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Users size={10} /> {group.members.length} membros
                  </span>
                  <span className="text-xs text-purple-600">{group.schedule}</span>
                </div>
                <div className="mt-1">
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{group.topic}</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => currentUser && joinPrayerGroup(group.id)}
              className={`mt-3 w-full py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-colors ${
                joined
                  ? 'bg-green-50 text-green-600 border border-green-200'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              {joined ? <><CheckCircle size={12} /> Participando</> : 'Participar do Grupo'}
            </button>
          </div>
        );
      })}
    </div>
  );
}

function TestimonialsTab() {
  const { testimonials, currentUser, likeTestimonial, addTestimonial, users } = useStore();
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  const handleSubmit = () => {
    if (!title.trim() || !content.trim()) return;
    addTestimonial(title.trim(), content.trim());
    setTitle('');
    setContent('');
    setShowForm(false);
  };

  return (
    <div className="p-4 space-y-3">
      {/* Add testimonial */}
      {showForm ? (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4 fade-in">
          <p className="font-bold text-slate-800 mb-3">Compartilhar Testemunho</p>
          <input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Título do testemunho"
            className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-purple-400"
          />
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder="Compartilhe o que Deus fez em sua vida..."
            className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm resize-none h-28 focus:outline-none focus:ring-2 focus:ring-purple-400"
          />
          <div className="flex gap-2 mt-3">
            <button onClick={() => setShowForm(false)} className="flex-1 py-2 bg-slate-100 text-slate-600 rounded-xl text-sm font-semibold">
              Cancelar
            </button>
            <button onClick={handleSubmit} className="flex-1 py-2 bg-purple-600 text-white rounded-xl text-sm font-semibold hover:bg-purple-700 transition-colors">
              Publicar
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowForm(true)}
          className="w-full py-3 border-2 border-dashed border-purple-300 rounded-2xl text-purple-600 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-purple-50 transition-colors"
        >
          <Plus size={16} /> Compartilhar Testemunho
        </button>
      )}

      {testimonials.map(t => {
        const author = users.find(u => u.id === t.userId);
        const liked = currentUser ? t.likes.includes(currentUser.id) : false;
        return (
          <div key={t.id} className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4">
            <div className="flex items-center gap-3 mb-3">
              <img src={author?.avatar} alt={author?.name} className="w-10 h-10 rounded-full object-cover" />
              <div>
                <p className="font-semibold text-slate-800 text-sm">{author?.name}</p>
                <p className="text-xs text-slate-400">
                  {t.createdAt.toLocaleDateString('pt-BR')}
                </p>
              </div>
            </div>
            <h4 className="font-bold text-slate-800 mb-1">{t.title}</h4>
            <p className="text-sm text-slate-600 leading-relaxed">{t.content}</p>
            <div className="flex items-center gap-4 mt-4 pt-3 border-t border-slate-50">
              <button
                onClick={() => currentUser && likeTestimonial(t.id)}
                className={`flex items-center gap-1.5 text-xs font-semibold transition-colors ${liked ? 'text-purple-600' : 'text-slate-400 hover:text-purple-500'}`}
              >
                <ThumbsUp size={14} className={liked ? 'fill-purple-600' : ''} />
                {t.likes.length} Amém
              </button>
              <button className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-600 font-semibold">
                <MessageCircle size={14} /> {t.comments.length} Comentários
              </button>
            </div>
            {t.comments.length > 0 && (
              <div className="mt-3 space-y-2">
                {t.comments.map(c => {
                  const commenter = users.find(u => u.id === c.userId);
                  return (
                    <div key={c.id} className="bg-slate-50 rounded-xl p-3 flex gap-2">
                      <img src={commenter?.avatar} alt={commenter?.name} className="w-7 h-7 rounded-full object-cover flex-shrink-0" />
                      <div>
                        <p className="text-xs font-semibold text-slate-700">{commenter?.name}</p>
                        <p className="text-xs text-slate-500">{c.content}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function VolunteerTab() {
  const { volunteerOpportunities, currentUser, enrollVolunteer } = useStore();

  return (
    <div className="p-4 space-y-3">
      <p className="text-xs text-slate-400 font-semibold uppercase tracking-wide">
        Oportunidades de Voluntariado
      </p>
      {volunteerOpportunities.map(v => {
        const enrolled = currentUser ? v.enrolled.includes(currentUser.id) : false;
        const spotsLeft = v.spots - v.enrolled.length;
        return (
          <div key={v.id} className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h4 className="font-bold text-slate-800">{v.title}</h4>
              <span className="flex-shrink-0 text-xs bg-green-100 text-green-600 px-2 py-0.5 rounded-full">{v.category}</span>
            </div>
            <p className="text-sm text-slate-500 mb-3">{v.description}</p>
            <div className="space-y-1.5 mb-3">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <MapPin size={12} className="text-green-500" /> {v.location.address}
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Users size={12} className="text-green-500" />
                {v.enrolled.length}/{v.spots} inscritos •
                <span className={spotsLeft <= 5 ? 'text-red-500 font-semibold' : 'text-green-600'}>
                  {spotsLeft} vagas restantes
                </span>
              </div>
              <div className="text-xs text-slate-400">
                por <strong>{v.organizerName}</strong> •{' '}
                {v.date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
              </div>
            </div>
            <button
              onClick={() => currentUser && enrollVolunteer(v.id)}
              disabled={!enrolled && spotsLeft === 0}
              className={`w-full py-2.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors ${
                enrolled
                  ? 'bg-green-50 text-green-600 border border-green-200'
                  : spotsLeft === 0
                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                    : 'bg-green-500 text-white hover:bg-green-600'
              }`}
            >
              {enrolled ? <><CheckCircle size={14} /> Inscrito</> : spotsLeft === 0 ? 'Sem vagas' : 'Quero Ser Voluntário'}
            </button>
          </div>
        );
      })}
    </div>
  );
}
