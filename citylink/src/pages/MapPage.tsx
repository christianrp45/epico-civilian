import { useEffect, useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useStore } from '../store/useStore';
import type { User, LatLng } from '../types';
import VisitRequestModal from '../components/VisitRequestModal';
import { haversineDistance, formatDistance } from '../utils/distance';
import { Navigation, ToggleLeft, ToggleRight, Users } from 'lucide-react';

const GOIANIA_CENTER: LatLng = { lat: -16.6864, lng: -49.2643 };
const NEARBY_RADIUS = 2000;

function createUserIcon(avatar: string, isOnline: boolean, openToVisits: boolean) {
  return L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:44px;height:44px">
        <img src="${avatar}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;border:3px solid ${openToVisits ? '#22c55e' : isOnline ? '#3b82f6' : '#94a3b8'};position:absolute;top:2px;left:2px" />
        ${isOnline ? `<div style="position:absolute;bottom:2px;right:2px;width:10px;height:10px;border-radius:50%;background:${openToVisits ? '#22c55e' : '#3b82f6'};border:2px solid white"></div>` : ''}
      </div>
    `,
    iconSize: [44, 44],
    iconAnchor: [22, 22],
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
  const { currentUser, users, userLocation, setUserLocation, toggleOpenToVisits } = useStore();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([GOIANIA_CENTER.lat, GOIANIA_CENTER.lng]);

  const friendIds = currentUser?.friends ?? [];
  const friends = users.filter(u => friendIds.includes(u.id) && u.id !== currentUser?.id);
  const nearbyFriends = friends.filter(f => {
    if (!userLocation || !f.location) return false;
    return haversineDistance(userLocation, f.location) <= NEARBY_RADIUS;
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
        {/* Open to visits toggle */}
        {currentUser && (
          <div className="flex items-center justify-between mb-3 bg-slate-50 rounded-xl px-3 py-2">
            <div>
              <p className="text-sm font-semibold text-slate-700">Aberto para visitas</p>
              <p className="text-xs text-slate-400">Amigos podem vir sem avisar</p>
            </div>
            <button onClick={toggleOpenToVisits} className="flex-shrink-0">
              {currentUser.openToVisits
                ? <ToggleRight size={36} className="text-green-500" />
                : <ToggleLeft size={36} className="text-slate-300" />}
            </button>
          </div>
        )}

        {/* Nearby friends */}
        <div className="flex items-center gap-2 mb-2">
          <Users size={14} className="text-blue-600" />
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
    </div>
  );
}
