<template>
  <div class="video-recorder-container">
    <div class="recorder-section">

      <!-- 只有在 mediaStream 存在或者有录制视频时显示视频框 -->
      <div v-if="mediaStream || recordedBlob" class="camera-preview">
        <video
          ref="videoPlayer"
          :src="recordedBlob ? recordedURL : ''"
          :srcObject="mediaStream && !recordedBlob ? mediaStream : null"
          :autoplay="mediaStream && !recordedBlob"   
          muted
          playsinline
          controls
          class="preview-video"
          @loadedmetadata="onVideoLoaded"
        />
      </div>

      <!-- 未启动摄像头且无录制视频时，显示启动按钮和提示 -->
      <div v-else class="no-camera">
        <div class="no-camera-icon">📹</div>
        <p>点击开始录制按钮启动摄像头</p>
        <button @click="startCamera" class="start-camera-btn">📹 启动摄像头</button>
      </div>

      <div class="recorder-controls">
        <div v-if="mediaStream && !recordedBlob" class="recording-controls">
          <button v-if="!recording" @click="startRecording" class="record-btn">🔴 开始录制</button>
          <button v-if="recording" @click="stopRecording" class="stop-btn">⏹️ 停止录制</button>
        </div>

        <div v-if="recordedBlob" class="playback-controls">
          <button 
  @click="useRecording" 
  class="use-btn" 
  :disabled="used"
  :class="{ disabled: used }"
>
  使用这个录制
</button>

          <button @click="reRecord" class="re-record-btn"> 重新录制</button>
        </div>
      </div>

      <div v-if="recording" class="recording-status">
        <div class="recording-indicator">
          <div class="recording-dot"></div>
          <span>录制中... {{ formatTime(recordingTime) }}</span>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, watch } from 'vue'

const videoPlayer = ref(null)
const recordedBlob = ref(null)
const recordedURL = ref('')
const recording = ref(false)
const mediaStream = ref(null)
const mediaRecorder = ref(null)
const recordingTime = ref(0)
const recordingTimer = ref(null)

const used = ref(false)


const emit = defineEmits(['recorded'])

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 },
      audio: true
    })

    mediaStream.value = stream
  } catch (error) {
    console.error('无法启动摄像头:', error)
    alert('无法启动摄像头，请检查设备权限')
  }
}

function startRecording() {
  if (!mediaStream.value) return

  try {
    mediaRecorder.value = new MediaRecorder(mediaStream.value, {
      mimeType: 'video/webm;codecs=vp8,opus'
    })

    const chunks = []

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data)
      }
    }

    mediaRecorder.value.onstop = () => {
      const blob = new Blob(chunks, { type: 'video/webm' })
      recordedBlob.value = blob
      recordedURL.value = URL.createObjectURL(blob)

      clearInterval(recordingTimer.value)
      recordingTimer.value = null
      recordingTime.value = 0
    }

    mediaRecorder.value.start()
    recording.value = true
    recordingTime.value = 0
    recordingTimer.value = setInterval(() => {
      recordingTime.value++
    }, 1000)
  } catch (error) {
    console.error('录制启动失败:', error)
    alert('录制启动失败，请检查浏览器支持')
  }
}

function stopRecording() {
  if (mediaRecorder.value && recording.value) {
    mediaRecorder.value.stop()
    recording.value = false
    stopCamera()
  }
}

function stopCamera() {
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }

  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
    recordingTime.value = 0
  }
}

function useRecording() {
  if (recordedBlob.value) {
    const file = new File([recordedBlob.value], 'recorded_video.webm', {
      type: 'video/webm'
    })

    emit('recorded', {
      file,
      url: recordedURL.value
    })

    used.value = true  // 设为已使用，按钮变灰
    console.log('used =', used.value)
  }
}

function reRecord() {
  recordedBlob.value = null
  recordedURL.value = ''
  used.value = false
  startCamera()
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 录制完毕后，不自动播放，清理自动播放属性
function onVideoLoaded() {
  if (recordedBlob.value && videoPlayer.value) {
    videoPlayer.value.pause()
  }
}

onBeforeUnmount(() => {
  stopCamera()
})
</script>



<style scoped>
.video-recorder-container {
  margin: 20px 0;
}

.recorder-section {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  background: white;
}

.camera-preview {
  position: relative;
  width: 100%;
  height: 400px;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-video, .recorded-video {
  height: 100%;
  width: auto;
  object-fit: contain;
}


.no-camera {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #666;
}

.no-camera-icon {
  font-size: 48px;
  color: #ccc;
}

.recorder-controls {
  padding: 16px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.recording-controls, .playback-controls {
  display: flex;
  gap: 12px;
  flex-wrap: nowrap;
}

.start-camera-btn, .record-btn, .stop-btn, .stop-camera-btn, .use-btn, .re-record-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
   white-space: nowrap;
}

.start-camera-btn {
  background: #cfa97e;
  color: white;
}

.start-camera-btn:hover {
  background: #b37700;
}

.record-btn {
  background: #ff4444;
  color: white;
}

.record-btn:hover {
  background: #cc0000;
}

.stop-btn {
  background: #666;
  color: white;
}

.stop-btn:hover {
  background: #333;
}

.stop-camera-btn {
  background: #999;
  color: white;
}

.stop-camera-btn:hover {
  background: #666;
}

.use-btn {
  background: #cfa97e;
  color: white;
}

.use-btn:hover {
  background: #d1a471;
}

.use-btn.disabled,
.use-btn:disabled {
  background: #999 !important;
  cursor: not-allowed;
  color: #ccc !important;
}

.re-record-btn {
  background: white;
  color: black;
}

.re-record-btn:hover {
  background: #4e5256;
}

.recording-status {
  padding: 16px;
  background: #fff3cd;
  border-top: 1px solid #ffeaa7;
  display: flex;
  justify-content: center;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #856404;
}

.recording-dot {
  width: 12px;
  height: 12px;
  background: #ff4444;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
</style>