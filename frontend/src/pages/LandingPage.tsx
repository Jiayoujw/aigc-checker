import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'framer-motion';
import {
  ScanEye, FileSearch, PenLine, Zap, Shield, Globe,
  ArrowRight, Sparkles, ChevronRight,
} from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle';

const features = [
  {
    icon: ScanEye,
    title: 'AIGC 检测',
    desc: '双模型AI检测引擎，段落级深度分析。精准判断文本是否由ChatGPT、Claude等AI生成，支持学术论文/简历/自媒体等多场景模式。',
    color: 'from-blue-500 to-cyan-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/30',
    iconColor: 'text-blue-600 dark:text-blue-400',
  },
  {
    icon: FileSearch,
    title: '查重检测',
    desc: '智能语义查重结合n-gram相似度分析，识别文本中的抄袭和重复内容，提供详细的相似来源标注。',
    color: 'from-purple-500 to-violet-400',
    bgColor: 'bg-purple-50 dark:bg-purple-950/30',
    iconColor: 'text-purple-600 dark:text-purple-400',
  },
  {
    icon: PenLine,
    title: '一键降 AIGC',
    desc: '三档强度可选（轻度/中度/深度），保留专业术语的同时将AI文本改写为自然人类写作风格，改写后自动复检。',
    color: 'from-emerald-500 to-teal-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
  },
];

const highlights = [
  { icon: Zap, label: '极速解析', desc: 'PyMuPDF引擎，10-20x加速' },
  { icon: Shield, label: '多维检测', desc: 'LLM + 统计 + 困惑度' },
  { icon: Globe, label: '无大小限制', desc: '支持任意大小文件上传' },
  { icon: Sparkles, label: '专业报告', desc: '对标知网/维普报告格式' },
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.12 },
  },
};

const itemAnim = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

