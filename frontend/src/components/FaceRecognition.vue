<template>
  <div class="face-camera">
    <h2>人脸识别</h2>
    <div class="mode-tabs">
      <button :class="{active: mode==='camera'}" @click="setMode('camera')">摄像头识别</button>
      <button :class="{active: mode==='image'}" @click="setMode('image')">上传图片</button>
      <button :class="{active: mode==='video'}" @click="setMode('video')">上传视频</button>
    </div>

    <!-- 摄像头画面 -->
   <div class="video-container" v-if="mode==='camera' && !recognitionFinished" ref="videoContainer">
  <video ref="video" autoplay playsinline></video>
  <canvas ref="overlayCanvas" class="overlay-canvas"></canvas> <!-- 用于画框 -->
</div>


    <!-- 上传图片 -->
    <div v-if="mode==='image' && !recognitionFinished">
      <input type="file" accept="image/*" @change="onImageUpload" />
      <p class="tip">选择一张本地图片进行识别</p>
    </div>

    <!-- 上传视频 -->
    <div v-if="mode==='video' && !recognitionFinished">
      <input type="file" accept="video/*" @change="onVideoUpload" />
      <p class="tip">选择一个本地视频，系统将自动抽帧识别</p>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar" v-if="!recognitionFinished">
      <div class="progress-inner" :style="{ width: progress + '%' }"></div>
    </div>
    <p class="progress-status" v-if="!recognitionFinished">{{ progressStatus }}</p>

    <!-- 识别前界面 -->
    <div v-if="mode==='camera' && !recognitionFinished">
      <p class="tip">请正对摄像头，系统将自动识别您的人脸</p>
      <button @click="startCamera">开启摄像头识别</button>
      <button style="margin-top: 12px;" @click="() => router.push('/first_page')">返回</button>
    </div>

    <!-- 识别完成界面 -->
    <div v-if="recognitionFinished">
      <p class="tip">识别成功，欢迎：<strong>{{ recognizedName }}</strong></p>
      <button @click="() => router.push('/first_page')">下一步</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { io } from 'socket.io-client'

const recognizedName = ref('')
const recognitionFinished = ref(false)
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
const mode = ref('camera') // 当前模式

//处理异步问题
let requestId = 0
let latestReqId = 0 // 只接受这一轮的结果

//人脸标识框
const overlayCanvas = ref(null)
const videoContainer = ref(null)

function drawFaceBoxes(bboxes) {
  const canvas = overlayCanvas.value
  const videoEl = video.value
  if (!canvas || !videoEl || videoEl.videoWidth === 0 || videoEl.videoHeight === 0) return

  // 设置 canvas 大小与视频匹配
  canvas.width = videoEl.videoWidth
  canvas.height = videoEl.videoHeight

  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.lineWidth = 2
  ctx.strokeStyle = 'red'

  bboxes.forEach(bbox => {
    const scaleX = canvas.width / videoEl.videoWidth
    const scaleY = canvas.height / videoEl.videoHeight

    // 如果 bbox 是原始像素坐标（不缩放），直接绘制
    const x = bbox.left
    const y = bbox.top
    const w = bbox.right - bbox.left
    const h = bbox.bottom - bbox.top

    ctx.strokeRect(x, y, w, h)
  })
}

function setMode(m) {
  stopAll()
  mode.value = m
  progress.value = 0
  progressStatus.value = '识别准备中...'
  recognitionFinished.value = false
  recognizedName.value = ''
}

async function startCamera() {
  stopAll()
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream
    connectSocket()
    video.value.onloadedmetadata = () => {
      startImageStream()
    }
  } catch (err) {
    alert('无法访问摄像头：' + err.message)
  }
}

// 图片识别 - 使用API接口
function onImageUpload(e) {
  stopAll()
  const file = e.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = async function(evt) {
    const base64Image = evt.target.result
    progress.value = 50
    progressStatus.value = '识别中...'

    try {
      const response = await fetch('http://127.0.0.1:8000/api/face/recognize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64Image })
      })

      const result = await response.json()
      progress.value = 100
      progressStatus.value = '识别完成'

      if (result.success && result.faces && result.faces.length > 0) {
        const face = result.faces[0]
        handleRecognitionResult(face)
      } else {
        progressStatus.value = result.message || '识别失败'
      }
    } catch (error) {
      console.error('API识别失败:', error)
      progressStatus.value = '识别失败，请重试'
    }
  }
  reader.readAsDataURL(file)
}

