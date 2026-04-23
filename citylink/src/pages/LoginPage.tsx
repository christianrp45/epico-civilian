import { useState } from 'react';
import { useStore } from '../store/useStore';
import { MOCK_USERS } from '../utils/mockData';
import { User, Phone, Lock } from 'lucide-react';

export default function LoginPage() {
  const { login } = useStore();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [profession, setProfession] = useState('');
  const [password, setPassword] = useState('');
  const [demo, setDemo] = useState('u1');

  const handleDemoLogin = () => {
    const user = MOCK_USERS.find(u => u.id === demo);
    if (user) login(user);
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    const newUser = {
      id: crypto.randomUUID(),
      name,
      avatar: `https://i.pravatar.cc/150?img=${Math.floor(Math.random() * 70)}`,
      profession,
      phone,
      email,
      isOnline: true,
      openToVisits: false,
      friends: [],
      bio: '',
    };
    login(newUser);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex flex-col items-center justify-center p-6">
      {/* Logo */}
      <div className="text-center mb-8">
        <div className="w-20 h-20 bg-white rounded-3xl shadow-xl flex items-center justify-center mx-auto mb-4">
          <span className="text-blue-600 font-black text-3xl">CL</span>
        </div>
        <h1 className="text-3xl font-black text-white tracking-tight">CityLink</h1>
        <p className="text-blue-200 text-sm mt-1">Conectando pessoas, fortalecendo comunidades</p>
      </div>

      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b border-slate-100">
          <button
            onClick={() => setMode('login')}
            className={`flex-1 py-4 text-sm font-semibold transition-colors ${mode === 'login' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-400'}`}
          >
            Entrar
          </button>
          <button
            onClick={() => setMode('register')}
            className={`flex-1 py-4 text-sm font-semibold transition-colors ${mode === 'register' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-slate-400'}`}
          >
            Cadastrar
          </button>
        </div>

        <div className="p-6">
          {mode === 'login' ? (
            <div>
              <p className="text-sm text-slate-500 mb-4 text-center">
                Acesso rápido com conta demonstração
              </p>
              <div className="space-y-2 mb-4">
                {MOCK_USERS.map(u => (
                  <label
                    key={u.id}
                    className={`flex items-center gap-3 p-3 rounded-xl border-2 cursor-pointer transition-colors ${demo === u.id ? 'border-blue-500 bg-blue-50' : 'border-slate-100 hover:border-slate-200'}`}
                  >
                    <input type="radio" name="demo" value={u.id} checked={demo === u.id} onChange={() => setDemo(u.id)} className="hidden" />
                    <img src={u.avatar} alt={u.name} className="w-10 h-10 rounded-full object-cover" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-slate-800">{u.name}</p>
                      <p className="text-xs text-slate-400">{u.profession}</p>
                    </div>
                    {u.openToVisits && (
                      <span className="text-xs bg-green-100 text-green-600 px-2 py-0.5 rounded-full">Aberto</span>
                    )}
                  </label>
                ))}
              </div>
              <button
                onClick={handleDemoLogin}
                className="w-full py-3.5 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-colors"
              >
                Entrar como Demo
              </button>
            </div>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Nome completo</label>
                <div className="relative">
                  <User size={16} className="absolute left-3 top-3 text-slate-400" />
                  <input
                    required
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Seu nome completo"
                    className="w-full pl-9 pr-3 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">E-mail</label>
                <input
                  required type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="seu@email.com"
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Telefone</label>
                <div className="relative">
                  <Phone size={16} className="absolute left-3 top-3 text-slate-400" />
                  <input
                    value={phone}
                    onChange={e => setPhone(e.target.value)}
                    placeholder="(62) 99999-0000"
                    className="w-full pl-9 pr-3 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Profissão</label>
                <input
                  value={profession}
                  onChange={e => setProfession(e.target.value)}
                  placeholder="Ex: Engenheiro, Professor..."
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Senha</label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3 top-3 text-slate-400" />
                  <input
                    required type="password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-3 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                  />
                </div>
              </div>
              <button
                type="submit"
                className="w-full py-3.5 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 transition-colors mt-2"
              >
                Criar Conta
              </button>
            </form>
          )}
        </div>
      </div>

      <p className="text-blue-200 text-xs mt-6 text-center">
        Ao entrar, você concorda com os Termos de Uso e Política de Privacidade
      </p>
    </div>
  );
}
