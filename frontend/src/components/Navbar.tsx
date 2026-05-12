import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const location = useLocation();
  const { user, isLoggedIn, logout } = useAuth();
  const isWorkbench = location.pathname.startsWith('/app');

  return (
    <header className="bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 md:px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-xl">{'🔍'}</span>
          <span className="text-base font-bold text-gray-900 dark:text-white">
            降AIGC
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          {isWorkbench && (
            <>
              <Link
                to="/app"
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  location.pathname === '/app'
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                工作台
              </Link>
              <Link
                to="/app/history"
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  location.pathname === '/app/history'
                    ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                历史
              </Link>
            </>
          )}

          {isLoggedIn ? (
            <div className="flex items-center gap-2 ml-2">
              <span className="text-xs text-gray-500 dark:text-gray-400 hidden sm:inline">
                {user?.name}
              </span>
              <button
                onClick={logout}
                className="text-xs px-2 py-1 rounded text-gray-500 hover:text-gray-700
                           dark:hover:text-gray-300 transition-colors"
              >
                退出
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="ml-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900
                         dark:hover:text-white transition-colors"
            >
              登录
            </Link>
          )}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
