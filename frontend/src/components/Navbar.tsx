export default function Navbar() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">&#x1F50D;</span>
          <div>
            <h1 className="text-lg font-bold text-gray-900">
              降AIGC &middot; 查重平台
            </h1>
            <p className="text-xs text-gray-500">
              AI检测 &middot; 智能改写 &middot; 查重比对
            </p>
          </div>
        </div>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
          MVP v0.1.0
        </span>
      </div>
    </header>
  );
}
