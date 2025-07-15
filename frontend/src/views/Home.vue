<template>
  <Header />
  <div class="home-container">
    <h1>用户信息</h1>

    <div v-if="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="user-info">
      <div class="info-item"><strong>账号：</strong>{{ user.username }}</div>
      <div class="info-item"><strong>角色：</strong>{{ user.role }}</div>
      <div class="info-item"><strong>邮箱：</strong>{{ user.email }}</div>
      <div class="info-item">
        <strong>已录入人脸照片</strong><br />
        <div v-if="faceImages.length">
            <img v-for="(img, idx) in faceImages" :key="idx" :src="img" alt="人脸照片" class="face-image" />
        </div>
        <span v-else>暂无照片</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Header from '@/components/Navigation.vue'

const user = ref({})
const loading = ref(true)
const error = ref('')
const faceImages = ref([])

const token = localStorage.getItem('token')
const API_URL = 'http://127.0.0.1:8000/api/auth/me'
const FACE_API = 'http://127.0.0.1:8000/api/face/my_faces'

onMounted(async () => {
  try {
    // 获取用户信息
    const res = await fetch(API_URL, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })
    const data = await res.json()
    if (data.success) {
      user.value = data.user
      // 获取人脸图片
      const faceRes = await fetch(FACE_API, {
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      })
      const faceData = await faceRes.json()
      if (faceData.success) {
        faceImages.value = faceData.images.map(url => 'http://127.0.0.1:8000' + url)
      }
    } else {
      error.value = data.message || '获取用户信息失败'
    }
  } catch (err) {
    error.value = '请求失败，请检查后端服务'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* 固定 Header */
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #333;
  color: white;
  padding: 10px 0;
  text-align: center;
  z-index: 1000;
}

/* 页面内容区域，避免被 Header 遮挡 */
.home-container {
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fafafa;
  font-family: Arial, sans-serif;
  margin-top: 60px; /* 使内容不被固定的 Header 遮挡 */
}

h1 {
  text-align: center;
  margin-bottom: 24px;
}

.info-item {
  margin-bottom: 16px;
  font-size: 16px;
}

.face-image {
  margin-top: 10px;
  max-width: 100%;
  height: auto;
  border: 1px solid #ccc;
  border-radius: 6px;
}

.error {
  color: red;
  text-align: center;
}
</style>
