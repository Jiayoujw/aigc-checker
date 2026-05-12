interface Props {
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
}

export default function TextInput({ value, onChange, maxLength = 5000 }: Props) {
  return (
    <div>
      <textarea
        className="w-full h-52 p-4 border border-gray-300 dark:border-gray-700
                   rounded-lg resize-none bg-white dark:bg-gray-900
                   focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   text-gray-800 dark:text-gray-200 placeholder-gray-400
                   dark:placeholder-gray-500 text-sm leading-relaxed
                   transition-shadow"
        placeholder="在此粘贴需要检测的文本（至少50字，支持中文/英文）..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={maxLength}
      />
      <div className="flex justify-between items-center mt-2 px-1">
        <span className="text-xs text-gray-400">
          {value.length < 50 && value.length > 0
            ? `还差 ${50 - value.length} 字达到最低要求`
            : ''}
        </span>
        <span
          className={`text-xs ${
            value.length > maxLength * 0.9 ? 'text-orange-500' : 'text-gray-400'
          }`}
        >
          {value.length} / {maxLength}
        </span>
      </div>
    </div>
  );
}
