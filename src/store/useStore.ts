import { create } from 'zustand';
import type {
  User, Business, Event, Message, Church, PrayerGroup,
  Testimonial, VolunteerOpportunity, VisitRequest, Notification,
  Conversation, AppTab, LatLng, SamaritanAlert,
} from '../types';
import { MOCK_USERS, MOCK_BUSINESSES, MOCK_EVENTS, MOCK_CHURCHES, MOCK_PRAYER_GROUPS, MOCK_TESTIMONIALS, MOCK_VOLUNTEER, MOCK_MESSAGES, MOCK_SAMARITAN_ALERTS } from '../utils/mockData';

interface Store {
  currentUser: User | null;
  activeTab: AppTab;
  users: User[];
  businesses: Business[];
  events: Event[];
  messages: Message[];
  churches: Church[];
  prayerGroups: PrayerGroup[];
  testimonials: Testimonial[];
  volunteerOpportunities: VolunteerOpportunity[];
  visitRequests: VisitRequest[];
  notifications: Notification[];
  conversations: Conversation[];
  pendingVisitRequest: VisitRequest | null;
  userLocation: LatLng | null;
  isLoggedIn: boolean;
  samaritanAlerts: SamaritanAlert[];

  login: (user: User) => void;
  logout: () => void;
  setActiveTab: (tab: AppTab) => void;
  setUserLocation: (loc: LatLng) => void;
  sendVisitRequest: (toUserId: string, message?: string) => void;
  respondToVisitRequest: (id: string, accepted: boolean) => void;
  clearPendingVisitRequest: () => void;
  toggleOpenToVisits: () => void;
  sendMessage: (toUserId: string, content: string) => void;
  markNotificationsRead: () => void;
  likeTestimonial: (id: string) => void;
  addTestimonial: (title: string, content: string) => void;
  joinEvent: (eventId: string) => void;
  joinPrayerGroup: (groupId: string) => void;
  enrollVolunteer: (opportunityId: string) => void;
  addFriend: (userId: string) => void;
  addSamaritanAlert: (alert: Omit<SamaritanAlert, 'id' | 'createdAt' | 'status'>) => void;
  resolveSamaritanAlert: (id: string) => void;
}

