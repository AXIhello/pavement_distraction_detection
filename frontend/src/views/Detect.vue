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
      <video
        :src="videoURL"
        controls
        muted
        playsinline
        ref="videoEl"
      ></video>
    </div>

    <!-- 操作按钮 -->
    <div class="actions" v-if="videoFile && !processing">
      <button @click="startAnalysis" :disabled="processing">开始分析</button>
    </div>

    <!-- 状态提示 -->
    <div class="status">
      <p v-if="processing">
        正在处理中... 
        <span v-if="totalFrames > 0">
          ({{ processedFrames }}/{{ totalFrames }})
        </span>
      </p>
      <p v-if="extractionComplete">帧提取完成，等待服务器处理结果...</p>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar" v-if="processing && totalFrames > 0">
      <div class="progress-fill" :style="{ width: (processedFrames / totalFrames) * 100 + '%' }"></div>
    </div>

    <!-- 分析结果图像 -->
    <div class="image-slider" v-if="annotatedImages.length">
      <div class="image-controls">
        <button @click="prevImage" :disabled="annotatedImages.length <= 1">上一张</button>
        <span>{{ currentImageIndex + 1 }} / {{ annotatedImages.length }}</span>
        <button @click="nextImage" :disabled="annotatedImages.length <= 1">下一张</button>
        <button @click="toggleAutoPlay">{{ autoPlay ? '停止自动播放' : '自动播放' }}</button>
      </div>
      <img :src="annotatedImages[currentImageIndex]" class="annotated-frame" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { io } from 'socket.io-client'
import Header2 from '@/components/Navigation.vue'

const headerRef = ref(null)
const headerHeight = ref(0)
const videoFile = ref(null)
const videoURL = ref('')
const processing = ref(false)
const extractionComplete = ref(false)
const annotatedImages = ref([])
const currentImageIndex = ref(0)
const videoEl = ref(null)
const totalFrames = ref(0)
const processedFrames = ref(0)
const autoPlay = ref(false)

let socket = null
let autoPlayTimer = null

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
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateHeaderHeight)
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
  annotatedImages.value = []
  currentImageIndex.value = 0
  totalFrames.value = 0
  processedFrames.value = 0
  extractionComplete.value = false
  processing.value = false
  autoPlay.value = false
}

function startAnalysis() {
  if (!videoURL.value) return alert('请先上传视频')
  
  processing.value = true
  extractionComplete.value = false
  annotatedImages.value = []
  currentImageIndex.value = 0
  processedFrames.value = 0

  // 连接WebSocket
  socket = io('http://127.0.0.1:8000')

  socket.on('connect', () => {
    console.log('已连接 socket')
    extractFramesOffline()
  })

  socket.on('frame_result', (result) => {
    if (result?.annotated_image) {
      annotatedImages.value.push(`data:image/jpeg;base64,${result.annotated_image}`)
    }
  })

  socket.on('analysis_complete', () => {
    console.log('分析完成')
    processing.value = false
    extractionComplete.value = false
  })

  socket.on('disconnect', () => {
    console.log('socket 断开')
    stopAnalysis()
  })

  socket.on('connect_error', (err) => {
    console.error('socket 连接失败:', err)
    stopAnalysis()
  })
}

function extractFramesOffline() {
  // 创建一个隐藏的video元素用于离线处理
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

    const frameInterval = 0.2 // 每0.2秒提取一帧
    const duration = video.duration
    totalFrames.value = Math.floor(duration / frameInterval)
    
    let currentTime = 0
    let frameIndex = 0

    const extractFrame = () => {
      if (currentTime >= duration) {
        // 所有帧处理完毕
        extractionComplete.value = true
        socket.emit('video_stream_end', { message: '视频帧发送完成' })
        document.body.removeChild(video)
        return
      }

      video.currentTime = currentTime

      const onSeeked = () => {
        video.removeEventListener('seeked', onSeeked)
        
        // 等待视频帧完全加载
        video.addEventListener('canplay', () => {
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
          const base64 = canvas.toDataURL('image/jpeg', 0.8) // 添加压缩质量
          
          socket.emit('video_frame', { image: base64 })
          
          processedFrames.value++
          frameIndex++
          currentTime += frameInterval
          
          // 添加小延迟避免处理过快
          setTimeout(extractFrame, 50)
        }, { once: true })
      }

      video.addEventListener('seeked', onSeeked)
    }

    extractFrame()
  })

  video.addEventListener('error', (e) => {
    console.error('视频加载失败:', e)
    alert('视频加载失败，请检查视频格式')
    stopAnalysis()
    if (document.body.contains(video)) {
      document.body.removeChild(video)
    }
  })
}

function stopAnalysis() {
  processing.value = false
  extractionComplete.value = false
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
  if (socket) {
    socket.disconnect()
    socket = null
  }
}

// 图像控制函数
function prevImage() {
  if (annotatedImages.value.length > 0) {
    currentImageIndex.value = currentImageIndex.value > 0 
      ? currentImageIndex.value - 1 
      : annotatedImages.value.length - 1
  }
}

function nextImage() {
  if (annotatedImages.value.length > 0) {
    currentImageIndex.value = (currentImageIndex.value + 1) % annotatedImages.value.length
  }
}

function toggleAutoPlay() {
  autoPlay.value = !autoPlay.value
  
  if (autoPlay.value) {
    autoPlayTimer = setInterval(() => {
      nextImage()
    }, 1000)
  } else {
    if (autoPlayTimer) {
      clearInterval(autoPlayTimer)
      autoPlayTimer = null
    }
  }
}
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

.video-preview video,
.video-preview .empty-video,
.image-slider img {
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
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
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

.image-slider {
  margin-top: 20px;
}

.image-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.image-controls button {
  padding: 5px 10px;
  background: #28a745;
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
  border: 2px solid #007bff;
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>