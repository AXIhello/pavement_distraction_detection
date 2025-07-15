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
            <div v-for="(img, idx) in faceImages" :key="img.id" style="display:inline-block; margin-right:10px;">
            <img :src="img.url" alt="人脸照片" class="face-image" />
            <button @click="deleteFace(img.id)">删除</button>
            </div>
        </div>
        <span v-else>暂无照片</span>
      </div>
      <!-- 修改用户名 -->
      <div class="info-item">
        <strong>修改账号（用户名）</strong><br />
        <input v-model="newUsername" placeholder="新用户名" />
        <button @click="changeUsername">修改</button>
        <span class="message">{{ usernameMsg }}</span>
      </div>
      <!-- 修改密码 -->
      <div class="info-item">
        <strong>修改密码</strong><br />
        <input v-model="newPassword" type="password" placeholder="新密码" />
        <input v-model="emailCode" placeholder="邮箱验证码" />
        <button @click="sendEmailCode" :disabled="codeSent">发送验证码</button>
        <button @click="changePassword">修改密码</button>
        <span class="message">{{ passwordMsg }}</span>
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

async function fetchFaceImages() {
  const faceRes = await fetch(FACE_API, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const faceData = await faceRes.json()
  if (faceData.success) {
    faceImages.value = faceData.images.map(img => ({
      id: img.id,
      url: 'http://127.0.0.1:8000' + img.url
    }))
  }
}

// 删除人脸
async function deleteFace(faceId) {
  if (!confirm('确定要删除这张人脸吗？')) return
  const res = await fetch(`http://127.0.0.1:8000/api/auth/delete_face/${faceId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
  const data = await res.json()
  alert(data.message)
  if (data.success) {
    await fetchFaceImages()
  }
}
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
      await fetchFaceImages() // 这里调用
    } else {
      error.value = data.message || '获取用户信息失败'
    }
  } catch (err) {
    error.value = '请求失败，请检查后端服务'
  } finally {
    loading.value = false
  }
})
// 修改用户名相关
const newUsername = ref('')
const usernameMsg = ref('')

async function changeUsername() {
  if (!newUsername.value) {
    usernameMsg.value = '新用户名不能为空'
    return
  }
  const res = await fetch('http://127.0.0.1:8000/api/auth/change_username', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ new_username: newUsername.value })
  })
  const data = await res.json()
  usernameMsg.value = data.message
  if (data.success) {
    user.value.username = newUsername.value
    newUsername.value = ''
  }
}

// 修改密码相关
const newPassword = ref('')
const emailCode = ref('')
const passwordMsg = ref('')
const codeSent = ref(false)

async function sendEmailCode() {
  const res = await fetch('http://127.0.0.1:8000/api/auth/send_email_code', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email: user.value.email })
  })
  const data = await res.json()
  passwordMsg.value = data.message
  if (data.success) codeSent.value = true
}

async function changePassword() {
  if (!newPassword.value || !emailCode.value) {
    passwordMsg.value = '新密码和验证码不能为空'
    return
  }
  const res = await fetch('http://127.0.0.1:8000/api/auth/change_password', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ code: emailCode.value, new_password: newPassword.value })
  })
  const data = await res.json()
  passwordMsg.value = data.message
  if (data.success) {
    newPassword.value = ''
    emailCode.value = ''
    codeSent.value = false
  }
}
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
.message {
  color: #b8860b;
  margin-left: 10px;
  font-size: 14px;
}
</style>
