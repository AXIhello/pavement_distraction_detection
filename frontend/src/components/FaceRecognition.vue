<template>
  <div class="face-camera">
    <h2>人脸识别</h2>
    <div class="video-container">
      <video ref="video" autoplay playsinline></video>
    </div>
    <button @click="startCamera">开启摄像头识别</button>
    <p class="tip">请正对摄像头，系统将自动识别您的人脸</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const video = ref(null)
let ws = null
let streamInterval = null

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream

    ws = new WebSocket('ws://127.0.0.1:8000/ws/face')

    ws.onopen = () => {
      streamInterval = setInterval(() => {
        const canvas = document.createElement('canvas')
        canvas.width = video.value.videoWidth
        canvas.height = video.value.videoHeight
        const ctx = canvas.getContext('2d')
        ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)

        const base64Image = canvas.toDataURL('image/jpeg')
        ws.send(JSON.stringify({ image: base64Image }))
      }, 200)
    }

    ws.onmessage = (e) => {
      const result = JSON.parse(e.data)
      console.log('识别结果:', result)
    }

    ws.onclose = () => {
      clearInterval(streamInterval)
    }
  } catch (err) {
    alert('无法访问摄像头：' + err.message)
  }
}
</script>

<style scoped>
.face-camera {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  font-family: "Arial", sans-serif;
  background-color: #f9f9f9;
  border-radius: 16px;
  max-width: 480px;
  margin: 60px auto;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.face-camera h2 {
  font-size: 28px;
  margin-bottom: 24px;
  color: #333;
}

.video-container {
  width: 100%;
  aspect-ratio: 4/3;
  background-color: #000;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3);
}

video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

button {
  margin-top: 20px;
  padding: 12px 24px;
  font-size: 16px;
  border: none;
  background-color: #d7c480;
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover {
  background-color: #005fcc;
}

.tip {
  margin-top: 16px;
  font-size: 14px;
  color: #666;
}
</style>
