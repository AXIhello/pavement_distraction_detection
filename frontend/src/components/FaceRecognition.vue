

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

    <!-- 活体检测进度条和提示 -->
    <div v-if="mode==='camera' && !livenessPassed && !recognitionFinished">
      <div class="progress-bar">
        <div class="progress-inner" :style="{ width: livenessProgress + '%' }"></div>
      </div>
      <p class="progress-status">{{ livenessTip }}</p>
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
import { onUnmounted } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { v4 as uuidv4 } from 'uuid'
let sessionId = ''
let frameIndex = 0

onUnmounted(() => { stopAll() })
onBeforeRouteLeave((to, from, next) => {
  stopAll()
  next()
})
const recognizedName = ref('')
const recognitionFinished = ref(false)
const router = useRouter()
const video = ref(null)

const livenessProgress = ref(0)
const livenessTip = ref('请眨眼...')
const livenessPassed = ref(false)

let socket = null
let stream = null
let isWaitingForResult = false // 是否正在等待结果
let lastResults = [] // 存储最近三帧识别结果
const MAX_RESULT_QUEUE = 3
const WAIT_INTERVAL = 500 // 每帧间隔ms

const progressStatus = ref('识别准备中...') // 状态提示
const mode = ref('camera') // 当前模式
const progress = ref(0)

//处理异步问题
let requestId = 0
let latestReqId = 0 // 只接受这一轮的结果

//人脸标识框
const overlayCanvas = ref(null)
const videoContainer = ref(null)

let livenessInterval = null // 活体检测定时器
let alertFrameSent = false;

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
  stopAll();
  alertFrameSent = false;
  mode.value = m;
  progressStatus.value = '识别准备中...';
  recognitionFinished.value = false;
  recognizedName.value = '';
  // 使用时间戳命名，与单张图片检测API保持一致
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() +1).padStart(2,0);
  const day = String(now.getDate()).padStart(2,0);
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  sessionId = `video_${year}${month}${day}_${hours}${minutes}${seconds}`;
  frameIndex = 0;
}

async function startCamera() {
  stopAll();
  alertFrameSent = false;
  // 确保 sessionId 有值
  if (!sessionId) {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() +1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    sessionId = `video_${year}${month}${day}_${hours}${minutes}${seconds}`;
    frameIndex = 0;
    console.log('[DEBUG] startCamera, sessionId=', sessionId);
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream
    connectSocket()
    video.value.onloadedmetadata = () => {
      startLivenessDetection()
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
    progressStatus.value = '识别中...'

    try {
      const response = await fetch('http://127.0.0.1:8000/api/face/recognize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64Image })
      })

      const result = await response.json()
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
  stopAll();
  const file = e.target.files[0];
  if (!file) return;
  connectSocket();
  // 使用时间戳命名，与单张图片检测API保持一致
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() +1).padStart(2,0);
  const day = String(now.getDate()).padStart(2, 0);
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  sessionId = `video_${year}${month}${day}_${hours}${minutes}${seconds}`;
  frameIndex = 0;
  const url = URL.createObjectURL(file);
  const videoEl = document.createElement('video');
  videoEl.src = url;
  videoEl.muted = true;
  videoEl.playsInline = true;
  videoEl.crossOrigin = 'anonymous';
  videoEl.currentTime = 0;
  videoEl.play();
  videoEl.onloadedmetadata = () => {
    const duration = videoEl.duration;
    const canvas = document.createElement('canvas');
    canvas.width = videoEl.videoWidth;
    canvas.height = videoEl.videoHeight;
    const ctx = canvas.getContext('2d');
    let currentTime = 0;
    const interval = 0.2; // 每0.2秒抽一帧
    let sentFrames = 0;
    function captureFrame() {
      videoEl.currentTime = currentTime;
    }
    videoEl.onseeked = () => {
      ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
      const base64Image = canvas.toDataURL('image/jpeg');
      uploadFrame(base64Image); // 每帧都保存
      const currentReqId = requestId++;
      latestReqId = currentReqId;
      socket.emit('face_recognition', {
        image: base64Image,
        req_id: currentReqId
      });
      sentFrames++;
      progressStatus.value = `视频识别中... (${sentFrames})`;
      currentTime += interval;
      if (currentTime < duration && !recognitionFinished.value) {
        setTimeout(captureFrame, 100);
      } else {
        progressStatus.value = '视频识别完成，等待结果...';
        URL.revokeObjectURL(url);
      }
    };
    captureFrame();
  };
}


async function uploadFrame(base64Image) {
  try {
    console.log(`[DEBUG] 上传帧: session_id=${sessionId}, frame_index=${frameIndex}`)
    const response = await fetch('http://127.0.0.1:8000/api/face/save_frame', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        image: base64Image,
        frame_index: frameIndex++
      })
    })
    const result = await response.json()
    console.log(`[DEBUG] 帧上传响应:`, result)
    if (!result.success) {
      console.error(`[ERROR] 帧上传失败:`, result.message)
    }
  } catch (e) {
    console.error('[ERROR] 上传帧失败', e)
  }
}

