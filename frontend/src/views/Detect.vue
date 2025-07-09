<template>
  <Header2 ref="headerRef" />
  <div class="detect-container" :style="{ paddingTop: headerHeight + 'px' }">
    <h2>上传并分析路障</h2>

    <!-- 模式选择 -->
    <div class="mode-select">
      <label><input type="radio" value="upload" v-model="mode" /> 上传视频</label>
      <label><input type="radio" value="record" v-model="mode" /> 现场录制</label>
    </div>

    <!-- 上传或录制视频预览 -->
    <div class="video-preview">
      <!-- 上传视频 -->
      <video v-if="mode === 'upload' && videoURL" :src="videoURL" controls autoplay muted playsinline @loadedmetadata="onVideoLoaded"></video>

      <!-- 录制视频 -->
      <video v-if="mode === 'record'" ref="liveVideo" controls playsinline></video>

      <!-- 空视频 -->
      <video v-if="(mode === 'upload' && !videoURL) || (mode === 'record' && !recordedBlob)" class="empty-video" muted playsinline></video>
    </div>

    <!-- 上传视频操作 -->
    <div v-if="mode === 'upload'" class="upload-section">
      <input type="file" accept="video/*" @change="handleVideoChange" v-if="!videoFile" />
      <button @click="removeVideo" v-if="videoFile">卸载视频</button>
    </div>

    <!-- 录制视频操作 -->
    <div v-if="mode === 'record'" class="record-section">
      <div class="record-buttons">
        <button @click="startRecording" v-if="!isRecording">开始录制</button>
        <button @click="stopRecording" v-if="isRecording">停止录制</button>
        <button @click="clearRecording" v-if="recordedBlob">清除录制</button>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions" v-if="videoURL || recordedBlob">
      <button @click="analyze_video" :disabled="uploading">上传帧图像</button>
    </div>

    <!-- 状态 -->
    <div class="status">
      <p v-if="uploading">正在上传帧图像...</p>
      <p v-if="analyzing">分析中...</p>
    </div>

    <!-- 结果 -->
    <div class="results" v-if="result">
      <h3>分析结果：</h3>
      <ul>
        <li><strong>类别：</strong>{{ result.category }}</li>
        <li><strong>位置：</strong>{{ result.location }}</li>
        <li><strong>数量：</strong>{{ result.count }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Header2 from '@/components/Navigation.vue'

const mode = ref('upload')
const videoFile = ref(null)
const videoURL = ref('')
const uploaded = ref(false)
const uploading = ref(false)
const analyzing = ref(false)
const result = ref(null)

const liveVideo = ref(null)
const isRecording = ref(false)
const mediaRecorder = ref(null)
const recordedBlob = ref(null)
const recordedURL = ref('')
let chunks = []

const headerRef = ref(null)
const headerHeight = ref(0)

function updateHeaderHeight() {
  nextTick(() => {
    if (headerRef.value?.$el) {
      headerHeight.value = headerRef.value.$el.offsetHeight
    } else if (headerRef.value instanceof HTMLElement) {
      headerHeight.value = headerRef.value.offsetHeight
    }
  })
}

onMounted(() => {
  updateHeaderHeight()
  window.addEventListener('resize', updateHeaderHeight)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateHeaderHeight)
})

function handleVideoChange(e) {
  const file = e.target.files[0]
  if (file) {
    videoFile.value = file
    videoURL.value = URL.createObjectURL(file)
    uploaded.value = false
    result.value = null
  }
}

function removeVideo() {
  videoFile.value = null
  videoURL.value = ''
  uploaded.value = false
  result.value = null
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    liveVideo.value.srcObject = stream // 将媒体流传递给 video 元素
    mediaRecorder.value = new MediaRecorder(stream)
    chunks = [] // 清空之前的录制数据

    // 每当有可用数据时，保存音视频数据到 chunks 数组
    mediaRecorder.value.ondataavailable = e => {
      if (e.data.size > 0) {
        chunks.push(e.data) // 保存数据
      }
    }

    // 在录制停止时，生成完整的视频 Blob
    mediaRecorder.value.onstop = () => {
      const blob = new Blob(chunks, { type: 'video/webm' })
      recordedBlob.value = blob
      recordedURL.value = URL.createObjectURL(blob) // 生成视频 URL
      videoURL.value = recordedURL.value
      liveVideo.value.srcObject.getTracks().forEach(track => track.stop()) // 停止所有媒体轨道
    }

    mediaRecorder.value.start() // 开始录制
    isRecording.value = true
    console.log('录制已开始')
  } catch (err) {
    console.error('录制失败:', err)
    alert('录制失败，请检查摄像头权限或设备设置')
  }
}

function stopRecording() {
  if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    mediaRecorder.value.stop() // 停止录制
    isRecording.value = false
    console.log('录制已停止')
  }
}

function clearRecording() {
  recordedBlob.value = null
  recordedURL.value = ''
  videoURL.value = ''
  uploaded.value = false
  result.value = null
  isRecording.value = false
  chunks = [] // 清空录制数据
}

function onVideoLoaded() {}

async function extractFrames() {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.src = videoURL.value
    video.crossOrigin = 'anonymous'
    video.preload = 'auto'
    video.muted = true
    video.playsInline = true

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const frames = []

    video.addEventListener('loadedmetadata', () => {
      const duration = video.duration
      const fps = 5
      const totalFrames = Math.floor(duration * fps)
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      let currentFrame = 0

      async function seekAndCapture() {
        if (currentFrame >= totalFrames) {
          resolve(frames)
          return
        }

        const time = currentFrame / fps
        video.currentTime = time

        video.addEventListener(
          'seeked',
          async function handler() {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
            canvas.toBlob(blob => {
              if (blob) frames.push(blob)
              currentFrame++
              seekAndCapture()
            }, 'image/jpeg')
            video.removeEventListener('seeked', handler)
          },
          { once: true }
        )
      }

      seekAndCapture()
    })

    video.onerror = () => reject(new Error('视频加载失败'))
  })
}

async function analyze_video() {
  if (!videoURL.value) return alert('请先上传或录制视频')

  uploading.value = true
  uploaded.value = false
  result.value = null

  try {
    const frames = await extractFrames()
    const formData = new FormData()

    frames.forEach((blob, index) => {
      formData.append(`frame_${index}`, blob, `frame_${index}.jpg`)
    })

    const res = await fetch('http://127.0.0.1:8000/api/analyze_video', {
      method: 'POST',
      body: formData
    })

    const data = await res.json()
    uploaded.value = data.success
    if (!data.success) alert('上传失败：' + data.message)
  } catch (err) {
    alert('上传出错：' + err.message)
  } finally {
    uploading.value = false
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

h2 {
  margin-bottom: 16px;
  font-weight: 600;
  color: #222;
}

.mode-select {
  margin-bottom: 12px;
  font-size: 14px;
}

.upload-section,
.record-section {
  margin-bottom: 20px;
}

.record-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.video-preview {
  margin: 20px 0;
  position: relative;
  width: 100%;
  max-width: 960px;
  height: 360px;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-preview video,
.video-preview .empty-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
  border-radius: 8px;
  display: block;
}

.actions {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

button {
  padding: 8px 16px;
  background-color: #333;
  color: #fefefe;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #555;
}

.results {
  background: #f8f8e8;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
</style>
