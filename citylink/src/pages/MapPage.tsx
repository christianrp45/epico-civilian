import { useEffect, useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useStore } from '../store/useStore';
import type { User, LatLng, SamaritanAlert } from '../types';
import VisitRequestModal from '../components/VisitRequestModal';
import { haversineDistance, formatDistance } from '../utils/distance';
import { Navigation, Users, AlertTriangle, HandHeart, X } from 'lucide-react';

const GOIANIA_CENTER: LatLng = { lat: -16.6864, lng: -49.2643 };
const NEARBY_RADIUS = 2000;
const SAMARITAN_RADIUS = 5000;

const ALERT_TYPE_LABEL: Record<SamaritanAlert['type'], string> = {
  urgency: '🚨 Urgência',
  prayer: '🙏 Pedido de Oração',
  practical_help: '🔧 Ajuda Prática',
};

function createUserIcon(avatar: string, isOnline: boolean, openToVisits: boolean) {
  const borderColor = openToVisits ? '#10b981' : isOnline ? '#6366f1' : '#94a3b8';
  return L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:44px;height:44px">
        <img src="${avatar}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;border:3px solid ${borderColor};position:absolute;top:2px;left:2px" />
        ${isOnline ? `<div style="position:absolute;bottom:2px;right:2px;width:10px;height:10px;border-radius:50%;background:${openToVisits ? '#10b981' : '#6366f1'};border:2px solid white"></div>` : ''}
      </div>
    `,
    iconSize: [44, 44],
    iconAnchor: [22, 22],
  });
}

function createSamaritanIcon() {
  return L.divIcon({
    className: '',
    html: `
      <div style="width:36px;height:36px;background:#f59e0b;border-radius:50%;border:3px solid white;box-shadow:0 0 0 3px rgba(245,158,11,0.4);display:flex;align-items:center;justify-content:center;font-size:16px">
        🆘
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}

