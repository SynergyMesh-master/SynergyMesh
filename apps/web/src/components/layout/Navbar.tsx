/**
 * @fileoverview Main navigation bar component with responsive mobile menu.
 *
 * This component provides the primary navigation for the application,
 * featuring a scroll-aware design and mobile-responsive hamburger menu.
 *
 * @module components/layout/Navbar
 */

import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router';
import { Menu, X, Terminal, Code2, Server, Layers, Mail, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Responsive navigation bar component with scroll effects and mobile menu.
 *
 * Features:
 * - **Scroll-aware styling**: Background becomes semi-transparent with blur on scroll
 * - **Active route highlighting**: Current page link is highlighted in blue
 * - **Mobile hamburger menu**: Collapsible menu for smaller screens
 * - **Auto-close on navigation**: Mobile menu closes when route changes
 *
 * Navigation items include: Home, Architecture, Frontend, Backend,
 * Language Governance, and Contact pages.
 *
 * @returns The rendered Navbar component
 *
 * @example
 * // Typical usage in page components
 * function MyPage() {
 *   return (
 *     <div>
 *       <Navbar />
 *       <main>Page content...</main>
 *       <Footer />
 *     </div>
 *   );
 * }
 */
export default function Navbar() {
  /** Controls mobile menu open/closed state */
  const [isOpen, setIsOpen] = useState(false);
  /** Tracks whether page has scrolled beyond 20px threshold */
  const [scrolled, setScrolled] = useState(false);
  /** Current route location for active link highlighting */
  const location = useLocation();

  /** Effect: Attaches scroll listener to update scrolled state */
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  /** Effect: Closes mobile menu when route changes */
  useEffect(() => {
    setIsOpen(false);
  }, [location]);

  /** Navigation items configuration with name, path, and icon */
  const navItems = [
    { name: '首頁', path: '/', icon: Terminal },
    { name: '系統架構', path: '/architecture', icon: Layers },
    { name: '前端技術', path: '/frontend', icon: Code2 },
    { name: '後端實現', path: '/backend', icon: Server },
    { name: '語言治理', path: '/language-governance', icon: Activity },
    { name: '聯絡我們', path: '/contact', icon: Mail },
  ];

  return (
    <nav
      className={cn(
        'fixed top-0 w-full z-50 transition-all duration-300 border-b',
        scrolled
          ? 'bg-slate-950/90 backdrop-blur-md border-slate-800 py-3'
          : 'bg-transparent border-transparent py-5'
      )}
    >
      <div className="container mx-auto px-6 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="bg-blue-600 p-2 rounded-lg group-hover:bg-blue-500 transition-colors">
            <Terminal className="text-white h-6 w-6" />
          </div>
          <span className="text-xl font-bold text-slate-100 tracking-tight">
            Auto-Fix <span className="text-blue-400">Bot</span>
          </span>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex gap-8">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'text-sm font-medium transition-colors flex items-center gap-2 hover:text-blue-400',
                location.pathname === item.path ? 'text-blue-400' : 'text-slate-300'
              )}
            >
              {item.name}
            </Link>
          ))}
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden text-slate-300 hover:text-white"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu Dropdown */}
      {isOpen && (
        <div className="md:hidden absolute top-full left-0 w-full bg-slate-900 border-b border-slate-800 shadow-xl">
          <div className="flex flex-col p-6 gap-4">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 text-lg font-medium p-2 rounded-md hover:bg-slate-800',
                  location.pathname === item.path ? 'text-blue-400' : 'text-slate-300'
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
