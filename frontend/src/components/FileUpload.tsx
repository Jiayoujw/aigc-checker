import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileText, File, Check, AlertTriangle, Gauge } from 'lucide-react';
import { toast } from './Toast';

interface Props {
  onTextExtracted: (text: string) => void;
}

interface Progress {
  stage: 'upload' | 'parsing' | 'done' | 'error';
  progress: number;
  size_mb?: number;
}

const API_BASE = import.meta.env.PROD
  ? 'https://aigc-checker.onrender.com/api'
  : '/api';

const ALLOWED_EXTS = ['.txt', '.docx', '.pdf'];

function formatSpeed(mbPerSec: number): string {
  if (mbPerSec >= 1) return `${mbPerSec.toFixed(1)} MB/s`;
  return `${(mbPerSec * 1024).toFixed(0)} KB/s`;
}

export default function FileUpload({ onTextExtracted }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [fileSize, setFileSize] = useState<number>(0);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [speed, setSpeed] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<{ filename: string; length: number; time_ms: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const startTimeRef = useRef<number>(0);
  const sizeRef = useRef<number>(0);

  // Cleanup progress state after done/error
  useEffect(() => {
    if (progress?.stage === 'done' || progress?.stage === 'error') {
      const t = setTimeout(() => {
        setProgress(null);
        setSpeed(null);
        setError(null);
      }, 5000);
      return () => clearTimeout(t);
    }
  }, [progress]);

  const getFileIcon = (name: string) => {
    const ext = '.' + name.split('.').pop()?.toLowerCase();
    if (ext === '.pdf') return <FileText className="w-5 h-5 text-red-500" />;
    if (ext === '.docx') return <FileText className="w-5 h-5 text-blue-500" />;
    return <File className="w-5 h-5 text-gray-500" />;
  };

  const handleFile = useCallback(
    async (file: File) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!ALLOWED_EXTS.includes(ext)) {
        toast('仅支持 .txt, .docx, .pdf 格式', 'error');
        return;
      }

      setFileName(file.name);
      setFileSize(file.size);
      setUploading(true);
      setError(null);
      setLastResult(null);
      setProgress({ stage: 'upload', progress: 0 });
      startTimeRef.current = performance.now();
      sizeRef.current = 0;

      try {
        const formData = new FormData();
        formData.append('file', file);

        // Use XMLHttpRequest for upload progress tracking
        const xhr = new XMLHttpRequest();

        const result = await new Promise<{
          text: string; filename: string; length: number;
          task_id: string; parse_time_ms: number; size_mb: number;
        }>((resolve, reject) => {
          xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
              const pct = Math.round((e.loaded / e.total) * 49);
              const elapsed = (performance.now() - startTimeRef.current) / 1000;
              const loadedMB = e.loaded / (1024 * 1024);
              const spd = elapsed > 0 ? loadedMB / elapsed : 0;
              setSpeed(formatSpeed(spd));
              setProgress({ stage: 'upload', progress: pct, size_mb: loadedMB });
              sizeRef.current = e.loaded;
            }
          });

          xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              try {
                resolve(JSON.parse(xhr.responseText));
              } catch {
                reject(new Error('服务器返回异常'));
              }
            } else {
              try {
                const err = JSON.parse(xhr.responseText);
                reject(new Error(err.detail || '上传失败'));
              } catch {
                reject(new Error(`上传失败 (${xhr.status})`));
              }
            }
          });

          xhr.addEventListener('error', () => reject(new Error('网络连接失败')));
          xhr.addEventListener('abort', () => reject(new Error('上传已取消')));

          xhr.open('POST', `${API_BASE}/upload`);
          xhr.send(formData);
        });

        // Parsing phase — poll progress via SSE or just show completion
        const totalTime = performance.now() - startTimeRef.current;
        setProgress({ stage: 'done', progress: 100, size_mb: result.size_mb });
        setSpeed(formatSpeed(result.size_mb / (totalTime / 1000)));

        onTextExtracted(result.text);
        setLastResult({
          filename: result.filename,
          length: result.length,
          time_ms: result.parse_time_ms,
        });
        toast(`${result.filename} — ${result.length} 字，${result.parse_time_ms}ms`, 'success');
      } catch (e) {
        const msg = e instanceof Error ? e.message : '上传失败';
        setError(msg);
        setProgress({ stage: 'error', progress: 0 });
        toast(msg, 'error');
      } finally {
        setUploading(false);
      }
    },
    [onTextExtracted]
  );

  // Track overall progress including parsing
  useEffect(() => {
    if (!uploading || !progress) return;

    // Simulate parsing progress while waiting for server response
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (!prev) return prev;
        if (prev.stage === 'upload' && prev.progress >= 48) {
          return { ...prev, stage: 'parsing', progress: 50 };
        }
        if (prev.stage === 'parsing' && prev.progress < 95) {
          return { ...prev, progress: prev.progress + Math.random() * 10 };
        }
        return prev;
      });
    }, 300);

    return () => clearInterval(timer);
  }, [uploading]);

  const displayProgress = progress?.progress ?? 0;

  return (
    <div className="space-y-3">
      <motion.div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
          ${dragOver
            ? 'border-blue-400 bg-blue-50/50 dark:bg-blue-900/10'
            : error
            ? 'border-red-300 bg-red-50/30 dark:bg-red-900/5'
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-500 bg-white dark:bg-gray-800/50'
          } ${uploading ? 'pointer-events-none' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        onClick={() => !uploading && inputRef.current?.click()}
        whileHover={uploading ? {} : { scale: 1.01 }}
        whileTap={uploading ? {} : { scale: 0.99 }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".txt,.docx,.pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = '';
          }}
        />

        <AnimatePresence mode="wait">
          {uploading || progress ? (
            <motion.div
              key="progress"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-4 py-4"
            >
              {/* File info */}
              <div className="flex items-center gap-3">
                {getFileIcon(fileName || '')}
                <span className="text-sm font-medium text-gray-700 dark:text-gray-200 truncate max-w-[200px]">
                  {fileName}
                </span>
                {fileSize > 0 && (
                  <span className="text-xs text-gray-400">
                    {(fileSize / (1024 * 1024)).toFixed(1)} MB
                  </span>
                )}
              </div>

              {/* Progress bar */}
              <div className="w-full max-w-xs">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>{progress?.stage === 'upload' ? '上传中' : progress?.stage === 'parsing' ? '解析中' : progress?.stage === 'done' ? '完成' : ''}</span>
                  <span>{Math.round(displayProgress)}%</span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full transition-colors ${
                      error ? 'bg-red-500' :
                      progress?.stage === 'done' ? 'bg-green-500' :
                      'bg-blue-500'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${displayProgress}%` }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                  />
                </div>
                {speed && (
                  <div className="flex items-center justify-center gap-1 mt-2 text-xs text-gray-400">
                    <Gauge className="w-3 h-3" />
                    <span>{speed}</span>
                    {progress?.size_mb && (
                      <span>· {progress.size_mb.toFixed(1)} MB</span>
                    )}
                  </div>
                )}
              </div>

              {error && (
                <div className="flex items-center gap-2 text-sm text-red-500">
                  <AlertTriangle className="w-4 h-4" />
                  <span>{error}</span>
                </div>
              )}
            </motion.div>
          ) : lastResult ? (
            <motion.div
              key="done"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center gap-2 py-2"
            >
              <div className="flex items-center gap-2 text-green-600">
                <Check className="w-5 h-5" />
                <span className="text-sm font-medium">{lastResult.filename}</span>
              </div>
              <p className="text-xs text-gray-400">
                {lastResult.length.toLocaleString()} 字 · {lastResult.time_ms}ms 解析
              </p>
              <p className="text-xs text-blue-400 cursor-pointer hover:underline" onClick={(e) => { e.stopPropagation(); }}>
                点击重新上传
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-3 py-4"
            >
              <Upload className="w-10 h-10 text-gray-300 dark:text-gray-600" />
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  拖拽文件到此处，或 <span className="text-blue-500">点击上传</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  支持 .txt / .docx / .pdf · 无大小限制 · 极速解析
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Quick action chips */}
      <div className="flex gap-2 text-xs text-gray-400">
        <span className="inline-flex items-center gap-1">
          <FileText className="w-3 h-3 text-red-400" /> PDF
        </span>
        <span className="inline-flex items-center gap-1">
          <FileText className="w-3 h-3 text-blue-400" /> DOCX
        </span>
        <span className="inline-flex items-center gap-1">
          <File className="w-3 h-3" /> TXT
        </span>
      </div>
    </div>
  );
}
