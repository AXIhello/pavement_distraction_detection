// Vue 路由配置
import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  // 其他路由...
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