export const useStore = create<Store>((set, get) => ({
  currentUser: null,
  activeTab: 'map',
  users: MOCK_USERS,
  businesses: MOCK_BUSINESSES,
  events: MOCK_EVENTS,
  messages: MOCK_MESSAGES,
  churches: MOCK_CHURCHES,
  prayerGroups: MOCK_PRAYER_GROUPS,
  testimonials: MOCK_TESTIMONIALS,
  volunteerOpportunities: MOCK_VOLUNTEER,
  visitRequests: [],
  notifications: [],
  conversations: [],
  pendingVisitRequest: null,
  userLocation: null,
  isLoggedIn: false,
  samaritanAlerts: MOCK_SAMARITAN_ALERTS,

  login: (user) => {
    const convs: Conversation[] = [];
    const msgs = get().messages.filter(m => m.fromUserId === user.id || m.toUserId === user.id);
    const partnerIds = [...new Set(msgs.map(m => m.fromUserId === user.id ? m.toUserId : m.fromUserId))];
    partnerIds.forEach(pid => {
      const pMsgs = msgs.filter(m => m.fromUserId === pid || m.toUserId === pid).sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
      if (pMsgs.length > 0) {
        convs.push({
          userId: pid,
          lastMessage: pMsgs[0],
          unreadCount: pMsgs.filter(m => m.fromUserId === pid && !m.read).length,
        });
      }
    });
    set({ currentUser: user, isLoggedIn: true, conversations: convs });
  },

  logout: () => set({ currentUser: null, isLoggedIn: false, activeTab: 'map' }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  setUserLocation: (loc) => {
    set({ userLocation: loc });
    const { users, currentUser } = get();
    if (!currentUser) return;
    const updated = users.map(u => u.id === currentUser.id ? { ...u, location: loc } : u);
    set({ users: updated, currentUser: { ...currentUser, location: loc } });
  },

  sendVisitRequest: (toUserId, message) => {
    const { currentUser } = get();
    if (!currentUser) return;
    const toUser = get().users.find(u => u.id === toUserId);
    if (!toUser) return;

    const req: VisitRequest = {
      id: crypto.randomUUID(),
      fromUserId: currentUser.id,
      toUserId,
      status: 'pending',
      message,
      createdAt: new Date(),
      location: get().userLocation ?? undefined,
    };

    if (toUser.openToVisits) {
      const notif: Notification = {
        id: crypto.randomUUID(),
        type: 'visit_accepted',
        title: 'Visita liberada!',
        body: `${toUser.name} aceita visitas sem confirmação. Pode ir!`,
        createdAt: new Date(),
        read: false,
      };
      set(s => ({ visitRequests: [...s.visitRequests, { ...req, status: 'accepted' }], notifications: [...s.notifications, notif] }));
    } else {
      const notif: Notification = {
        id: crypto.randomUUID(),
        type: 'visit_request',
        title: 'Solicitação enviada',
        body: `Aguardando resposta de ${toUser.name}`,
        createdAt: new Date(),
        read: false,
      };

      const incoming: VisitRequest = { ...req };
      set(s => ({
        visitRequests: [...s.visitRequests, req],
        notifications: [...s.notifications, notif],
        pendingVisitRequest: currentUser.id === toUserId ? incoming : s.pendingVisitRequest,
      }));

      setTimeout(() => {
        const accepted = Math.random() > 0.3;
        const responseNotif: Notification = {
          id: crypto.randomUUID(),
          type: accepted ? 'visit_accepted' : 'visit_declined',
          title: accepted ? `${toUser.name} aceitou sua visita!` : `${toUser.name} não pode receber agora`,
          body: accepted ? 'Boa visita! O endereço está marcado no mapa.' : 'Tente novamente mais tarde.',
          createdAt: new Date(),
          read: false,
        };
        set(s => ({
          visitRequests: s.visitRequests.map(r => r.id === req.id ? { ...r, status: accepted ? 'accepted' : 'declined' } : r),
          notifications: [...s.notifications, responseNotif],
        }));
      }, 3000);
    }
  },

  respondToVisitRequest: (id, accepted) => {
    set(s => ({
      visitRequests: s.visitRequests.map(r => r.id === id ? { ...r, status: accepted ? 'accepted' : 'declined' } : r),
      pendingVisitRequest: null,
    }));
  },

  clearPendingVisitRequest: () => set({ pendingVisitRequest: null }),

  toggleOpenToVisits: () => {
    const { currentUser, users } = get();
    if (!currentUser) return;
    const updated = { ...currentUser, openToVisits: !currentUser.openToVisits };
    set({
      currentUser: updated,
      users: users.map(u => u.id === currentUser.id ? updated : u),
    });
  },

  sendMessage: (toUserId, content) => {
    const { currentUser } = get();
    if (!currentUser) return;
    const msg: Message = {
      id: crypto.randomUUID(),
      fromUserId: currentUser.id,
      toUserId,
      content,
      createdAt: new Date(),
      read: false,
    };
    set(s => {
      const existing = s.conversations.find(c => c.userId === toUserId);
      const convs = existing
        ? s.conversations.map(c => c.userId === toUserId ? { ...c, lastMessage: msg } : c)
        : [...s.conversations, { userId: toUserId, lastMessage: msg, unreadCount: 0 }];
      return { messages: [...s.messages, msg], conversations: convs };
    });
  },

  markNotificationsRead: () => {
    set(s => ({ notifications: s.notifications.map(n => ({ ...n, read: true })) }));
  },

  likeTestimonial: (id) => {
    const { currentUser } = get();
    if (!currentUser) return;
    set(s => ({
      testimonials: s.testimonials.map(t => {
        if (t.id !== id) return t;
        const liked = t.likes.includes(currentUser.id);
        return { ...t, likes: liked ? t.likes.filter(l => l !== currentUser.id) : [...t.likes, currentUser.id] };
      }),
    }));
  },

  addTestimonial: (title, content) => {
    const { currentUser } = get();
    if (!currentUser) return;
    const t: Testimonial = {
      id: crypto.randomUUID(),
      userId: currentUser.id,
      title,
      content,
      createdAt: new Date(),
      likes: [],
      comments: [],
    };
    set(s => ({ testimonials: [t, ...s.testimonials] }));
  },

  joinEvent: (eventId) => {
    const { currentUser } = get();
    if (!currentUser) return;
    set(s => ({
      events: s.events.map(e => {
        if (e.id !== eventId) return e;
        const joined = e.attendees.includes(currentUser.id);
        return { ...e, attendees: joined ? e.attendees.filter(a => a !== currentUser.id) : [...e.attendees, currentUser.id] };
      }),
    }));
  },

  joinPrayerGroup: (groupId) => {
    const { currentUser } = get();
    if (!currentUser) return;
    set(s => ({
      prayerGroups: s.prayerGroups.map(g => {
        if (g.id !== groupId) return g;
        const joined = g.members.includes(currentUser.id);
        return { ...g, members: joined ? g.members.filter(m => m !== currentUser.id) : [...g.members, currentUser.id] };
      }),
    }));
  },

  enrollVolunteer: (opportunityId) => {
    const { currentUser } = get();
    if (!currentUser) return;
    set(s => ({
      volunteerOpportunities: s.volunteerOpportunities.map(v => {
        if (v.id !== opportunityId) return v;
        const enrolled = v.enrolled.includes(currentUser.id);
        return { ...v, enrolled: enrolled ? v.enrolled.filter(e => e !== currentUser.id) : [...v.enrolled, currentUser.id] };
      }),
    }));
  },

  addFriend: (userId) => {
    const { currentUser, users } = get();
    if (!currentUser) return;
    const updated = currentUser.friends.includes(userId)
      ? { ...currentUser, friends: currentUser.friends.filter(f => f !== userId) }
      : { ...currentUser, friends: [...currentUser.friends, userId] };
    set({ currentUser: updated, users: users.map(u => u.id === currentUser.id ? updated : u) });
  },

  addSamaritanAlert: (alertData) => {
    const alert: SamaritanAlert = {
      ...alertData,
      id: crypto.randomUUID(),
      createdAt: new Date(),
      status: 'active',
    };
    set(s => ({ samaritanAlerts: [alert, ...s.samaritanAlerts] }));
  },

  resolveSamaritanAlert: (id) => {
    set(s => ({
      samaritanAlerts: s.samaritanAlerts.map(a => a.id === id ? { ...a, status: 'resolved' } : a),
    }));
  },
}));
