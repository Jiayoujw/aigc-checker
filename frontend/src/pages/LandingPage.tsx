import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const features = [
  {
    icon: '🔍',
    title: 'AIGC检测',
    desc: '双模型AI检测引擎，精准判断文本是否由ChatGPT、Claude等AI生成，支持段落级可疑标注。',
    color: 'from-blue-500 to-blue-600',
  },
  {
    icon: '📑',
    title: '查重检测',
    desc: '智能语义查重，识别文本中的抄袭和重复内容，多维度分析原创度。',
    color: 'from-purple-500 to-purple-600',
  },
  {
    icon: '✏️',
    title: '一键降AIGC',
    desc: '将AI生成的文本改写为自然人类写作风格，保留原意的同时降低AI检测率。',
    color: 'from-emerald-500 to-emerald-600',
  },
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.15 },
  },
};

const item = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0 },
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Navbar */}
      <nav className="border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <span className="text-2xl">{'🔍'}</span>
            <span className="text-lg font-bold text-gray-900 dark:text-white">
              降AIGC
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
            >
              登录
            </Link>
            <Link
              to="/app"
              className="text-sm px-4 py-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors"
            >
              开始使用
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 py-20 md:py-32">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
            让AI文本
            <span className="bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
              {' '}更像人写的{' '}
            </span>
          </h1>
          <p className="text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-10">
            AI检测 · 智能改写 · 查重比对 — 一站式文本质量平台，
            帮助你的内容通过AI检测，确保原创性
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              to="/app"
              className="px-8 py-3 rounded-xl bg-blue-500 text-white font-medium
                         hover:bg-blue-600 transition-all shadow-lg shadow-blue-500/25
                         hover:shadow-xl hover:shadow-blue-500/30 active:scale-[0.98]"
            >
              免费开始使用
            </Link>
            <a
              href="#features"
              className="px-8 py-3 rounded-xl border border-gray-300 dark:border-gray-700
                         text-gray-700 dark:text-gray-300 font-medium
                         hover:bg-gray-50 dark:hover:bg-gray-900 transition-all"
            >
              了解更多
            </a>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-20">
        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="grid md:grid-cols-3 gap-8"
        >
          {features.map((f) => (
            <motion.div
              key={f.title}
              variants={item}
              className="group relative bg-white dark:bg-gray-900 border border-gray-200
                         dark:border-gray-800 rounded-2xl p-8 hover:shadow-xl transition-all
                         hover:-translate-y-1"
            >
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color}
                            flex items-center justify-center text-2xl mb-4
                            shadow-lg`}
              >
                {f.icon}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {f.title}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                {f.desc}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-3xl p-12 md:p-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            准备好提升文本质量了？
          </h2>
          <p className="text-blue-100 mb-8 max-w-lg mx-auto">
            无需注册即可使用，支持中英文检测，AI驱动的高精度分析
          </p>
          <Link
            to="/app"
            className="inline-block px-8 py-3 rounded-xl bg-white text-blue-600 font-medium
                       hover:bg-gray-100 transition-all active:scale-[0.98]"
          >
            立即体验
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 py-8 text-center">
        <p className="text-sm text-gray-400">
          &copy; 2026 降AIGC平台 · 保护你的内容原创性
        </p>
      </footer>
    </div>
  );
}
