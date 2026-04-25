# CityLink — Documentação do Projeto

## Visão Geral

CityLink é um aplicativo de proximidade social voltado para comunidades, igrejas, amigos e familiares. A ideia central é resgatar as visitas espontâneas do passado: quando você está passando perto da casa de um amigo, pode solicitar uma visita. Se ele estiver com o modo "Aberto para visitas" ativado, você vai direto sem precisar de confirmação.

**Deploy:** Vercel  
**Repositório:** github.com/christianrp45/citylink  
**Stack:** React 19 + TypeScript + Vite + Tailwind CSS v4 + Zustand + Leaflet

---

## Stack Tecnológica

| Tecnologia | Versão | Finalidade |
|---|---|---|
| React | 19.2 | Interface do usuário |
| TypeScript | 6.0 | Tipagem estática |
| Vite | 8.0 | Build tool e dev server |
| Tailwind CSS | 4.2 | Estilização |
| Zustand | 5.0 | Gerenciamento de estado global |
| Leaflet + react-leaflet | 1.9 / 5.0 | Mapas interativos (OpenStreetMap) |
| Lucide React | 1.8 | Ícones |

---

## Estrutura de Arquivos

```
citylink/
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── src/
│   ├── components/
│   │   ├── IncomingVisitModal.tsx    # Modal de visita recebida
│   │   ├── Layout.tsx                # Header + navegação inferior
│   │   ├── NotificationPanel.tsx     # Painel de notificações
│   │   └── VisitRequestModal.tsx     # Modal de solicitar visita
│   ├── pages/
│   │   ├── BusinessPage.tsx          # Catálogo de empresas
│   │   ├── ChatPage.tsx              # Mensagens privadas
│   │   ├── CommunityPage.tsx         # Igreja, oração, testemunhos, voluntário
│   │   ├── EventsPage.tsx            # Eventos da comunidade
│   │   ├── FriendsPage.tsx           # Amigos e descobrir pessoas
│   │   ├── LoginPage.tsx             # Login e cadastro
│   │   ├── MapPage.tsx               # Mapa principal com localização
│   │   └── ProfilePage.tsx           # Perfil do usuário
│   ├── store/
│   │   └── useStore.ts               # Store Zustand (estado global)
│   ├── types/
│   │   └── index.ts                  # Interfaces TypeScript
│   ├── utils/
│   │   ├── distance.ts               # Fórmula Haversine para distância
│   │   └── mockData.ts               # Dados de demonstração
│   ├── App.tsx                       # Componente raiz
│   ├── index.css                     # Tailwind + Leaflet CSS
│   └── main.tsx                      # Entry point
├── vercel.json                       # Configuração de deploy
├── vite.config.ts                    # Configuração Vite + Tailwind
├── tsconfig.json                     # Configuração TypeScript
└── package.json                      # Dependências
```

---

## Funcionalidades

### 1. Autenticação
- Seleção de conta demo (5 usuários pré-cadastrados)
- Formulário de cadastro com: nome, e-mail, telefone, profissão, senha
- Logout com limpeza de estado

### 2. Mapa (MapPage)
- Mapa interativo com OpenStreetMap via Leaflet
- Marcadores personalizados com avatar do usuário
  - Borda **verde**: aberto para visitas
  - Borda **azul**: online
  - Borda **cinza**: offline
- Círculo de proximidade de 2km
- Geolocalização real via `navigator.geolocation` com fallback simulado
- Botão "minha localização" para recentrar o mapa
- Toggle "Aberto para visitas" no rodapé
- Lista de amigos próximos (dentro do raio de 2km)

### 3. Sistema de Visitas
- **Fluxo normal:** solicitação enviada → amigo recebe notificação → aceita ou recusa (simulado em 3 segundos)
- **Fluxo aberto:** se o amigo está com `openToVisits = true`, a visita é aprovada instantaneamente sem confirmação
- Modal de solicitação com mensagem opcional
- Modal de visita recebida com botões Aceitar / Recusar
- Notificações de resultado no sino do header

### 4. Amigos (FriendsPage)
- Aba "Meus Amigos": lista de amigos com botões Visitar, Chat, Remover
- Aba "Descobrir": lista de outros usuários com botão Adicionar Amigo
- Busca por nome ou profissão
- Badge "Aberto" verde para usuários disponíveis para visita

### 5. Empresas (BusinessPage)
- Catálogo com filtros por categoria:
  - Alimentação, Saúde, Mercado, Educação, Serviços, Religioso
- Cards expansíveis com: avaliação, telefone, horário, descrição
- Sistema de pontos de fidelidade

### 6. Eventos (EventsPage)
- Filtros por tipo: Social, Religioso, Voluntariado, Negócios
- Cards com data, local, organizador e participantes
- Avatares dos participantes (até 5 + contador)
- Botão participar/cancelar participação (toggle)

### 7. Chat (ChatPage)
- Lista de conversas com última mensagem
- Thread de mensagens com bolhas diferenciadas (enviado/recebido)
- Envio com tecla Enter
- Histórico de mensagens simulado

### 8. Comunidade (CommunityPage)
Quatro sub-abas:

- **Igrejas:** diretório com denominação, pastor, horários, membros
- **Oração:** grupos de oração online/presencial com botão participar/sair
- **Testemunhos:** publicação de testemunhos com curtida (Amém) e comentários
- **Voluntário:** oportunidades com vagas disponíveis e botão se inscrever

### 9. Perfil (ProfilePage)
- Banner com avatar e nome
- Edição de bio
- Toggle "Aberto para visitas"
- Informações: e-mail, telefone, profissão, endereço, igreja
- Stats: amigos, visitas, pontos
- Botão de logout

### 10. Notificações
- Sino no header com badge de não lidas
- Painel dropdown com ícones por tipo de notificação
- Marcar todas como lidas