export default function LandingPage() {
  const { scrollY } = useScroll();
  const heroOpacity = useTransform(scrollY, [0, 400], [1, 0.3]);
  const heroY = useTransform(scrollY, [0, 400], [0, -60]);

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-white">
      {/* ─── Navbar ─── */}
      <nav className="sticky top-0 z-20 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-gray-200/50 dark:border-gray-800/50">
        <div className="max-w-6xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
              <ScanEye className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              降<span className="text-blue-500">AIGC</span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <a href="#features" className="hidden sm:block text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors">
              功能
            </a>
            <Link to="/login" className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
              登录
            </Link>
            <Link
              to="/app"
              className="flex items-center gap-1.5 text-sm px-4 py-2 rounded-xl bg-blue-500 text-white hover:bg-blue-600 transition-all shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 active:scale-[0.97]"
            >
              开始使用
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <ThemeToggle />
          </div>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <section className="relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-400/10 rounded-full blur-3xl" />
          <div className="absolute top-40 right-10 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl" />
          <div className="absolute bottom-10 left-1/3 w-80 h-80 bg-emerald-400/10 rounded-full blur-3xl" />
        </div>

        <motion.div
          style={{ opacity: heroOpacity, y: heroY }}
          className="relative max-w-6xl mx-auto px-6 pt-24 pb-20 md:pt-36 md:pb-28 text-center"
        >
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: 'easeOut' }}
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 dark:bg-blue-950/40 border border-blue-200/50 dark:border-blue-800/50 text-xs text-blue-600 dark:text-blue-400 mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
              专业级 AIGC 检测平台
            </div>

            <h1 className="text-5xl md:text-7xl font-extrabold leading-tight tracking-tight mb-6">
              让 AI 文本
              <br />
              <span className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
                更像人写的
              </span>
            </h1>

            <p className="text-lg md:text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              多维度 AIGC 检测引擎，段落级深度分析，专业报告输出。
              <br className="hidden sm:block" />
              帮助你的论文、简历、自媒体内容通过 AI 检测，确保原创性。
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/app"
                className="group inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-blue-500 text-white font-semibold text-base
                           hover:bg-blue-600 transition-all shadow-xl shadow-blue-500/25
                           hover:shadow-2xl hover:shadow-blue-500/30 active:scale-[0.98]"
              >
                免费开始使用
                <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl border-2 border-gray-200 dark:border-gray-700
                           text-gray-700 dark:text-gray-300 font-semibold text-base
                           hover:bg-gray-50 dark:hover:bg-gray-900 transition-all"
              >
                了解更多
              </a>
            </div>

            {/* Highlights */}
            <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
              {highlights.map((h) => {
                const Icon = h.icon;
                return (
                  <div key={h.label} className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-50 dark:bg-gray-900/50">
                    <Icon className="w-5 h-5 text-blue-500" />
                    <span className="text-sm font-semibold">{h.label}</span>
                    <span className="text-xs text-gray-400">{h.desc}</span>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* ─── Features ─── */}
      <section id="features" className="relative max-w-6xl mx-auto px-6 py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            三大核心功能
          </h2>
          <p className="text-gray-500 dark:text-gray-400 max-w-lg mx-auto">
            从检测到改写，全流程覆盖你的文本质量需求
          </p>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          className="grid md:grid-cols-3 gap-8"
        >
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <motion.div
                key={f.title}
                variants={itemAnim}
                className="group relative bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-8 hover:shadow-2xl transition-all duration-300 hover:-translate-y-2"
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-5 shadow-lg ${f.color.includes('blue') ? 'shadow-blue-500/25' : f.color.includes('purple') ? 'shadow-purple-500/25' : 'shadow-emerald-500/25'}`}>
                  <Icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-3">{f.title}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
                  {f.desc}
                </p>
                <div className="mt-6 flex items-center gap-1 text-sm text-blue-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                  了解更多
                  <ChevronRight className="w-4 h-4" />
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </section>

      {/* ─── How It Works ─── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            三步完成检测
          </h2>
          <p className="text-gray-500 dark:text-gray-400">
            从上传到报告，全程不超过 30 秒
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {[
            { step: '01', title: '上传或输入文本', desc: '支持直接输入、文件拖拽上传，PDF/DOCX/TXT 格式，无大小限制，极速解析。', icon: FileSearch },
            { step: '02', title: 'AI 多维分析', desc: '双模型语义分析 + 统计特征检测 + 段落级深度扫描，多引擎并行处理。', icon: ScanEye },
            { step: '03', title: '查看报告 & 改写', desc: '获取专业检测报告，一键降低 AIGC 痕迹。支持 PDF 导出，对标知网/维普报告格式。', icon: PenLine },
          ].map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div
                key={s.step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="relative text-center"
              >
                <div className="text-6xl font-black text-gray-100 dark:text-gray-800 mb-4">{s.step}</div>
                <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-950/40 flex items-center justify-center mx-auto mb-4">
                  <Icon className="w-6 h-6 text-blue-500" />
                </div>
                <h3 className="text-lg font-bold mb-2">{s.title}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">{s.desc}</p>

                {i < 2 && (
                  <div className="hidden md:block absolute top-12 -right-4">
                    <ChevronRight className="w-6 h-6 text-gray-300 dark:text-gray-700" />
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="max-w-6xl mx-auto px-6 py-24">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 via-blue-500 to-purple-600 p-12 md:p-20 text-center"
        >
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMiIvPjwvZz48L2c+PC9zdmc+')] opacity-50" />
          <div className="relative">
            <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-4">
              准备好提升文本质量了？
            </h2>
            <p className="text-blue-100 text-lg mb-10 max-w-lg mx-auto">
              无需注册即可免费使用。专业级 AIGC 检测，让你的内容通过每一次审核。
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/app"
                className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-white text-blue-600 font-semibold
                           hover:bg-gray-50 transition-all active:scale-[0.98] shadow-lg"
              >
                立即体验
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-white/10 text-white font-semibold
                           hover:bg-white/20 transition-all border border-white/20 backdrop-blur-sm"
              >
                注册账号
              </Link>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                <ScanEye className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-bold">
                降<span className="text-blue-500">AIGC</span>
              </span>
            </Link>
            <div className="flex items-center gap-6 text-sm text-gray-400">
              <Link to="/app" className="hover:text-gray-600 dark:hover:text-gray-300 transition-colors">工作台</Link>
              <Link to="/login" className="hover:text-gray-600 dark:hover:text-gray-300 transition-colors">登录</Link>
              <span>&copy; 2026 降AIGC平台</span>
            </div>
          </div>
          <p className="text-center text-xs text-gray-400 mt-8">
            本平台检测结果由自动化系统生成，仅供辅助参考，不构成对文本原创性的最终判定。
          </p>
        </div>
      </footer>
    </div>
  );
}
