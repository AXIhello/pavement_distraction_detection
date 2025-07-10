<template>
  <Header2 ref="headerRef" />
  <div class="detect-container" :style="{ paddingTop: headerHeight + 'px' }">
    <h2>上传并分析路障</h2>

    <!-- 上传视频 -->
    <div class="upload-section">
      <input type="file" accept="video/*" @change="handleVideoChange" v-if="!videoFile" />
      <button @click="removeVideo" v-if="videoFile">卸载视频</button>
    </div>

    <!-- 视频预览 -->
    <div class="video-preview" v-if="videoURL">
      <video :src="videoURL" controls muted playsinline ref="videoEl"></video>
    </div>

    <!-- 操作按钮 -->
    <div class="actions" v-if="videoFile && !processing">
      <button @click="startAnalysis" :disabled="processing">开始分析</button>
    </div>

    <!-- 状态提示 -->
    <div class="status">
      <p v-if="processing">正在处理中... <span v-if="totalFrames > 0">({{ processedFrames }}/{{ totalFrames }})</span></p>
      <p v-if="extractionComplete">帧提取完成，等待服务器处理结果...</p>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar" v-if="processing && totalFrames > 0">
      <div class="progress-fill" :style="{ width: (processedFrames / totalFrames) * 100 + '%' }"></div>
    </div>

    <!-- 分析完成提示 -->
    <div v-if="showCompleteNotice" class="popup-notice">分析完毕</div>

    <!-- 分析结果 -->
    <h3 v-if="frameResults.length" class="result-title">分析结果</h3>


    <!-- 图像轮播与检测详情 -->
    <div class="image-slider" v-if="frameResults.length">
      <div class="image-controls">
        <button @click="prevImage" :disabled="frameResults.length <= 1">上一张</button>
        <span>{{ currentImageIndex + 1 }} / {{ frameResults.length }}</span>
        <button @click="nextImage" :disabled="frameResults.length <= 1">下一张</button>
        <button @click="toggleAutoPlay">{{ autoPlay ? '停止自动播放' : '自动播放' }}</button>
      </div>

      <div class="image-result">
  <div class="image-column">
    <img :src="frameResults[currentImageIndex].image" class="annotated-frame" />
  </div>
  <div class="info-column detection-info">
    <h4>检测结果：</h4>
    <ul v-if="frameResults[currentImageIndex].detections.length">
      <li v-for="(det, i) in frameResults[currentImageIndex].detections" :key="i">
        类别：<strong>{{ det.class }}</strong><br />
        置信度：{{ (det.confidence * 100).toFixed(1) }}%<br />
        坐标：[{{ det.bbox.join(', ') }}]
      </li>
    </ul>
    <p v-else>无检测结果</p>
  </div>
</div>

    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { io } from 'socket.io-client'
import Header2 from '@/components/Navigation.vue'

const headerRef = ref(null)
const headerHeight = ref(0)

const videoFile = ref(null)
const videoURL = ref('')
const videoEl = ref(null)

const processing = ref(false)
const extractionComplete = ref(false)
const totalFrames = ref(0)
const processedFrames = ref(0)
const autoPlay = ref(false)
const currentImageIndex = ref(0)
const autoPlayTimer = ref(null)
const showCompleteNotice = ref(false)

const frameResults = ref([]) // [{ image, detections }]
const allDetections = ref([])
const uniqueDetectionClasses = ref([])

let socket = null

function updateHeaderHeight() {
  nextTick(() => {
    if (headerRef.value?.$el) {
      headerHeight.value = headerRef.value.$el.offsetHeight
    }
  })
}

onMounted(() => {
  updateHeaderHeight()
  window.addEventListener('resize', updateHeaderHeight)
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateHeaderHeight)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  stopAnalysis()
})

function handleVideoChange(e) {
  const file = e.target.files[0]
  if (file) {
    videoFile.value = file
    videoURL.value = URL.createObjectURL(file)
    resetState()
  }
}

function removeVideo() {
  videoFile.value = null
  videoURL.value = ''
  resetState()
  stopAnalysis()
}

function resetState() {
  frameResults.value = []
  currentImageIndex.value = 0
  totalFrames.value = 0
  processedFrames.value = 0
  extractionComplete.value = false
  processing.value = false
  autoPlay.value = false
  allDetections.value = []
  uniqueDetectionClasses.value = []
}

function startAnalysis() {
  if (!videoURL.value) return alert('请先上传视频')

  processing.value = true
  extractionComplete.value = false
  frameResults.value = []
  processedFrames.value = 0
  currentImageIndex.value = 0

  socket = io('http://127.0.0.1:8000')

  socket.on('connect', () => {
    extractFramesOffline()
  })

  socket.on('frame_result', (result) => {
    if (result?.annotated_image) {
      frameResults.value.push({
        image: `data:image/jpeg;base64,${result.annotated_image}`,
        detections: result.detections || []
      })
    }

    if (result?.detections) {
      allDetections.value.push(...result.detections)
    }
  })

  socket.on('stream_complete', () => {
    processing.value = false
    extractionComplete.value = false

    const seen = new Set()
    uniqueDetectionClasses.value = allDetections.value
      .map(d => d.class)
      .filter(cls => {
        if (!seen.has(cls)) {
          seen.add(cls)
          return true
        }
        return false
      })

    showCompleteNotice.value = true
    setTimeout(() => {
      showCompleteNotice.value = false
    }, 1000)
  })

  socket.on('disconnect', stopAnalysis)
  socket.on('connect_error', stopAnalysis)
}

