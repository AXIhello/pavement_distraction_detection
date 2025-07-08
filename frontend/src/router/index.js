// Vue 路由配置
import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import FaceRecognition from '@/components/FaceRecognition.vue'  // 摄像头组件的路径

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/',
    redirect: '/face'  // 默认打开人脸识别页
  },
  {
    path: '/face',
    name: 'FaceRecognition',
    component: FaceRecognition
  }

  // 其他路由...
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
