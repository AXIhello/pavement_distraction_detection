<template>
  <div class="face-register-container">
    <h2>人脸信息录入</h2>

    <div class="content">
      <!-- 左边摄像头/图片 -->
      <div class="video-section">
        <div v-if="!photoCaptured">
          <video ref="video" autoplay playsinline></video>
        </div>
        <div v-else>
          <img :src="capturedPhoto" alt="拍摄照片预览" />
        </div>
      </div>

      <!-- 右边操作区 -->
      <div class="control-section">
        <p class="tip">操作步骤：</p>
        <ol class="steps">
          <li>点击「打开摄像头」</li>
          <li>点击「拍照」获取图像</li>
          <li>输入姓名（支持中文）</li>
          <li>点击「保存」完成录入</li>
        </ol>

        <input v-model="name" placeholder="请输入姓名（支持中文）" />

        <div class="button-group">
          <button @click="startCamera" v-if="!streaming && !photoCaptured">打开摄像头</button>
          <button @click="capturePhoto" v-if="streaming && !photoCaptured">拍照</button>
          <button @click="clearPhoto" v-if="photoCaptured">重拍</button>
          <button @click="savePhoto" :disabled="!capturedPhoto || !name || loading">
            {{ loading ? '处理中...' : '保存' }}
          </button>
          <button @click="() => router.push('/first_page')">返回首页</button>
        </div>

        <p class="message">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const video = ref(null)
const name = ref('')
const capturedPhoto = ref('')
const message = ref('')
const streaming = ref(false)
const photoCaptured = ref(false)
const loading = ref(false)
let stream = null

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream
    streaming.value = true
    message.value = '摄像头已开启'
  } catch (err) {
    message.value = '无法打开摄像头：' + err.message
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
    streaming.value = false
  }
}

function capturePhoto() {
  const canvas = document.createElement('canvas')
  canvas.width = video.value.videoWidth
  canvas.height = video.value.videoHeight
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)

  capturedPhoto.value = canvas.toDataURL('image/png')
  photoCaptured.value = true
  message.value = '已拍照，准备保存或重拍'
  stopCamera()
}

function clearPhoto() {
  capturedPhoto.value = ''
  photoCaptured.value = false
  message.value = '照片已清除，请重新拍摄'
  startCamera()
}

async function savePhoto() {
  if (!capturedPhoto.value || !name.value) {
    message.value = '请先拍照并输入姓名'
    return
  }
  loading.value = true
  message.value = '正在处理中，请稍候...'

  try {
    const token = localStorage.getItem('token')
    if (!token) {
      message.value = '缺少token，请先登录'
      loading.value = false
      return
    }

    const res = await fetch('http://127.0.0.1:8000/api/face/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        name: name.value,
        image: capturedPhoto.value
      })
    })

    const data = await res.json()

    if (data.success) {
      message.value = '录入成功！'
    } else {
      message.value = '录入失败！' + (data.message || '')
    }
  } catch (err) {
    message.value = '请求失败，请检查后端服务'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.face-register-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 40px;
  background-color: #f9f9f9;
  border-radius: 16px;
  max-width: 1000px;
  margin: 60px auto;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  font-family: "Arial", sans-serif;
}

.face-register-container h2 {
  font-size: 28px;
  margin-bottom: 24px;
  color: #333;
}

.content {
  display: flex;
  gap: 30px;
  width: 100%;
  margin-bottom: 30px;
}

.video-section {
  flex: 6;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3);
}

.video-section video,
.video-section img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.control-section {
  flex: 4;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.tip {
  font-weight: bold;
  margin-bottom: 8px;
}

.steps {
  padding-left: 20px;
  font-size: 14px;
  line-height: 1.6;
  color: #444;
  margin-bottom: 12px;
}

input {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #aaa;
  border-radius: 6px;
  background-color: #fff;
  margin-bottom: 12px;
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

button {
  padding: 10px 20px;
  font-size: 14px;
  background-color: #d7c480;
  border: none;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background-color: #b5a25a;
}

button:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

.message {
  font-size: 14px;
  color: #800000;
  margin-top: 10px;
}
</style>
