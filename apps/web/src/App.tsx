/**
 * @fileoverview Main application component with routing configuration.
 *
 * This is the root component of the React application that sets up
 * client-side routing using React Router with HashRouter for
 * compatibility with static file hosting.
 *
 * @module App
 */

import { HashRouter, Route, Routes } from 'react-router';
import { Toaster } from 'sonner';
import Home from './pages/Home';
import Architecture from './pages/Architecture';
import Frontend from './pages/Frontend';
import Backend from './pages/Backend';
import Contact from './pages/Contact';
import LanguageGovernance from './pages/LanguageGovernance';

/**
 * Root application component with routing and global providers.
 *
 * This component configures:
 * 1. **HashRouter**: Uses hash-based routing (/#/path) for static hosting compatibility
 * 2. **Toaster**: Global toast notification system from Sonner library
 * 3. **Routes**: Maps URL paths to page components
 *
 * Available routes:
 * - `/` - Home page (landing page)
 * - `/architecture` - System architecture documentation
 * - `/frontend` - Frontend technology details
 * - `/backend` - Backend implementation details
 * - `/contact` - Contact form and information
 * - `/language-governance` - Language governance dashboard
 *
 * Toast configuration:
 * - Position: top-center
 * - Rich colors enabled
 * - Dark theme matching site design
 *
 * @returns The rendered App component with routing
 *
 * @example
 * // Entry point (main.tsx)
 * import App from './App';
 *
 * ReactDOM.createRoot(document.getElementById('root')!).render(
 *   <React.StrictMode>
 *     <App />
 *   </React.StrictMode>
 * );
 *
 * @example
 * // Navigating between pages (in components)
 * import { Link } from 'react-router';
 *
 * <Link to="/architecture">View Architecture</Link>
 */
export default function App() {
  return (
    <HashRouter>
      <Toaster position="top-center" richColors theme="dark" />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/architecture" element={<Architecture />} />
        <Route path="/frontend" element={<Frontend />} />
        <Route path="/backend" element={<Backend />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/language-governance" element={<LanguageGovernance />} />
      </Routes>
    </HashRouter>
  );
}