// 统一处理识别结果
async function handleRecognitionResult(face) {
  console.log(`[DEBUG] 处理识别结果: mode=${mode.value}, face.name=${face.name}, alertFrameSent=${alertFrameSent}`)
  if ((face.name === 'deepfake' || face.name === '陌生人') && !alertFrameSent) {
    alertFrameSent = true;
    console.log(`[DEBUG] 检测到告警: ${face.name}`)
    // 先截图，确保 video.value 可用
    let base64Image = ''
    if (video.value && video.value.videoWidth && video.value.videoHeight) {
      const canvas = document.createElement('canvas')
      canvas.width = video.value.videoWidth
      canvas.height = video.value.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)
      base64Image = canvas.toDataURL('image/jpeg')
      console.log(`[DEBUG] 成功截图，图片大小: ${base64Image.length}`)
      // 发送到后端
      // sendFaceAlertFrame(base64Image, face.name, face.distance || 0) // 已废弃
    } else {
      console.warn('无法获取摄像头画面，未能保存告警帧')
    }
    // 新增：最终判定
    if (mode.value === 'camera' || mode.value === 'video') {
      console.log(`[DEBUG] 准备发送最终判定: ${face.name === 'deepfake' ? 'deepfake' : 'stranger'}`)
      await sendFinalJudgement(face.name === 'deepfake' ? 'deepfake' : 'stranger', face.distance || 1.0)
    }
    // 再 stopAll 和跳转
    if(face.name === 'deepfake') {
      alert(`⚠️ 警告：检测到DeepFake人脸！`)
      stopAll()
      router.push('/login')
      return
    }
    if (face.name === '陌生人') {
      alert('告警：检测到陌生人！')
      stopAll()
      router.push('/face_register')
      return
    }
  } else if (!alertFrameSent) {
    if (mode.value === 'camera' || mode.value === 'video') {
      console.log(`[DEBUG] 正常情况，发送最终判定: normal`)
      await sendFinalJudgement('normal')
    }
    recognizedName.value = face.name || ''
    recognitionFinished.value = true
    stopAll()
  }
  //  if (face.name === '未知人员') {
  //   alert('人脸数据库中无数据，请前去录入')
  //   stopAll()
  //   router.push('/face_register')
  //   return
  // }
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

// 新增：处理识别结果（视频和摄像头模式通用）
socket.on('face_result', (result) => {
  processRecognitionResult(result);
  // 继续采集下一帧（摄像头模式自动采集，视频模式由 onVideoUpload 控制）
  if (!recognitionFinished.value && mode.value === 'camera') {
    setTimeout(() => startImageStream(), WAIT_INTERVAL);
  }
});

