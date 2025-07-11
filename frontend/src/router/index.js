import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import FaceRecognition from '@/components/FaceRecognition.vue'
import Home from '@/views/Home.vue'
import FaceRegister from '@/views/FaceRegister.vue'
import Detect from '@/views/Detect.vue'
import Admin from '@/views/Admin.vue'
import RoadLog from '@/components/RoadWarn.vue'
import Log from '@/views/Log.vue'
import FirstPage from '@/views/FirstPage.vue'

const routes = [
  {
    path: '/',
    redirect: '/login' // 首次进入默认跳转登录页
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/face',
    name: 'FaceRecognition',
    component: FaceRecognition,
    meta: { requiresAuth: true }
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/face_register',
    name: 'FaceRegister',
    component: FaceRegister,
    meta: { requiresAuth: true }
  },
  {
    path: '/detect',
    name: 'Detect',
    component: Detect,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true }
  },
  {
    path:'/road',
    name:'Road',
    component: RoadLog,
    meta: { requiresAuth: true }
  },
  {
    path:'/first_page',
    name:'FirstPage',
    component: FirstPage,
    meta: { requiresAuth: true }
  },
  {
    path: '/log',
    name:'Log',
    component: Log,
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// // 路由拦截守卫
// router.beforeEach((to, from, next) => {
//   // 简单示例，token存在则认为登录了
//   const token = localStorage.getItem('token') 

//   if (to.meta.requiresAuth && !token) {
//     // 要访问的页面需要登录，但没登录，跳登录页
//     next({ name: 'Login' })
//   } else if (to.name === 'Login' && token) {
//     // 已登录，禁止访问登录页，跳首页
//     next({ name: 'Home' })
//   } else {
//     // 正常访问
//     next()
//   }
// })

export default router