function extractFramesOffline() {
  const video = document.createElement('video')
  video.src = videoURL.value
  video.muted = true
  video.style.display = 'none'
  document.body.appendChild(video)

  video.addEventListener('loadedmetadata', () => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const frameInterval = 0.2
    const duration = video.duration
    totalFrames.value = Math.floor(duration / frameInterval)

    let currentTime = 0

    const extractFrame = () => {
      if (currentTime >= duration) {
        extractionComplete.value = true
        socket.emit('video_stream_end', { message: '视频帧发送完成' })
        document.body.removeChild(video)
        return
      }

      video.currentTime = currentTime
      video.addEventListener(
        'seeked',
        () => {
          video.addEventListener(
            'canplay',
            () => {
              ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
              const base64 = canvas.toDataURL('image/jpeg', 1.0)
              socket.emit('video_frame', { image: base64 })

              processedFrames.value++
              currentTime += frameInterval
              setTimeout(extractFrame, 50)
            },
            { once: true }
          )
        },
        { once: true }
      )
    }

    extractFrame()
  })

  video.addEventListener('error', (e) => {
    alert('视频加载失败，请检查视频格式')
    stopAnalysis()
    document.body.contains(video) && document.body.removeChild(video)
  })
}

function stopAnalysis() {
  processing.value = false
  extractionComplete.value = false
  autoPlayTimer.value && clearInterval(autoPlayTimer.value)
  autoPlayTimer.value = null
  socket?.disconnect()
  socket = null
}

function prevImage() {
  if (frameResults.value.length > 0) {
    currentImageIndex.value =
      currentImageIndex.value > 0
        ? currentImageIndex.value - 1
        : frameResults.value.length - 1
  }
}

function nextImage() {
  if (frameResults.value.length > 0) {
    currentImageIndex.value =
      (currentImageIndex.value + 1) % frameResults.value.length
  }
}

function toggleAutoPlay() {
  autoPlay.value = !autoPlay.value

  if (autoPlay.value) {
    autoPlayTimer.value = setInterval(() => {
      frameResults.value.length > 0 && nextImage()
    }, 1000)
  } else {
    clearInterval(autoPlayTimer.value)
    autoPlayTimer.value = null
  }
}

const router = useRouter()
function hasUnsavedChanges() {
  return videoFile.value && processing.value
}
function handleBeforeUnload(e) {
  if (hasUnsavedChanges()) {
    e.preventDefault()
    e.returnValue = ''
  }
}
onBeforeRouteLeave((to, from, next) => {
  hasUnsavedChanges() ? (window.confirm('未完成分析将丢失，确定离开？') ? next() : next(false)) : next()
})
</script>
<style scoped>
.detect-container {
  max-width: 960px;
  margin: auto;
  padding: 20px;
  font-family: sans-serif;
  background: #fefef9;
  border-radius: 12px;
}

.video-preview video {
  width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 8px;
}

.actions {
  margin-top: 20px;
}

.actions button {
  padding: 10px 20px;
  background: #000000;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.actions button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.status {
  margin-top: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 5px;
  text-align: center;
}

.progress-bar {
  margin-top: 10px;
  width: 100%;
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #0056b3);
  transition: width 0.3s ease;
}

.result-title {
  margin-top: 20px;
  font-size: 22px;
  color: #333;
  text-align: center;
}

/* .detection-summary {
  margin-top: 16px;
  font-weight: bold;
  text-align: center;
} */

.image-slider {
  margin-top: 20px;
}

.image-controls {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-bottom: 10px;
}

.image-controls button {
  padding: 5px 10px;
  background: #cfa97e;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.image-controls button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.annotated-frame {
  width: 100%;
  max-height: 360px;
  object-fit: contain;
  border-radius: 8px;
  border: 2px solid #007bff;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.detection-info {
  margin-top: 12px;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fefdf9;
  max-width: 720px;
  font-size: 14px;
  line-height: 1.6;
}

.detection-info ul {
  list-style: none;
  padding-left: 0;
}

.detection-info li {
  background: #f3f3f3;
  margin-bottom: 8px;
  padding: 8px;
  border-radius: 4px;
  font-family: monospace;
}

.popup-notice {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background-color: #f5e9d7;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  font-size: 18px;
  opacity: 1;
  animation: fadeOut 2s forwards;
  z-index: 999;
}
.image-result {
  display: flex;
  flex-direction: row;
  gap: 20px;
  align-items: flex-start;
  margin-top: 16px;
  flex-wrap: wrap; /* 让它在小屏幕也能垂直展示 */
}
.image-column {
  flex: 0 0 50%;
  max-width: 50%;
}

.info-column {
  flex: 1;
  max-width: 50%;
}



@keyframes fadeOut {
  0% {
    opacity: 1;
  }
  80% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}
</style>
