// src/utils/http.js
import axios from 'axios'

const http = axios.create({
  baseURL: 'http://127.0.0.1:8000/api', 

  timeout: 5000,
})

// 请求拦截器：自动加 token
http.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

// 响应拦截器（可选：自动处理 401 错误或其他通用逻辑）
http.interceptors.response.use(response => response, error => {
  if (error.response && error.response.status === 401) {
    console.warn('未认证或Token过期')
    // 可跳转到登录页或提示
    // window.location.href = '/login'
  }
  return Promise.reject(error)
})

export default http
