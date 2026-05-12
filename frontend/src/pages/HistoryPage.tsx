import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import Navbar from '../components/Navbar';

export default function HistoryPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            历史记录
          </h2>
        </div>

        <div className="text-center py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <p className="text-4xl mb-4">{'📋'}</p>
            <p className="text-gray-500 dark:text-gray-400 mb-2">
              登录后即可查看检测历史记录
            </p>
            <Link
              to="/login"
              className="text-sm text-blue-500 hover:text-blue-600"
            >
              前往登录
            </Link>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