function createMeIcon() {
  return L.divIcon({
    className: '',
    html: `
      <div style="width:24px;height:24px;background:#3b82f6;border-radius:50%;border:3px solid white;box-shadow:0 0 0 4px rgba(59,130,246,0.3)"></div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

function MapRelocator({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => { map.setView(center, 14); }, [center, map]);
  return null;
}

export default function MapPage() {
  const { currentUser, users, userLocation, setUserLocation, toggleOpenToVisits, samaritanAlerts } = useStore();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<SamaritanAlert | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([GOIANIA_CENTER.lat, GOIANIA_CENTER.lng]);

  const friendIds = currentUser?.friends ?? [];
  const friends = users.filter(u => friendIds.includes(u.id) && u.id !== currentUser?.id);
  const nearbyFriends = friends.filter(f => {
    if (!userLocation || !f.location) return false;
    return haversineDistance(userLocation, f.location) <= NEARBY_RADIUS;
  });
  const activeAlerts = samaritanAlerts.filter(a => {
    if (a.status !== 'active') return false;
    if (!userLocation) return true;
    return haversineDistance(userLocation, a.location) <= SAMARITAN_RADIUS;
  });

  const simulateLocation = useCallback(() => {
    const loc: LatLng = {
      lat: GOIANIA_CENTER.lat + (Math.random() - 0.5) * 0.02,
      lng: GOIANIA_CENTER.lng + (Math.random() - 0.5) * 0.02,
      address: 'Sua localização atual',
    };
    setUserLocation(loc);
    setMapCenter([loc.lat, loc.lng]);
  }, [setUserLocation]);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          const loc: LatLng = { lat: pos.coords.latitude, lng: pos.coords.longitude, address: 'Você está aqui' };
          setUserLocation(loc);
          setMapCenter([loc.lat, loc.lng]);
        },
        () => simulateLocation()
      );
    } else {
      simulateLocation();
    }
  }, [simulateLocation, setUserLocation]);

  return (
    <div className="flex flex-col h-full relative">
      {/* Map */}
      <div className="flex-1 relative">
        <MapContainer
          center={mapCenter}
          zoom={14}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          <MapRelocator center={mapCenter} />

          {/* My location */}
          {userLocation && (
            <>
              <Marker position={[userLocation.lat, userLocation.lng]} icon={createMeIcon()}>
                <Popup>
                  <strong>Você está aqui</strong>
                  {currentUser && <p className="text-xs mt-1">{currentUser.name}</p>}
                </Popup>
              </Marker>
              <Circle
                center={[userLocation.lat, userLocation.lng]}
                radius={NEARBY_RADIUS}
                pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.05, weight: 1, dashArray: '6' }}
              />
            </>
          )}

          {/* Alertas Samaritanos no mapa */}
          {activeAlerts.map(alert => (
            <Marker
              key={alert.id}
              position={[alert.location.lat, alert.location.lng]}
              icon={createSamaritanIcon()}
              eventHandlers={{ click: () => setSelectedAlert(alert) }}
            />
          ))}

          {/* Friends on map */}
          {friends.map(friend => {
            if (!friend.location) return null;
            return (
              <Marker
                key={friend.id}
                position={[friend.location.lat, friend.location.lng]}
                icon={createUserIcon(friend.avatar, friend.isOnline, friend.openToVisits)}
                eventHandlers={{ click: () => setSelectedUser(friend) }}
              >
                <Popup>
                  <div className="text-center min-w-[140px]">
                    <img src={friend.avatar} alt={friend.name} className="w-12 h-12 rounded-full mx-auto mb-1 object-cover" />
                    <p className="font-semibold text-sm">{friend.name}</p>
                    <p className="text-xs text-gray-500">{friend.profession}</p>
                    {userLocation && friend.location && (
                      <p className="text-xs text-blue-600 mt-1">
                        {formatDistance(haversineDistance(userLocation, friend.location))} de você
                      </p>
                    )}
                    <button
                      onClick={() => setSelectedUser(friend)}
                      className="mt-2 w-full text-xs bg-blue-600 text-white py-1.5 rounded-lg hover:bg-blue-700"
                    >
                      Solicitar Visita
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>

        {/* My location button */}
        <button
          onClick={simulateLocation}
          className="absolute bottom-4 right-4 z-[1000] bg-white rounded-full p-3 shadow-lg border border-slate-200 hover:bg-slate-50"
          title="Minha localização"
        >
          <Navigation size={20} className="text-blue-600" />
        </button>
      </div>

      {/* Bottom sheet: nearby friends */}
      <div className="bg-white border-t border-slate-200 px-4 pt-3 pb-2 flex-shrink-0">
        {/* Toggle Mesa Posta / Requer Aviso */}
        {currentUser && (
          <button
            onClick={toggleOpenToVisits}
            className={`w-full flex items-center justify-between mb-3 rounded-xl px-3 py-2 transition-colors ${
              currentUser.openToVisits ? 'bg-emerald-50' : 'bg-amber-50'
            }`}
          >
            <div className="text-left">
              <p className={`text-sm font-bold ${currentUser.openToVisits ? 'text-emerald-700' : 'text-amber-700'}`}>
                {currentUser.openToVisits ? '🟢 Mesa Posta' : '🟡 Requer Aviso'}
              </p>
              <p className="text-xs text-slate-400">
                {currentUser.openToVisits ? 'Portas abertas para visitas' : 'Solicite antes de visitar'}
              </p>
            </div>
            <div className={`w-10 h-5 rounded-full relative flex-shrink-0 ${currentUser.openToVisits ? 'bg-emerald-400' : 'bg-slate-300'}`}>
              <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${currentUser.openToVisits ? 'translate-x-5' : 'translate-x-0.5'}`} />
            </div>
          </button>
        )}

        {/* Alertas ativos */}
        {activeAlerts.length > 0 && (
          <button
            onClick={() => setSelectedAlert(activeAlerts[0])}
            className="w-full flex items-center gap-2 mb-2 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2"
          >
            <AlertTriangle size={14} className="text-amber-500 flex-shrink-0" />
            <p className="text-xs font-semibold text-amber-700 truncate">
              {activeAlerts.length} alerta{activeAlerts.length > 1 ? 's' : ''} próximo{activeAlerts.length > 1 ? 's' : ''} — toque para ver
            </p>
          </button>
        )}

        {/* Amigos próximos */}
        <div className="flex items-center gap-2 mb-2">
          <Users size={14} className="text-indigo-600" />
          <p className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
            Amigos próximos ({nearbyFriends.length})
          </p>
        </div>

        {nearbyFriends.length === 0 ? (
          <p className="text-xs text-slate-400 pb-1">Nenhum amigo próximo no momento.</p>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-1 no-scrollbar">
            {nearbyFriends.map(friend => (
              <button
                key={friend.id}
                onClick={() => setSelectedUser(friend)}
                className="flex-shrink-0 flex flex-col items-center gap-1"
              >
                <div className="relative">
                  <img src={friend.avatar} alt={friend.name} className="w-12 h-12 rounded-full object-cover border-2 border-blue-300" />
                  {friend.openToVisits && (
                    <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-green-500 rounded-full border-2 border-white" />
                  )}
                </div>
                <span className="text-xs text-slate-600 text-center max-w-[52px] truncate">{friend.name.split(' ')[0]}</span>
                {userLocation && friend.location && (
                  <span className="text-[10px] text-blue-500">
                    {formatDistance(haversineDistance(userLocation, friend.location))}
                  </span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Visit request modal */}
      {selectedUser && (
        <VisitRequestModal user={selectedUser} onClose={() => setSelectedUser(null)} />
      )}

      {/* Modal de Alerta Samaritano — Bottom Sheet */}
      {selectedAlert && (
        <div className="absolute inset-0 z-[2000] flex items-end" onClick={() => setSelectedAlert(null)}>
          <div
            className="w-full bg-white rounded-t-3xl shadow-2xl p-6"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-bold text-amber-600 bg-amber-100 px-3 py-1 rounded-full">
                {ALERT_TYPE_LABEL[selectedAlert.type]}
              </span>
              <button onClick={() => setSelectedAlert(null)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <div className="flex items-center gap-3 mb-3">
              <img src={selectedAlert.userAvatar} alt={selectedAlert.userName} className="w-12 h-12 rounded-full object-cover border-2 border-amber-300" />
              <div>
                <p className="font-bold text-slate-800">{selectedAlert.userName}</p>
                <p className="text-xs text-slate-400">{selectedAlert.location.address}</p>
              </div>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed mb-5">{selectedAlert.description}</p>
            <button
              onClick={() => setSelectedAlert(null)}
              className="w-full py-3 bg-amber-500 text-white font-bold rounded-2xl flex items-center justify-center gap-2 hover:bg-amber-600 transition-colors"
            >
              <HandHeart size={18} /> Posso Ajudar!
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
