<template>
    <Header />
    <div class="home-container">
      <h1>用户信息</h1>
  
      <div v-if="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="user-info">
        <div class="info-item"><strong>账号：</strong>{{ user.username }}</div>
        <div class="info-item"><strong>电话：</strong>{{ user.phone }}</div>
        <div class="info-item"><strong>邮箱：</strong>{{ user.email }}</div>
        <div class="info-item">
          <strong>人脸识别照片：</strong><br />
          <img v-if="user.face_image_url" :src="user.face_image_url" alt="人脸照片" class="face-image" />
          <span v-else>暂无照片</span>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import Header from '@/components/navigation.vue'
  
  const user = ref({})
  const loading = ref(true)
  const error = ref('')
  
  // 后端接口路径（请根据实际修改）
  const API_URL = 'http://127.0.0.1:5000/api/user_info'
  
  onMounted(async () => {
    try {
      const res = await fetch(API_URL)
      const data = await res.json()
      if (data.success) {
        user.value = data.user
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
  .home-container {
    max-width: 600px;
    margin: 40px auto;
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background-color: #fafafa;
    font-family: Arial, sans-serif;
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