export interface User {
  id: string;
  name: string;
  avatar: string;
  profession: string;
  phone: string;
  email: string;
  cpf?: string;
  birthDate?: string;
  location?: LatLng;
  homeLocation?: LatLng;
  workLocation?: LatLng;
  isOnline: boolean;
  openToVisits: boolean;
  friends: string[];
  churchId?: string;
  bio?: string;
  helpOffer?: string;
}

export interface LatLng {
  lat: number;
  lng: number;
  address?: string;
}

export interface Business {
  id: string;
  name: string;
  category: BusinessCategory;
  location: LatLng;
  phone: string;
  hours: string;
  description: string;
  ownerId: string;
  rating: number;
  reviewCount: number;
  logo?: string;
  loyaltyPoints?: number;
  communityRecommendations: string[];
}

export interface SamaritanAlert {
  id: string;
  userId: string;
  userName: string;
  userAvatar: string;
  type: 'urgency' | 'prayer' | 'practical_help';
  description: string;
  location: LatLng;
  createdAt: Date;
  status: 'active' | 'resolved';
}

export type BusinessCategory =
  | 'restaurante'
  | 'mercado'
  | 'saude'
  | 'educacao'
  | 'servicos'
  | 'religioso'
  | 'outros';

export interface VisitRequest {
  id: string;
  fromUserId: string;
  toUserId: string;
  status: 'pending' | 'accepted' | 'declined';
  message?: string;
  createdAt: Date;
  location?: LatLng;
}

export interface Event {
  id: string;
  title: string;
  description: string;
  type: 'social' | 'religious' | 'volunteer' | 'business';
  location: LatLng;
  date: Date;
  organizer: string;
  organizerId: string;
  attendees: string[];
  churchId?: string;
  imageUrl?: string;
}

export interface Message {
  id: string;
  fromUserId: string;
  toUserId: string;
  content: string;
  createdAt: Date;
  read: boolean;
}

export interface Conversation {
  userId: string;
  lastMessage: Message;
  unreadCount: number;
}

export interface Church {
  id: string;
  name: string;
  denomination: string;
  location: LatLng;
  phone: string;
  schedule: string;
  pastor?: string;
  description: string;
  members: number;
}

export interface PrayerGroup {
  id: string;
  name: string;
  description: string;
  churchId?: string;
  location?: LatLng;
  isOnline: boolean;
  schedule: string;
  members: string[];
  creatorId: string;
  topic: string;
}

export interface Testimonial {
  id: string;
  userId: string;
  title: string;
  content: string;
  createdAt: Date;
  likes: string[];
  comments: TestimonialComment[];
}

export interface TestimonialComment {
  id: string;
  userId: string;
  content: string;
  createdAt: Date;
}

export interface VolunteerOpportunity {
  id: string;
  title: string;
  description: string;
  organizerId: string;
  organizerName: string;
  location: LatLng;
  date: Date;
  spots: number;
  enrolled: string[];
  category: string;
}

export type AppTab = 'map' | 'friends' | 'community' | 'business' | 'events' | 'chat' | 'profile';

export type VisitStatus = 'mesa_posta' | 'requer_aviso';

export type Notification = {
  id: string;
  type: 'visit_request' | 'visit_accepted' | 'visit_declined' | 'message' | 'event' | 'nearby';
  title: string;
  body: string;
  createdAt: Date;
  read: boolean;
  data?: Record<string, string>;
};