---

## Tipos de Dados (TypeScript)

```typescript
User {
  id, name, avatar, profession, phone, email
  cpf?, birthDate?
  location?, homeLocation?, workLocation?  // LatLng
  isOnline, openToVisits
  friends: string[]  // IDs dos amigos
  churchId?, bio?
}

LatLng {
  lat, lng, address?
}

Business {
  id, name, category, location, phone
  hours, description, ownerId
  rating, reviewCount
  logo?, loyaltyPoints?
}

VisitRequest {
  id, fromUserId, toUserId
  status: 'pending' | 'accepted' | 'declined'
  message?, createdAt, location?
}

Event {
  id, title, description
  type: 'social' | 'religious' | 'volunteer' | 'business'
  location, date, organizer, organizerId
  attendees: string[]
  churchId?, imageUrl?
}

Message {
  id, fromUserId, toUserId
  content, createdAt, read
}

Church {
  id, name, denomination, location
  phone, schedule, pastor?, description, members
}

PrayerGroup {
  id, name, description, churchId?
  location?, isOnline, schedule
  members: string[], creatorId, topic
}

Testimonial {
  id, userId, title, content
  createdAt, likes: string[]
  comments: TestimonialComment[]
}

VolunteerOpportunity {
  id, title, description
  organizerId, organizerName, location
  date, spots, enrolled: string[], category
}

Notification {
  id, type, title, body, createdAt, read, data?
}
```

---

## Gerenciamento de Estado (Zustand)

O arquivo `src/store/useStore.ts` centraliza todo o estado do app.

### Estado principal
| Campo | Tipo | Descrição |
|---|---|---|
| `currentUser` | User ou null | Usuário logado |
| `activeTab` | AppTab | Aba ativa na navegação |
| `userLocation` | LatLng ou null | Localização atual do usuário |
| `users` | User[] | Todos os usuários |
| `businesses` | Business[] | Catálogo de empresas |
| `events` | Event[] | Lista de eventos |
| `messages` | Message[] | Todas as mensagens |
| `churches` | Church[] | Diretório de igrejas |
| `prayerGroups` | PrayerGroup[] | Grupos de oração |
| `testimonials` | Testimonial[] | Testemunhos |
| `volunteerOpportunities` | VolunteerOpportunity[] | Oportunidades de voluntariado |
| `visitRequests` | VisitRequest[] | Histórico de visitas |
| `notifications` | Notification[] | Notificações do usuário |
| `pendingVisitRequest` | VisitRequest ou null | Visita recebida aguardando resposta |

### Ações principais
| Ação | Descrição |
|---|---|
| `login(user)` | Faz login e carrega conversas |
| `logout()` | Limpa estado e volta para tela de login |
| `sendVisitRequest(toUserId, message?)` | Envia solicitação de visita (respeita openToVisits) |
| `respondToVisitRequest(id, accepted)` | Aceita ou recusa visita recebida |
| `toggleOpenToVisits()` | Alterna disponibilidade para visitas |
| `sendMessage(toUserId, content)` | Envia mensagem no chat |
| `addFriend(userId)` | Adiciona ou remove amigo (toggle) |
| `joinEvent(eventId)` | Participa ou sai de evento (toggle) |
| `joinPrayerGroup(groupId)` | Entra ou sai de grupo de oração (toggle) |
| `enrollVolunteer(opportunityId)` | Inscreve ou cancela no voluntariado (toggle) |
| `likeTestimonial(id)` | Curte ou remove curtida de testemunho (toggle) |
| `addTestimonial(title, content)` | Publica novo testemunho |
| `markNotificationsRead()` | Marca todas notificações como lidas |

---

## Algoritmo de Proximidade

O arquivo `src/utils/distance.ts` implementa a fórmula de Haversine para calcular distância entre coordenadas geográficas.

```typescript
haversineDistance(a: LatLng, b: LatLng): number  // retorna metros
formatDistance(meters: number): string            // "350m" ou "1.2km"
isNearby(a, b, radiusMeters = 2000): boolean      // dentro do raio?
```

Raio padrão de proximidade: **2.000 metros (2km)**

---

## Dados de Demonstração

O arquivo `src/utils/mockData.ts` contém dados simulados para demonstração:

- **5 usuários:** João Silva, Maria Oliveira, Pedro Santos, Ana Costa, Carlos Ferreira — todos em bairros de Goiânia/GO
- **4 empresas:** restaurante, farmácia, mercado, escola
- **4 eventos:** confraternização, culto, mutirão, reunião de negócios
- **3 igrejas:** diferentes denominações em Goiânia
- **3 grupos de oração:** online e presencial
- **3 testemunhos:** com curtidas e comentários iniciais
- **3 oportunidades de voluntariado:** com vagas e datas

---

## Configuração de Deploy (Vercel)

**`vercel.json`**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "installCommand": "npm install",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

O rewrite `/(.*) → /index.html` é obrigatório para que o roteamento client-side do React funcione corretamente no Vercel.

---

## Como Rodar Localmente

```bash
# 1. Clone o repositório
git clone https://github.com/christianrp45/citylink.git
cd citylink

# 2. Instale as dependências
npm install

# 3. Inicie o servidor de desenvolvimento
npm run dev

# 4. Acesse no navegador
# http://localhost:5173
```

---

## Próximos Passos Sugeridos

- Integração com backend real (Node.js / Supabase / Firebase)
- Autenticação real com JWT ou OAuth
- Notificações push via Web Push API
- Geolocalização em tempo real com WebSockets
- Upload de fotos de perfil e avatares personalizados
- Sistema de avaliações para empresas
- Pagamentos para programa de fidelidade
- App mobile com React Native (reaproveitando a lógica)
