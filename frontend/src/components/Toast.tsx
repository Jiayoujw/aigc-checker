import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, XCircle, Info } from 'lucide-react';

interface ToastMessage {
  id: number;
  text: string;
  type: 'success' | 'error' | 'info';
}

let addToastFn: ((text: string, type: ToastMessage['type']) => void) | null = null;

export function toast(text: string, type: ToastMessage['type'] = 'info') {
  addToastFn?.(text, type);
}

const icons: Record<ToastMessage['type'], typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
};

const iconColors: Record<ToastMessage['type'], string> = {
  success: 'text-green-500',
  error: 'text-red-500',
  info: 'text-blue-500',
};

const colors: Record<ToastMessage['type'], string> = {
  success: 'border-green-400 bg-green-50 dark:bg-green-900/30',
  error: 'border-red-400 bg-red-50 dark:bg-red-900/30',
  info: 'border-blue-400 bg-blue-50 dark:bg-blue-900/30',
};

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const add = useCallback((text: string, type: ToastMessage['type']) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  useEffect(() => {
    addToastFn = add;
    return () => {
      addToastFn = null;
    };
  }, [add]);

  return (
    <div className="fixed top-20 right-4 z-50 flex flex-col gap-2 max-w-sm">
      <AnimatePresence>
        {toasts.map((t) => {
          const Icon = icons[t.type];
          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 50, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 50, scale: 0.9 }}
              className={`border rounded-lg px-4 py-3 text-sm shadow-lg flex items-center gap-2 ${colors[t.type]}`}
            >
              <Icon className={`w-4 h-4 flex-shrink-0 ${iconColors[t.type]}`} />
              <span className="text-gray-800 dark:text-gray-200">{t.text}</span>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