// 视频识别 - 使用Socket.IO
function onVideoUpload(e) {
  stopAll()
  const file = e.target.files[0]
  if (!file) return
  connectSocket()
  const url = URL.createObjectURL(file)
  const videoEl = document.createElement('video')
  videoEl.src = url
  videoEl.muted = true
  videoEl.playsInline = true
  videoEl.crossOrigin = 'anonymous'
  videoEl.currentTime = 0
  videoEl.play()
  videoEl.onloadedmetadata = () => {
    const duration = videoEl.duration
    const canvas = document.createElement('canvas')
    canvas.width = videoEl.videoWidth
    canvas.height = videoEl.videoHeight
    const ctx = canvas.getContext('2d')
    let currentTime = 0
    const interval = 0.2 // 每0.2秒抽一帧
    let totalFrames = Math.floor(duration / interval)
    let sentFrames = 0
    function captureFrame() {
      videoEl.currentTime = currentTime
    }
    videoEl.onseeked = () => {
      ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height)
      const base64Image = canvas.toDataURL('image/jpeg')

      const currentReqId = requestId++
latestReqId = currentReqId // 标记为最新

socket.emit('face_recognition', {
  image: base64Image,
  req_id: currentReqId
})

      sentFrames++
      progress.value = Math.round((sentFrames / totalFrames) * 100)
      progressStatus.value = `视频识别中... (${sentFrames}/${totalFrames})`
      currentTime += interval
      if (currentTime < duration) {
        setTimeout(captureFrame, 100)
      } else {
        progress.value = 100
        progressStatus.value = '视频识别完成，等待结果...'
        URL.revokeObjectURL(url)
      }
    }
    captureFrame()
  }
}

// 统一处理识别结果
function handleRecognitionResult(face) {
  // DeepFake 检测弹窗（优先级最高）
  if(face.name === 'deepfake') {
    alert(`⚠️ 警告：检测到DeepFake人脸！`)
    stopAll()
    return
  }
  if (face.name === '陌生人') {
    alert('告警：检测到陌生人！')
    stopAll()
    router.push('/login')
    return
  }
   if (face.name === '未知人员') {
    alert('人脸数据库中无数据，请前去录入')
    stopAll()
    router.push('/face_register')
    return
  }
  recognizedName.value = face.name || ''
  recognitionFinished.value = true
  stopAll()
}

function sendRecognitionEndSignal() {
  if(socket && socket.connected) {
    socket.emit('face_recognition_end', { msg: 'recognition_finished' })
    console.log('已发送识别结束信号给后端')
  }
}

function connectSocket() {
  if (socket) {
    socket.disconnect()
    socket = null
  }
  socket = io('http://127.0.0.1:8000')
  socket.on('connect', () => {
    progress.value = 0
    progressStatus.value = '识别中...'
  })

 socket.on('face_bbox', (result) => {
  if (typeof result.req_id !== 'undefined' && result.req_id < latestReqId) {
    console.warn(`忽略过期 bbox：req_id=${result.req_id} < ${latestReqId}`)
    return
  }

  if (result.success && result.bboxes && result.bboxes.length > 0) {
    drawFaceBoxes(result.bboxes)
  } else {
    // 没检测到人脸，清空框
    const ctx = overlayCanvas.value?.getContext('2d')
    if (ctx) ctx.clearRect(0, 0, overlayCanvas.value.width, overlayCanvas.value.height)
  }
})

socket.on('face_result', (result) => {
  if (typeof result.req_id !== 'undefined' && result.req_id < latestReqId) {
    console.warn(`忽略过期识别结果：req_id=${result.req_id} < ${latestReqId}`)
    return
  }

  isWaitingForResult = false
  progress.value = 100
  progressStatus.value = '识别完成'
  if (result.success) {
    console.log('🎉 识别成功，处理识别结果')
    const face = result.faces[0]
    handleRecognitionResult(face)
    sendRecognitionEndSignal()
  } else {
    console.warn('识别失败:', result.message || '未识别到人脸')
  }
})

  socket.on('disconnect', () => {
    stopAll()
  })
  socket.on('connect_error', (error) => {
    stopAll()
  })
}

function startImageStream() {
  streamInterval = setInterval(() => {
    if (!video.value || video.value.videoWidth === 0 || video.value.videoHeight === 0) return
    if (isWaitingForResult) return
    const canvas = document.createElement('canvas')
    canvas.width = video.value.videoWidth
    canvas.height = video.value.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)
    const base64Image = canvas.toDataURL('image/jpeg')
    socket.emit('face_recognition', { image: base64Image })
    frameCount++
    progress.value = Math.round((frameCount / FRAMES_PER_BATCH) * 100)
    progressStatus.value = '识别中...'
    if (frameCount >= FRAMES_PER_BATCH) {
      isWaitingForResult = true
      frameCount = 0
      progress.value = 100
      progressStatus.value = '识别中，请稍候...'
      setTimeout(() => {
        if (isWaitingForResult) {
          isWaitingForResult = false
          progress.value = 0
          progressStatus.value = '识别中...'
        }
      }, WAIT_TIME)
    }
  }, BATCH_INTERVAL)
}

function stopAll() {
  clearInterval(streamInterval)
  streamInterval = null
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  if (socket) {
    sendRecognitionEndSignal()  
    socket.disconnect()
    socket = null
  }
  progress.value = 0
  progressStatus.value = '识别准备中...'
  frameCount = 0
  isWaitingForResult = false
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
.mode-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.mode-tabs button {
  padding: 8px 18px;
  border: none;
  border-radius: 6px;
  background: #eee;
  color: #333;
  cursor: pointer;
  font-size: 15px;
  transition: background 0.2s;
}
.mode-tabs button.active {
  background: #d7c480;
  color: #fff;
}
.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.video-container {
  position: relative; /* 让 canvas 相对定位 */
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
