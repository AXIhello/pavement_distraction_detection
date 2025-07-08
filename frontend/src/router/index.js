// src/router/index.js（或你配置路由的文件）
import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import FaceRecognition from '@/components/FaceRecognition.vue'

const routes = [
  {
    path: '/',
    redirect: '/login' // ✅ 首次进入默认跳转到登录页
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/face',
    name: 'FaceRecognition',
    component: FaceRecognition
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
