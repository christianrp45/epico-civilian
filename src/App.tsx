import { useStore } from './store/useStore';
import Layout from './components/Layout';
import IncomingVisitModal from './components/IncomingVisitModal';
import LoginPage from './pages/LoginPage';
import MapPage from './pages/MapPage';
import FriendsPage from './pages/FriendsPage';
import ProfilePage from './pages/ProfilePage';
import BusinessPage from './pages/BusinessPage';
import EventsPage from './pages/EventsPage';
import ChatPage from './pages/ChatPage';
import CommunityPage from './pages/CommunityPage';
import './index.css';

const PAGE_MAP = {
  map: MapPage,
  friends: FriendsPage,
  business: BusinessPage,
  events: EventsPage,
  chat: ChatPage,
  community: CommunityPage,
  profile: ProfilePage,
};

export default function App() {
  const { isLoggedIn, activeTab, pendingVisitRequest } = useStore();

  if (!isLoggedIn) {
    return <LoginPage />;
  }

  const PageComponent = PAGE_MAP[activeTab];

  return (
    <Layout>
      <PageComponent />
      {pendingVisitRequest && <IncomingVisitModal />}
    </Layout>
  );
}
