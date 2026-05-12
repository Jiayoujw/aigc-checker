import { useState, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { toast } from './Toast';

interface Props {
  onTextExtracted: (text: string) => void;
}

const API_BASE = import.meta.env.PROD
  ? 'https://aigc-checker.onrender.com/api'
  : '/api';

export default function FileUpload({ onTextExtracted }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      const allowed = ['.txt', '.docx', '.pdf'];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!allowed.includes(ext)) {
        toast('仅支持 .txt, .docx, .pdf 格式', 'error');
        return;
      }

      setFileName(file.name);
      setUploading(true);

      try {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch(`${API_BASE}/upload`, {
          method: 'POST',
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: '上传失败' }));
          throw new Error(err.detail);
        }
        const data = await res.json();
        onTextExtracted(data.text);
        toast(`提取成功，${data.text.length} 字`, 'success');
      } catch (e) {
        toast(e instanceof Error ? e.message : '上传失败', 'error');
        setFileName(null);
      } finally {
        setUploading(false);
      }
    },
    [onTextExtracted]
  );

  return (
    <motion.div
      className={`relative border-2 border-dashed rounded-xl p-10 text-center transition-colors
        ${dragOver
          ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900'
        }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.docx,.pdf"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500">正在解析 {fileName}...</p>
        </div>
      ) : fileName ? (
        <div className="text-gray-500">
          <p className="text-2xl mb-2">{'📄'}</p>
          <p className="text-sm">{fileName}</p>
          <p className="text-xs mt-1">点击重新上传</p>
        </div>
      ) : (
        <div className="text-gray-400">
          <p className="text-3xl mb-3">{'📁'}</p>
          <p className="text-sm font-medium">拖拽文件到此处，或点击上传</p>
          <p className="text-xs mt-1">支持 .txt / .docx / .pdf</p>
        </div>
      )}
    </motion.div>
  );
}
