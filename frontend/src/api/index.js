// frontend/src/api/index.js
import axios from 'axios';

// 创建一个 axios 实例，指定后端地址
const api = axios.create({
  baseURL: '/api/v1',
});

// 请求拦截器：每次发请求前，自动把 Token 塞进 Header 里
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：如果后端报 401（Token过期），自动踢回登录页
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/'; // 刷新页面，回到初始状态
    }
    return Promise.reject(error);
  }
);

export default api;