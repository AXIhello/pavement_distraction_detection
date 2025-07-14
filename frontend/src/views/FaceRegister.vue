<template>
  <div class="face-register">
    <!-- 左侧：摄像头或图片预览 -->
    <div class="left-panel">
      <div class="video-container" v-if="!photoCaptured">
        <video ref="video" autoplay playsinline></video>
      </div>
      <div class="photo-preview" v-else>
        <img :src="capturedPhoto" alt="拍摄照片预览" />
      </div>
    </div>

    <!-- 右侧：提示与操作 -->
    <div class="right-panel">
      <h2>人脸信息录入</h2>
      <p class="tip">操作步骤：</p>
      <ol class="steps">
        <li>点击「打开摄像头」</li>
        <li>点击「拍照」获取图像</li>
        <li>输入姓名（支持中文）</li>
        <li>点击「保存」完成录入</li>
      </ol>

      <input v-model="name" placeholder="请输入姓名（支持中文）" />

      <div class="buttons">
        <button @click="startCamera" v-if="!streaming && !photoCaptured">打开摄像头</button>
        <button @click="capturePhoto" v-if="streaming && !photoCaptured">拍照</button>
        <button @click="clearPhoto" v-if="photoCaptured">重拍</button>
        <button @click="savePhoto" :disabled="!capturedPhoto || !name || loading">{{ loading ? '处理中...' : '保存' }}</button>
      </div>

      <p class="message">{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const video = ref(null)
const name = ref('')
const capturedPhoto = ref('')
const message = ref('')
const streaming = ref(false)
const photoCaptured = ref(false)
let stream = null

// 打开摄像头
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

// 关闭摄像头
function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
    streaming.value = false
  }
}

// 拍照
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



// 重拍
function clearPhoto() {
  capturedPhoto.value = ''
  photoCaptured.value = false
  message.value = '照片已清除，请重新拍摄'

  // 重新开启摄像头
  startCamera()
}

const loading = ref(false)
// 保存人脸数据
async function savePhoto() {
  if (!capturedPhoto.value || !name.value) {
    message.value = '请先拍照并输入姓名'
    return
  }
  loading.value = true
  message.value = '正在处理中，请稍候...'

  try {
    const token = localStorage.getItem('token')
    console.log('savePhoto: token =', token)
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
    console.log('savePhoto: fetch 响应状态', res.status)
    const data = await res.json()
    console.log('savePhoto: 返回数据', data)

    if (data.success) {
      message.value = '录入成功！'
    } else {
      message.value = '录入失败！' + (data.message || '')
    }
  } catch (err) {
    console.error('savePhoto 请求异常:', err)
    message.value = '请求失败，请检查后端服务'
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.face-register {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 40px;
  padding: 40px;
  font-family: "Arial", sans-serif;
  color: #222;
}

.left-panel {
  width: 50%;
  max-width: 500px;
  background-color: #000;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.video-container,
.photo-preview {
  width: 100%;
  aspect-ratio: 4/3;
}

video,
img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.right-panel {
  width: 40%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

h2 {
  margin: 0;
  font-size: 24px;
  color: #000;
}

.tip {
  font-weight: bold;
}

.steps {
  padding-left: 20px;
  font-size: 14px;
  line-height: 1.6;
  color: #444;
}

input {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #aaa;
  border-radius: 6px;
  background-color: #fff;
}

.buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

button {
  padding: 10px 16px;
  font-size: 14px;
  background-color: #333;
  border: none;
  color: #f5f5dc;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background-color: #000;
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