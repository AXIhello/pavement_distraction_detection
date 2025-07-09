<template>
  <div class="detect-container">
    <h2>视频检测页面</h2>

    <!-- 模式选择 -->
    <div class="mode-select">
      <label><input type="radio" value="upload" v-model="mode" /> 上传视频</label>
      <label><input type="radio" value="record" v-model="mode" /> 现场录制</label>
    </div>

    <!-- 本地上传 -->
    <div v-if="mode === 'upload'" class="upload-section">
      <input type="file" accept="video/*" @change="handleVideoChange" v-if="!videoFile" />
      <button @click="removeVideo" v-if="videoFile">卸载视频</button>
    </div>

    <!-- 现场录制 -->
    <div v-if="mode === 'record'" class="record-section">
      <video ref="liveVideo" autoplay playsinline muted v-show="!recordedBlob"></video>
      <video :src="recordedURL" controls v-if="recordedBlob"></video>
      <div class="record-buttons">
        <button @click="startRecording" v-if="!isRecording">开始录制</button>
        <button @click="stopRecording" v-if="isRecording">停止录制</button>
        <button @click="clearRecording" v-if="recordedBlob">清除录制</button>
      </div>
    </div>

    <!-- 视频预览区域 -->
    <div class="video-preview" v-if="videoURL">
      <div class="video-wrapper">
        <video ref="previewRef" :src="videoURL" controls @loadedmetadata="onVideoLoaded" />
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions" v-if="videoURL">
      <button @click="uploadVideo" :disabled="uploading">上传帧图像</button>
      <button @click="analyzeVideo" :disabled="!uploaded || analyzing">分析视频</button>
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
import { ref } from 'vue'

const mode = ref('upload')
const videoFile = ref(null)
const videoURL = ref('')
const uploaded = ref(false)
const uploading = ref(false)
const analyzing = ref(false)
const result = ref(null)
const previewRef = ref(null)

const liveVideo = ref(null)
const isRecording = ref(false)
const mediaRecorder = ref(null)
const recordedBlob = ref(null)
const recordedURL = ref('')
let chunks = []

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
  const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
  liveVideo.value.srcObject = stream
  mediaRecorder.value = new MediaRecorder(stream)
  chunks = []

  mediaRecorder.value.ondataavailable = e => chunks.push(e.data)
  mediaRecorder.value.onstop = () => {
    const blob = new Blob(chunks, { type: 'video/webm' })
    recordedBlob.value = blob
    recordedURL.value = URL.createObjectURL(blob)
    videoURL.value = recordedURL.value
    liveVideo.value.srcObject.getTracks().forEach(track => track.stop())
  }

  mediaRecorder.value.start()
  isRecording.value = true
}

function stopRecording() {
  mediaRecorder.value.stop()
  isRecording.value = false
}

function clearRecording() {
  recordedBlob.value = null
  recordedURL.value = ''
  videoURL.value = ''
  uploaded.value = false
  result.value = null
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

    video.onerror = () => reject('视频加载失败')
  })
}

async function uploadVideo() {
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

    const res = await fetch('http://127.0.0.1:8000/api/upload_frames', {
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

async function analyzeVideo() {
  analyzing.value = true
  result.value = null

  try {
    const res = await fetch('http://127.0.0.1:8000/api/analyze_video')
    const data = await res.json()
    if (data.success) {
      result.value = {
        category: data.category,
        location: data.location,
        count: data.count
      }
    } else {
      alert('分析失败：' + data.message)
    }
  } catch (err) {
    alert('分析错误：' + err.message)
  } finally {
    analyzing.value = false
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
video {
  width: 100%;
  max-height: 360px;
  border-radius: 8px;
  background: #000;
}
.video-preview {
  margin: 20px 0;
  position: relative;
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
}
button:disabled {
  background-color: #aaa;
}
.results {
  background: #f8f8e8;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
</style>
