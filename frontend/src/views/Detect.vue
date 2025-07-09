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
    <div class="video-preview">
      <video 
        v-if="videoURL" 
        :src="videoURL" 
        controls 
        autoplay 
        muted 
        playsinline 
        ref="videoEl"
        @ended="handleVideoEnded"
      ></video>
      <video v-else class="empty-video" muted playsinline></video>
    </div>

    <!-- 操作按钮 -->
    <div class="actions" v-if="videoURL">
      <button @click="startStreaming" :disabled="uploading">开始分析</button>
    </div>

    <!-- 状态提示 -->
    <div class="status">
      <p v-if="uploading">分析中...</p>
    </div>

    <!-- 分析结果图像 -->
    <div class="image-slider" v-if="annotatedImages.length">
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
const uploading = ref(false)
const annotatedImages = ref([])
const currentImageIndex = ref(0)
const videoEl = ref(null)

let socket = null
let frameInterval = null
let displayTimer = null

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
  stopStreaming()
})

function handleVideoChange(e) {
  const file = e.target.files[0]
  if (file) {
    videoFile.value = file
    videoURL.value = URL.createObjectURL(file)
    annotatedImages.value = []
    currentImageIndex.value = 0
  }
}

function removeVideo() {
  videoFile.value = null
  videoURL.value = ''
  annotatedImages.value = []
  currentImageIndex.value = 0
  stopStreaming()
}

function startStreaming() {
  if (!videoURL.value) return alert('请先上传视频')
  uploading.value = true
  annotatedImages.value = []
  currentImageIndex.value = 0

  socket = io('http://127.0.0.1:8000')

  socket.on('connect', () => {
    console.log('已连接 socket')
    streamFrames()
  })

  socket.on('frame_result', (result) => {
    if (result?.annotated_image) {
      annotatedImages.value.push(`data:image/jpeg;base64,${result.annotated_image}`)
    }
  })

  socket.on('disconnect', () => {
    console.log('socket 断开')
    stopStreaming()
  })

  socket.on('connect_error', (err) => {
    console.error('socket 连接失败:', err)
    stopStreaming()
  })
}

function streamFrames() {
  const video = videoEl.value
  if (!video) return

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  if (frameInterval) clearInterval(frameInterval)
  frameInterval = setInterval(() => {
    if (video.paused || video.ended) return
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const base64 = canvas.toDataURL('image/jpeg')
    socket.emit('video_frame', { image: base64 })
  }, 200)

  startDisplayLoop()
}

// 视频播放完毕，发送结束消息给后端
function handleVideoEnded() {
  console.log('视频播放结束，发送结束消息给后端')
  if (socket && socket.connected) {
    socket.emit('video_stream_end', { message: '视频帧发送完成' })
  }
  stopStreaming()
}

function startDisplayLoop() {
  if (displayTimer) clearInterval(displayTimer)
  currentImageIndex.value = 0
  displayTimer = setInterval(() => {
    if (annotatedImages.value.length > 0) {
      currentImageIndex.value = (currentImageIndex.value + 1) % annotatedImages.value.length
    }
  }, 1000)
}

function stopStreaming() {
  uploading.value = false
  if (frameInterval) {
    clearInterval(frameInterval)
    frameInterval = null
  }
  if (displayTimer) {
    clearInterval(displayTimer)
    displayTimer = null
  }
  if (socket) {
    socket.disconnect()
    socket = null
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
</style>
