// src/router/index.js（或你配置路由的文件）
import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import FaceRecognition from '@/components/FaceRecognition.vue'
import Home from '@/views/Home.vue'
import FaceRegister from '@/views/FaceRegister.vue'
import Detect from '@/views/Detect.vue'

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
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  },
  {
    path: '/face_register',
    name: 'FaceRegister',
    component: FaceRegister
  },
  {
    path: '/detect',
    name: 'Detect',
    component: Detect
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
