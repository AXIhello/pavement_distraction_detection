<template>
  <div class="face-camera">
    <h2>人脸识别</h2>
    <div class="video-container">
      <video ref="video" autoplay playsinline></video>
    </div>
    <div class="progress-bar">
      <div class="progress-inner" :style="{ width: progress + '%' }"></div>
    </div>
    <p class="progress-status">{{ progressStatus }}</p>
    <button @click="startCamera">开启摄像头识别</button>
    <p class="tip">请正对摄像头，系统将自动识别您的人脸</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { io } from 'socket.io-client'

const router = useRouter()
const video = ref(null)

let socket = null
let streamInterval = null
let stream = null
let isWaitingForResult = false // 是否正在等待结果
let frameCount = 0 // 当前批次已发送的帧数
const FRAMES_PER_BATCH = 5 // 每批次发送5帧
const BATCH_INTERVAL = 200 // 批次内每帧间隔200ms
const WAIT_TIME = 1000 // 等待结果时间1000ms

const progress = ref(0) // 进度条百分比
const progressStatus = ref('识别准备中...') // 状态提示

async function startCamera() {
  try {
    // 打开摄像头
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream

    // 连接 SocketIO
    socket = io('http://127.0.0.1:8000')

    socket.on('connect', () => {
      console.log('SocketIO 已连接')
      progress.value = 0
      progressStatus.value = '识别中...'
      startImageStream()
    })

    socket.on('face_result', (result) => {
      console.log('识别结果:', result);
      isWaitingForResult = false // 收到结果，停止等待
      progress.value = 100
      progressStatus.value = '识别完成'
      setTimeout(() => {
        progress.value = 0
        progressStatus.value = '识别中...'
      }, 1000)

      if (result.success) {
        const face = result.faces[0];
        if (face.name === '陌生人') {
          alert('告警：检测到陌生人！');
          // 停止摄像头 & 关闭 SocketIO
          clearInterval(streamInterval)
          stream.getTracks().forEach(track => track.stop())
          socket.disconnect()
          // 跳转到登录界面
          router.push('/login')
          return;
        }
        console.log('识别成功:', result.faces);
        // 停止摄像头 & 关闭 SocketIO
        clearInterval(streamInterval)
        stream.getTracks().forEach(track => track.stop())
        socket.disconnect()

        // 跳转到首页
        router.push('/home')
      } else {
        console.warn('识别失败:', result.message || '未识别到人脸')
      }
    })

    socket.on('disconnect', () => {
      console.log('SocketIO 断开')
      stopCamera()
    })

    socket.on('connect_error', (error) => {
      console.error('SocketIO 连接失败:', error)
      stopCamera()
    })

  } catch (err) {
    alert('无法访问摄像头：' + err.message)
  }
}

function startImageStream() {
  video.value.onloadedmetadata = () => {
    console.log('视频元数据已加载，开始推送图片流')

    streamInterval = setInterval(() => {
      if (video.value.videoWidth === 0 || video.value.videoHeight === 0) {
        console.error('摄像头未准备好')
        return
      }

      // 如果正在等待结果，跳过
      if (isWaitingForResult) {
        return
      }

      // 发送一帧图片
      const canvas = document.createElement('canvas')
      canvas.width = video.value.videoWidth
      canvas.height = video.value.videoHeight

      const ctx = canvas.getContext('2d')
      ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)

      const base64Image = canvas.toDataURL('image/jpeg')
      console.log(`发送第 ${frameCount + 1} 帧...`)
      socket.emit('face_recognition', { image: base64Image })
      
      frameCount++
      progress.value = Math.round((frameCount / FRAMES_PER_BATCH) * 100)
      progressStatus.value = '识别中...'

      // 如果发送了5帧，开始等待结果
      if (frameCount >= FRAMES_PER_BATCH) {
        console.log('已发送5帧，等待1秒看结果...')
        isWaitingForResult = true
        frameCount = 0
        progress.value = 100
        progressStatus.value = '识别中，请稍候...'
        // 1秒后如果没有结果，继续发送下一批
        setTimeout(() => {
          if (isWaitingForResult) {
            console.log('1秒内无结果，继续发送下一批...')
            isWaitingForResult = false
            progress.value = 0
            progressStatus.value = '识别中...'
          }
        }, WAIT_TIME)
      }
    }, BATCH_INTERVAL) // 每200ms发送一帧
  }
}

function stopCamera() {
  clearInterval(streamInterval)
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
  }
  if (socket) {
    socket.disconnect()
  }
  progress.value = 0
  progressStatus.value = '识别准备中...'
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

.progress-bar {
  width: 100%;
  height: 10px;
  background: #eee;
  border-radius: 5px;
  margin: 16px 0 8px 0;
  overflow: hidden;
}
.progress-inner {
  height: 100%;
  background: #4caf50;
  transition: width 0.2s;
}
.progress-status {
  font-size: 14px;
  color: #888;
  text-align: center;
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
