import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ScanEye, Mail, Lock, User, ArrowRight, Eye, EyeOff, AlertCircle, CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { toast } from '../components/Toast';
import ThemeToggle from '../components/ThemeToggle';

const passwordRules = [
  { test: (p: string) => p.length >= 6, label: '至少 6 个字符' },
  { test: (p: string) => /[A-Z]/.test(p), label: '包含大写字母' },
  { test: (p: string) => /[0-9]/.test(p), label: '包含数字' },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password.length < 6) {
      setError('密码至少需要 6 个字符');
      return;
    }

    setLoading(true);
    try {
      await register(email, name, password);
      toast('注册成功', 'success');
      navigate('/app');
    } catch (err) {
      const msg = err instanceof Error ? err.message : '注册失败';
      setError(msg);
      toast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const passwordStrength = passwordRules.filter(r => r.test(password)).length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex">
      {/* Left: decorative panel */}
      <div className="hidden lg:flex lg:w-5/12 bg-gradient-to-br from-emerald-600 via-teal-500 to-blue-600 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMiIvPjwvZz48L2c+PC9zdmc+')] opacity-50" />
        <div className="relative flex flex-col justify-center p-16 text-white">
          <Link to="/" className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
              <ScanEye className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold">降AIGC</span>
          </Link>
          <h2 className="text-4xl font-bold leading-tight mb-6">
            开始你的
            <br />
            文本检测之旅
          </h2>
          <p className="text-emerald-100 text-lg leading-relaxed">
            注册即享完整功能：
            <br />
            历史记录、段落级分析、专业报告导出。
          </p>
          <div className="mt-12 space-y-4 text-sm text-emerald-200">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">1</div>
              免费的无限次检测
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">2</div>
              保存和管理检测历史
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">3</div>
              导出专业 PDF 报告
            </div>
          </div>
        </div>
      </div>

      {/* Right: form */}
      <div className="flex-1 flex items-center justify-center px-6 py-8">
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <Link to="/" className="lg:hidden flex items-center gap-2 mb-10 justify-center">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <ScanEye className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">降AIGC</span>
          </Link>

          <h1 className="text-2xl font-bold mb-1">创建账号</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">
            注册即可保存检测记录和历史
          </p>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 p-3 mb-4 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm"
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">
                <User className="w-3.5 h-3.5" />
                姓名
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => { setName(e.target.value); setError(''); }}
                className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                           bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm
                           focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                           placeholder-gray-400 transition-all outline-none"
                placeholder="你的名字"
              />
            </div>

            <div>
              <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">
                <Mail className="w-3.5 h-3.5" />
                邮箱地址
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(''); }}
                className="w-full px-4 py-3 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                           bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm
                           focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                           placeholder-gray-400 transition-all outline-none"
                placeholder="your@email.com"
                autoComplete="email"
              />
            </div>

            <div>
              <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1.5">
                <Lock className="w-3.5 h-3.5" />
                密码
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(''); }}
                  className="w-full px-4 py-3 pr-10 border-2 border-gray-200 dark:border-gray-700 rounded-xl
                             bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm
                             focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500
                             placeholder-gray-400 transition-all outline-none"
                  placeholder="至少6位，建议包含大小写字母和数字"
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Password strength indicator */}
              {password.length > 0 && (
                <div className="mt-2 space-y-1.5">
                  <div className="flex gap-1.5">
                    {[1, 2, 3].map((i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-colors ${
                          i <= passwordStrength
                            ? passwordStrength === 3
                              ? 'bg-emerald-500'
                              : passwordStrength === 2
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                            : 'bg-gray-200 dark:bg-gray-700'
                        }`}
                      />
                    ))}
                  </div>
                  <div className="space-y-0.5">
                    {passwordRules.map((rule) => {
                      const passed = rule.test(password);
                      return (
                        <div key={rule.label} className="flex items-center gap-1.5 text-xs">
                          {passed
                            ? <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                            : <div className="w-3 h-3 rounded-full border border-gray-300 dark:border-gray-600" />
                          }
                          <span className={passed ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400'}>
                            {rule.label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold text-sm
                         hover:from-emerald-600 hover:to-teal-700 disabled:opacity-60 transition-all shadow-lg shadow-emerald-500/25
                         active:scale-[0.98]"
            >
              {loading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  创建账号
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <p className="text-sm text-gray-500 text-center mt-6">
            已有账号？{' '}
            <Link to="/login" className="text-emerald-500 hover:text-emerald-600 font-medium transition-colors">
              立即登录
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
