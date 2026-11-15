import { useState, useEffect } from 'react';
import api from './api';

function App() {
  // === 状态管理 ===
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  // 工作台状态
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [reviewId, setReviewId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle'); 
  const [reportData, setReportData] = useState(null);

  // === 登录逻辑 ===
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await api.post('/auth/login', { username, password });
      localStorage.setItem('token', res.data.access_token);
      setToken(res.data.access_token);
    } catch (err) {
      setError('账号或密码错误');
    }
  };

  // === 退出登录 ===
  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    setReportData(null);
    setReviewId(null);
    setFile(null);
    setStatus('idle');
  };

  // === 上传文件 ===
  const handleUpload = async () => {
    if (!file) return alert('请先选择一个文件！');
    
    setUploading(true);
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/review/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setReviewId(res.data.review_id);
      setStatus('processing');
      setUploading(false);
    } catch (err) {
      alert('上传失败：' + (err.response?.data?.detail || err.message));
      setUploading(false);
      setStatus('idle');
    }
  };

  // === 轮询审查进度 ===
  useEffect(() => {
    let timer = null;
    if (status === 'processing' && reviewId) {
      timer = setInterval(async () => {
        try {
          const res = await api.get(`/review/${reviewId}`);
          setProgress(res.data.progress * 100);
          
          if (res.data.status === 'completed') {
            setStatus('completed');
            setReportData(res.data);
            clearInterval(timer);
          } else if (res.data.status === 'failed') {
            setStatus('failed');
            clearInterval(timer);
          }
        } catch (err) {
          console.error('轮询出错', err);
        }
      }, 1000); // 1秒查一次，进度更丝滑
    }
    return () => clearInterval(timer);
  }, [status, reviewId]);

  // === 下载 PDF ===
  const handleDownload = async () => {
    try {
      const res = await api.get(`/review/${reviewId}/report`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `审查报告_${reviewId.substring(0, 6)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('下载失败');
    }
  };

  // ================= 渲染层 =================

  // 1. 未登录，显示登录页
  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-3xl font-extrabold text-center text-blue-600 mb-8">合同智审系统</h2>
          {error && <div className="bg-red-50 text-red-500 text-sm p-3 rounded-lg mb-4 text-center">{error}</div>}
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">账号</label>
              <input type="text" value={username} onChange={e => setUsername(e.target.value)} className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="请输入 admin" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">密码</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all" placeholder="请输入 admin123" required />
            </div>
            <button type="submit" className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl shadow-md transition-all">立即登录</button>
          </form>
        </div>
      </div>
    );
  }

  // 2. 已登录，显示工作台
  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      {/* 顶部导航 */}
      <nav className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 h-16 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-800 tracking-wide">合同智审工作台</h1>
          <button onClick={handleLogout} className="text-sm font-medium text-gray-500 hover:text-red-500 transition-colors">退出登录</button>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 mt-10">
        {/* 上传区 */}
        {status === 'idle' && (
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-12 text-center">
            <h3 className="text-2xl font-bold text-gray-800 mb-2">上传合同文件</h3>
            <p className="text-gray-500 mb-8">支持 TXT、PDF、DOCX 格式，AI 将自动提取条款与风险</p>
            <input type="file" onChange={e => setFile(e.target.files[0])} className="block mx-auto mb-8 text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer" />
            <button onClick={handleUpload} disabled={uploading || !file} className={`px-10 py-3 rounded-full font-semibold shadow-lg transition-all ${uploading || !file ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}>
              {uploading ? '上传中...' : '开始审查'}
            </button>
          </div>
        )}

        {/* 进度条 */}
        {(status === 'processing' || status === 'uploading') && (
          <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-16 text-center">
            <h3 className="text-xl font-bold text-gray-800 mb-2">AI 正在审查中</h3>
            <p className="text-gray-500 mb-8">正在提取条款、识别风险并生成建议...</p>
            <div className="w-full bg-gray-100 rounded-full h-4 mb-4 overflow-hidden">
              <div className="bg-blue-600 h-4 rounded-full transition-all duration-300 ease-out" style={{ width: `${progress}%` }}></div>
            </div>
            <p className="text-blue-600 font-bold text-lg">{progress.toFixed(1)}%</p>
          </div>
        )}

        {/* 审查报告结果 */}
        {status === 'completed' && reportData && (
          <div className="space-y-6">
            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-green-600">✅ 审查完成</h2>
                <p className="text-gray-500 mt-2">任务编号：{reviewId}</p>
              </div>
              <button onClick={handleDownload} className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-md transition-all">下载 PDF 报告</button>
            </div>

            {/* 降级警告提示 */}
            {reportData.warnings && reportData.warnings.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 p-5 rounded-2xl">
                <h4 className="font-bold text-amber-800 mb-2">⚠️ 系统降级提示</h4>
                <ul className="list-disc list-inside text-amber-700 text-sm space-y-1">
                  {reportData.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}

            {/* 风险列表 */}
            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
              <h3 className="text-xl font-bold text-gray-800 mb-6">🔍 风险发现 <span className="bg-red-100 text-red-600 text-sm py-1 px-3 rounded-full ml-2">{reportData.risk_findings?.length || 0}</span></h3>
              <div className="space-y-4">
                {reportData.risk_findings?.map((r, i) => (
                  <div key={i} className={`p-4 rounded-xl border-l-4 ${r.risk_level === 'high' ? 'border-red-500 bg-red-50/50' : r.risk_level === 'medium' ? 'border-amber-500 bg-amber-50/50' : 'border-green-500 bg-green-50/50'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${r.risk_level === 'high' ? 'bg-red-200 text-red-700' : r.risk_level === 'medium' ? 'bg-amber-200 text-amber-700' : 'bg-green-200 text-green-700'}`}>
                        {r.risk_level.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-800">{r.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* 建议列表 */}
            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
              <h3 className="text-xl font-bold text-gray-800 mb-6">💡 修改建议 <span className="bg-blue-100 text-blue-600 text-sm py-1 px-3 rounded-full ml-2">{reportData.suggestions?.length || 0}</span></h3>
              <div className="grid gap-4">
                {reportData.suggestions?.map((s, i) => (
                  <div key={i} className="p-5 border border-gray-100 rounded-2xl bg-gray-50 hover:bg-white transition-colors">
                    <div className="mb-3">
                      <span className="font-bold text-gray-700">问题：</span>
                      <span className="text-gray-800">{s.issue}</span>
                    </div>
                    <div className="mb-4">
                      <span className="font-bold text-blue-700">建议：</span>
                      <span className="text-blue-800">{s.suggestion}</span>
                    </div>
                    <span className={`inline-block px-3 py-1 text-xs font-bold rounded-full ${s.priority === 'high' ? 'bg-red-100 text-red-600' : 'bg-gray-200 text-gray-600'}`}>
                      优先级: {s.priority.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;