// 关键：liveness_result 监听注册到这里
  socket.on('liveness_result', (result) => {
    if (result.success) {
      livenessProgress.value = result.progress
      livenessTip.value = result.next_action
      if (result.progress === 100) {
        livenessPassed.value = true
        if (livenessInterval) clearInterval(livenessInterval)
        startImageStream()
      }
    } else {
      livenessTip.value = result.message
    }
  })

  socket.on('disconnect', () => {
    stopAll()
  })
  socket.on('connect_error', (error) => {
    stopAll()
  })
}

// 新的单帧节流采集逻辑
function startImageStream() {
  if (isWaitingForResult || recognitionFinished.value) return
  if (!video.value || video.value.videoWidth === 0 || video.value.videoHeight === 0) return
  const canvas = document.createElement('canvas')
  canvas.width = video.value.videoWidth
  canvas.height = video.value.videoHeight
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)
  const base64Image = canvas.toDataURL('image/jpeg')
  isWaitingForResult = true
  progressStatus.value = '识别中...'
  // 新增：每帧都上传
  uploadFrame(base64Image)
  socket.emit('face_recognition', { image: base64Image })
}

function stopAll() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  if (socket) {
    sendRecognitionEndSignal()
    socket.disconnect()
    socket = null
  }
  if (livenessInterval) clearInterval(livenessInterval)
  isWaitingForResult = false
  lastResults = []
  progress.value = 0
  progressStatus.value = '识别准备中...'
  alertFrameSent = false;
}
function startLivenessDetection() {
  livenessPassed.value = false
  livenessProgress.value = 0
  livenessTip.value = '请眨眼...'
  if (livenessInterval) clearInterval(livenessInterval)
  livenessInterval = setInterval(() => {
    sendLivenessFrame()
  }, 100) // 每100ms发一帧
}

function sendLivenessFrame() {
  if (!video.value || video.value.videoWidth === 0 || video.value.videoHeight === 0 || livenessPassed.value) return
  const canvas = document.createElement('canvas')
  canvas.width = video.value.videoWidth
  canvas.height = video.value.videoHeight
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video.value, 0, 0, canvas.width, canvas.height)
  const base64Image = canvas.toDataURL('image/jpeg')
  socket.emit('liveness_detection', { image: base64Image })
}

async function sendFinalJudgement(resultType, confidence = 1.0) {
  try {
    console.log(`[DEBUG] 发送最终判定: session_id=${sessionId}, resultType=${resultType}, confidence=${confidence}`)
    const response = await fetch('http://127.0.0.1:8000/api/face/alert_judgement', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        result: resultType, // 'normal' | 'deepfake' | 'stranger'
        confidence
      })
    })
    const result = await response.json()
    console.log(`[DEBUG] 最终判定响应:`, result)
    if (!result.success) {
      console.error(`[ERROR] 最终判定失败:`, result.message)
    }
  } catch (e) {
    console.error('[ERROR] 上传判定结果失败', e)
  }
}

// 新增：统一三帧一致判定逻辑
function processRecognitionResult(result) {
  if (recognitionFinished.value || alertFrameSent) return;
  isWaitingForResult = false;
  const name = result.faces && result.faces[0] ? result.faces[0].name : '未检测到人脸';
  lastResults.push(name);
  if (lastResults.length > MAX_RESULT_QUEUE) lastResults.shift();

  if (lastResults.length === 1) {
    progress.value = 33;
  } else if (lastResults.length === 2) {
    if (lastResults[0] === lastResults[1] && lastResults[0] !== '未检测到人脸') {
      progress.value = 66;
    } else {
      progress.value = 0;
      lastResults = [lastResults[1]];
    }
  } else if (lastResults.length === 3) {
    if (lastResults[0] === lastResults[1] && lastResults[1] === lastResults[2] && lastResults[0] !== '未检测到人脸') {
      progress.value = 100;
      // 只在最终三帧一致时调用handleRecognitionResult
      handleRecognitionResult(result.faces[0]);
      recognitionFinished.value = true;
      stopAll();
      return;
    } else {
      progress.value = 0;
      lastResults = [lastResults[2]];
    }
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


