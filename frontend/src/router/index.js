import { createRouter, createWebHistory } from 'vue-router'
import { jwtDecode } from 'jwt-decode'

import Login from '@/views/Login.vue'
import FaceRecognition from '@/components/FaceRecognition.vue'
import Home from '@/views/Home.vue'
import FaceRegister from '@/views/FaceRegister.vue'
import Detect from '@/views/Detect.vue'
import Admin from '@/views/Admin.vue'
import RoadLog from '@/components/RoadWarn.vue'
import Warning from '@/views/Warning.vue'
import Log from '@/views/Log.vue'
import FirstPage from '@/views/FirstPage.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/face', name: 'FaceRecognition', component: FaceRecognition, meta: { requiresAuth: true } },
  { path: '/home', name: 'Home', component: Home, meta: { requiresAuth: true } },
  { path: '/face_register', name: 'FaceRegister', component: FaceRegister, meta: { requiresAuth: true } },
  { path: '/detect', name: 'Detect', component: Detect, meta: { requiresAuth: true } },
  { path: '/admin', name: 'Admin', component: Admin, meta: { requiresAuth: true } },
  { path: '/road', name: 'Road', component: RoadLog, meta: { requiresAuth: true } },
  { path: '/first_page', name: 'FirstPage', component: FirstPage, meta: { requiresAuth: true } },
  { path: '/warning', name: 'Warning', component: Warning, meta: { requiresAuth: true } },
  { path: '/log', name: 'Log', component: Log, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

//先全部放行
// router.beforeEach((to, from, next) => {
//   const token = localStorage.getItem('token')

//   // 如果需要登录但没token，跳登录页
//   if (to.meta.requiresAuth && !token) {
//     return next({ name: 'Login' })
//   }

//   let userRole = null
//   if (token) {
//     try {
//       const decoded = jwtDecode(token)  // ✅ 此处修复
//       userRole = decoded.role
//     } catch (err) {
//       localStorage.removeItem('token')
//       return next({ name: 'Login' })
//     }
//   }

//   // 管理员专属页面拦截
//   if ((to.path === '/admin' || to.path === '/log') && userRole !== 'admin') {
//     return next({ name: 'Home' }) // 非管理员跳回首页
//   }

//   // 已登录用户禁止访问登录页
//   if (to.name === 'Login' && token) {
//     return next({ name: 'Home' })
//   }

//   next()
// })

export default router
