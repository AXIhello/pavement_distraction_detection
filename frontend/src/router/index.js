// Vue 路由配置
import { createRouter, createWebHistory } from 'vue-router'
import LoginByPassword from '@/views/LoginByPassword.vue'

const routes = [
  {
    path: '/login',
    name: 'LoginByPassword',
    component: LoginByPassword,
  },
  // 其他路由...
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
