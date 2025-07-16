<template>
  <Header2 ref="headerRef" />
  <div class="detect-container" :style="{ paddingTop: headerHeight + 'px' }">
    <div class="page-header">
      <h2 class="page-title">
        上传并分析路障
      </h2>
    </div>

    <!-- 模式选择按钮 -->
    <div class="upload-mode">
      <button :class="{ active: mode === 'upload' }" @click="selectUploadMode">
        <span class="button-icon">📁</span>
        上传视频
      </button>
      <button :class="{ active: mode === 'record' }" @click="selectRecordMode">
        <span class="button-icon">📹</span>
        现场录制
      </button>
    </div>

    <!-- 上传视频 -->
    <div class="upload-section" v-if="mode === 'upload'">
      <div class="upload-area" v-if="!videoFile">
        <div class="upload-content">
          <div class="upload-icon">📤</div>
          <p>点击选择视频文件</p>
          <input type="file" accept="video/*" @change="handleVideoChange" class="file-input" />
        </div>
      </div>
      <div class="video-actions" v-if="videoFile">
        <button @click="removeVideo" class="remove-btn">
          <span class="button-icon">🗑️</span>
          卸载视频
        </button>
      </div>
    </div>

    <!-- 现场录制 -->
    <div class="record-section" v-if="mode === 'record'">
      <div class="video-container">
        <video ref="recordPreview" autoplay muted playsinline></video>
        <div class="recording-indicator" v-if="recording">
          <div class="recording-dot"></div>
          <span>正在录制...</span>
        </div>
      </div>
      <div class="record-buttons">
        <button @click="startRecording" :disabled="recording" class="record-btn">
          <span class="button-icon">⏺️</span>
          开始录制
        </button>
        <button @click="stopRecording" :disabled="!recording" class="stop-btn">
          <span class="button-icon">⏹️</span>
          停止录制
        </button>
        <button @click="cancelRecording" v-if="recordedBlob" class="cancel-btn">
          <span class="button-icon">❌</span>
          取消录制
        </button>
      </div>
    </div>

    <!-- 视频预览 -->
    <div class="video-preview" v-if="videoURL && !recording">
      <div class="video-container">
        <video :src="videoURL" controls muted playsinline ref="videoEl"></video>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions" v-if="videoFile && !processing && !recording">
      <button @click="startAnalysis" :disabled="processing" class="analyze-btn">
        <span class="button-icon">🔍</span>
        开始分析
      </button>
    </div>

    <!-- 状态提示 -->
    <div class="status" v-if="processing">
      <div class="status-content">
        <div class="status-text">
          <p v-if="processing">正在处理中... 
            <span v-if="totalFrames > 0" class="progress-text">
              ({{ processedFrames }}/{{ totalFrames }})
            </span>
          </p>
    
        </div>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-container" v-if="processing && totalFrames > 0">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: (processedFrames / totalFrames) * 100 + '%' }"></div>
      </div>
      <div class="progress-percentage">{{ Math.round((processedFrames / totalFrames) * 100) }}%</div>
    </div>

    <!-- 分析完成提示 -->
    <div v-if="showCompleteNotice" class="popup-notice">
      分析完毕！
    </div>

    <!-- 分析结果：等待所有帧接收完再展示 -->
<div v-if="readyToShowResults" class="results-section">
      <div class="result-header">
        <h3 class="result-title">
          分析结果
        </h3>
        <div class="result-stats">
          <div class="stat-item">
            <span class="stat-label">总帧数:</span>
            <span class="stat-value">{{ frameResults.length }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">告警帧数:</span>
            <span class="stat-value">{{ framesWithDetections.length }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">路障类别:</span>
            <span class="stat-value">{{ uniqueDetectionClasses.length }}</span>
          </div>
        </div>
      </div>

      <!-- 图像轮播与检测详情 -->
      <div class="image-slider">
        <div class="image-controls">
          <!-- 左侧导航按钮 -->
          <div class="nav-controls-left">
            <button @click="prevImage" :disabled="frameResults.length <= 1" class="nav-btn">
              <span class="button-icon">◀️</span>
              上一张
            </button>
          </div>
          
          <!-- 中间帧信息 -->
          <div class="frame-info">
            <span>第</span>
            <input 
              type="number" 
              v-model.number="currentFrameNumber"
              :min="1" 
              :max="frameResults.length"
              @keyup.enter="jumpToSpecificFrame"
              @blur="jumpToSpecificFrame"
              @input="handleFrameNumberInput"
              style="width: 60px; text-align: center; border: 1px solid #ccc; border-radius: 6px;"
            />
            <span> / {{ frameResults.length }} 帧</span>
          </div>

          <!-- 右侧导航和自动播放按钮 -->
          <div class="nav-controls-right">
            <button @click="nextImage" :disabled="frameResults.length <= 1" class="nav-btn">
              下一张
              <span class="button-icon">▶️</span>
            </button>
            <button @click="toggleAutoPlay" class="auto-play-btn" :class="{ active: autoPlay }">
              <span class="button-icon">{{ autoPlay ? '⏸️' : '▶️' }}</span>
              {{ autoPlay ? '停止自动播放' : '自动播放' }}
            </button>
          </div>
        </div>

        <!-- 有检测帧下拉选择 -->
        <div v-if="framesWithDetections.length" class="bottom-dropdown">
          <label for="frameSelect" class="dropdown-label">跳转到有检测结果的帧:</label>
          <select id="frameSelect" v-model="selectedFrameIndex" @change="jumpToFrameIndex">
            <option value="">请选择</option>
            <option v-for="frameIndex in framesWithDetections" :key="frameIndex" :value="frameIndex">
              第 {{ frameIndex + 1 }} 帧
            </option>
          </select>
        </div>

        <div class="image-result">
          <div class="image-column">
            <div class="image-wrapper">
              <img :src="frameResults[currentImageIndex].image" class="annotated-frame" />
              <div class="image-overlay" v-if="frameResults[currentImageIndex].detections.length === 0">
                <div class="no-detection">无检测结果</div>
              </div>
            </div>
          </div>
          <div class="info-column">
            <div class="detection-info">
              <h4 class="detection-title">
                检测结果
                <span class="detection-count" v-if="frameResults[currentImageIndex].detections.length">
                  ({{ frameResults[currentImageIndex].detections.length }} 个)
                </span>
              </h4>
              <div class="detection-list" v-if="frameResults[currentImageIndex].detections.length">
                <div 
                  v-for="(det, i) in frameResults[currentImageIndex].detections" 
                  :key="i"
                  class="detection-item"
                >
                  <div class="detection-header">
                    <span class="detection-class">{{ det.class }}</span>
                    <span class="detection-confidence">{{ (det.confidence * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="detection-details">
                    <span class="bbox-label">坐标:</span>
                    <span class="bbox-values">[{{ det.bbox.join(', ') }}]</span>
                  </div>
                </div>
              </div>
              <div v-else class="no-detection-message">
                <div class="no-detection-icon">🔍</div>
                <p>本帧未检测到路障</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { io } from 'socket.io-client'
import Header2 from '@/components/Navigation.vue'

const headerRef = ref(null)
const headerHeight = ref(0)
const selectedFrameIndex = ref('')

const mode = ref('upload') // 上传 或 录制

const readyToShowResults = ref(false)

 //容错处理（后端未返回全部数据）
let fallbackTimer = null
let fallbackTriggered = false



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

// 新增：当前帧号（用于显示和输入）
const currentFrameNumber = ref(1)

let socket = null

// 录制相关
const recordPreview = ref(null)
const mediaRecorder = ref(null)
const recordedChunks = ref([])
const recordedBlob = ref(null)
const recording = ref(false)
const mediaStream = ref(null)

// 计算属性：有检测结果的帧索引
const framesWithDetections = computed(() => {
  return frameResults.value
    .map((frame, index) => ({ index, hasDetections: frame.detections.length > 0 }))
    .filter(item => item.hasDetections)
    .map(item => item.index)
})

// 监听当前图像索引变化，同步更新帧号和下拉选择
watch(currentImageIndex, (newIndex) => {
  currentFrameNumber.value = newIndex + 1
  
  // 如果当前帧有检测结果，更新下拉选择
  if (framesWithDetections.value.includes(newIndex)) {
    selectedFrameIndex.value = newIndex
  } else {
    selectedFrameIndex.value = ''
  }
})

// 监听帧结果变化，重置状态
watch(frameResults, () => {
  if (frameResults.value.length > 0) {
    currentImageIndex.value = 0
    currentFrameNumber.value = 1
    selectedFrameIndex.value = ''
  }
})

// --- UI 相关 ---

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
  stopCamera()
})

// 模式切换
function selectUploadMode() {
  resetAll()
  mode.value = 'upload'
}

function selectRecordMode() {
  resetAll()
  mode.value = 'record'
  startCamera()
}

// 处理上传视频文件
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
  document.querySelector('.file-input').value = null
}

// 录制相关

async function startCamera() {
  try {
    mediaStream.value = await navigator.mediaDevices.getUserMedia({ video: true })
    if (recordPreview.value) {
      recordPreview.value.srcObject = mediaStream.value
    }
  } catch (err) {
    alert('无法访问摄像头：' + err.message)
  }
}

function stopCamera() {
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }
  if (recordPreview.value) {
    recordPreview.value.srcObject = null
  }
}

function startRecording() {
  if (!mediaStream.value) {
    alert('摄像头未启动')
    return
  }
  recordedChunks.value = []
  const options = { mimeType: 'video/webm; codecs=vp8' }
  const recorder = new MediaRecorder(mediaStream.value, options)
  mediaRecorder.value = recorder
  recording.value = true

  recorder.ondataavailable = e => {
    if (e.data.size > 0) recordedChunks.value.push(e.data)
  }

  recorder.onstop = () => {
    recordedBlob.value = new Blob(recordedChunks.value, { type: 'video/webm' })
    videoFile.value = new File([recordedBlob.value], 'recorded.webm', { type: 'video/webm' })
    videoURL.value = URL.createObjectURL(recordedBlob.value)
    stopCamera()
    recording.value = false
  }

  recorder.start()
}

function stopRecording() {
  if (mediaRecorder.value && recording.value) {
    mediaRecorder.value.stop()
  }
}

function cancelRecording() {
  resetAll()
  stopCamera()
}

// 重置状态
function resetState() {
  frameResults.value = []
  currentImageIndex.value = 0
  currentFrameNumber.value = 1
  totalFrames.value = 0
  processedFrames.value = 0
  // extractionComplete.value = false
  processing.value = false
  autoPlay.value = false
  allDetections.value = []
  uniqueDetectionClasses.value = []
  selectedFrameIndex.value = ''
  readyToShowResults.value = false
}

function resetAll() {
  videoFile.value = null
  videoURL.value = ''
  recordedBlob.value = null
  recording.value = false
  stopCamera()
  resetState()
}

// 处理帧号输入
function handleFrameNumberInput() {
  // 实时验证输入范围
  if (currentFrameNumber.value < 1) {
    currentFrameNumber.value = 1
  } else if (currentFrameNumber.value > frameResults.value.length) {
    currentFrameNumber.value = frameResults.value.length
  }
}

// 跳转到指定帧号
function jumpToSpecificFrame() {
  if (currentFrameNumber.value >= 1 && currentFrameNumber.value <= frameResults.value.length) {
    currentImageIndex.value = currentFrameNumber.value - 1
  } else {
    // 如果输入无效，恢复到当前帧号
    currentFrameNumber.value = currentImageIndex.value + 1
  }
}

// 跳转到指定帧索引（下拉选择使用）
function jumpToFrameIndex() {
  if (selectedFrameIndex.value !== '' && selectedFrameIndex.value >= 0 && selectedFrameIndex.value < frameResults.value.length) {
    currentImageIndex.value = selectedFrameIndex.value
  }
}

// --- 分析功能 ---

function startAnalysis() {
  if (!videoURL.value) return alert('请先上传或录制视频')
  if (processing.value) return alert('正在分析中...')
  // if (readyToShowResults.value) return alert('请先卸载视频再重新分析')
  if (videoEl.value?.readyState < 3) {
  return alert('视频尚未加载完成，请稍等片刻')
}

// 当收到的帧与发送过去的不符时
function forceShowResults() {
  processing.value = false
  readyToShowResults.value = true
  showCompleteNotice.value = true
  setTimeout(() => {
    showCompleteNotice.value = false
  }, 3000)
}



  processing.value = true
  // extractionComplete.value = false
  frameResults.value = []
  processedFrames.value = 0
  currentImageIndex.value = 0
  currentFrameNumber.value = 1
  // 如果已有 socket，先断开连接
  if (socket) {
    socket.off('frame_result')
    socket.off('disconnect')
    socket.off('connect_error')
    socket.disconnect()
  }
  
  socket = io('http://127.0.0.1:8000')

  socket.on('connect', () => {
    extractFramesOffline()

    socket.on('connect', () => {
  extractFramesOffline()

  // fallback 定时器：3 秒后如果没有任何帧，强制展示结果
  fallbackTimer = setTimeout(() => {
    if (!fallbackTriggered && frameResults.value.length === 0) {
      console.warn('3秒未收到帧，执行容错逻辑')
      fallbackTriggered = true
      forceShowResults()
    }
  }, 3000)
})

  })

 const analysisCompleted = ref(false)

socket.on('frame_result', (result) => {
  //收到便清除
  if (fallbackTimer) {
    clearTimeout(fallbackTimer)
    fallbackTimer = null
  }
  const { frame_index, annotated_image, detections } = result

  // 累加 detection 信息
  if (detections) {
    allDetections.value.push(...detections)
  }

  if (typeof frame_index === 'number' && annotated_image) {
    const frameData = {
      frame_index,
      image: `data:image/jpeg;base64,${annotated_image}`,
      detections: detections || []
    }

    const exists = frameResults.value.some(f => f.frame_index === frame_index)
    if (!exists) {
      frameResults.value.push(frameData)

      // 排序
      frameResults.value.sort((a, b) => a.frame_index - b.frame_index)

      // ✅ 判断是否全部接收完毕，且只触发一次
      if (!analysisCompleted.value && frameResults.value.length >= totalFrames.value) {
        analysisCompleted.value = true
        processing.value = false
        // extractionComplete.value = true
        readyToShowResults.value = true


        // 统计唯一检测类别
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

        // 弹窗提示
        showCompleteNotice.value = true
        setTimeout(() => {
          showCompleteNotice.value = false
        }, 3000)
      }
    }
  }
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
    totalFrames.value = Math.ceil(duration / frameInterval)

    let currentTime = 0

    const extractFrame = () => {
      if (currentTime >= duration) {
        // extractionComplete.value = true
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
              socket.emit('video_frame', { 
                frame_index: processedFrames.value,
                image: base64 })

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
  // extractionComplete.value = false
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
    }, 300)
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
  hasUnsavedChanges()
    ? (window.confirm('未完成分析将丢失，确定离开？') ? next() : next(false))
    : next()
})
</script>
<style scoped>
.detect-container {
  max-width: 960px;
  margin: auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: transparent;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.page-header {
  text-align: left; 
  margin-top: 20px;
}

.page-title {
  font-size: 28px;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: flex-start; 
  gap: 12px;
}
.button-icon {
  margin-right: 8px;
}

.upload-mode {
  margin-bottom: 24px;
  margin-top:10px;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.upload-mode button {
  padding: 12px 24px;
  border: 2px solid #ddd;
  border-radius: 12px;
  cursor: pointer;
  background: white;
  color: #333;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.upload-mode button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.upload-mode button.active {
  background: #1e2124;
  color: white;
  border-color: #1e2124;
}

.upload-area {
  border: 2px dashed #cfa97e;
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  background: #fefdf9;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.upload-area:hover {
  border-color: #b37700;
  background: #fdfbf5;
}

.upload-content {
  position: relative;
  z-index: 2;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.video-actions {
  margin-top: 16px;
  text-align: center;
}

remove-btn.remove-btn {
  padding: 10px 20px;
  background: #5d5a5a;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;

  
}

.remove-btn:hover {
  background: #e6bb2e;
  transform: translateY(-1px);
}

.video-container {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.video-preview video,
.record-section video {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
  background: rgb(212, 209, 201);
}

.recording-indicator {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(220, 53, 69, 0.9);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.recording-dot {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.record-buttons {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.record-buttons button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
}

.record-btn {
  background: #28a745;
  color: white;
}

.record-btn:hover:not(:disabled) {
  background: #218838;
}

.stop-btn {
  background: #dc3545;
  color: white;
}

.stop-btn:hover:not(:disabled) {
  background: #c82333;
}

.cancel-btn {
  background: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background: #5a6268;
}

.record-buttons button:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.actions {
  margin-top: 24px;
  text-align: center;
}

.analyze-btn {
  padding: 16px 32px;
  background: linear-gradient(135deg, #1e2124, #2c3136);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 18px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.analyze-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3);
}

.analyze-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

.status {
  margin-top: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border-radius: 12px;
  border-left: 4px solid #cfa97e;
}

.status-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-icon {
  font-size: 24px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.status-text {
  flex: 1;
}

.progress-text {
  font-weight: 600;
  color: #cfa97e;
}

.progress-container {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #e7a74d, #b37700);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-percentage {
  font-weight: 600;
  color: #b37700;
  min-width: 48px;
}

.popup-notice {
  position: fixed;
  top: 100px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #f5e9d7, #e6d3b7);
  color: #333;
  padding: 16px 32px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  font-size: 18px;
  font-weight: 600;
  opacity: 1;
  animation: slideDown 0.3s ease, fadeOut 2s 1s forwards;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 8px;
}

@keyframes slideDown {
  from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
  to { transform: translateX(-50%) translateY(0); opacity: 1; }
}

@keyframes fadeOut {
  to { opacity: 0; transform: translateX(-50%) translateY(-20px); }
}

.results-section {
  margin-top: 32px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border-radius: 12px;
  flex-wrap: wrap;
  gap: 16px;
}

.result-title {
  font-size: 24px;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-stats {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e2124;
}

.quick-nav {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
}

.nav-section h4 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-section h4:before {
  content: "🚀";
}

.nav-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.jump-input {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.jump-input input {
  padding: 8px 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  width: 80px;
  text-align: center;
  transition: border-color 0.3s ease;
}

.jump-input input:focus {
  outline: none;
  border-color: #cfa97e;
}

.jump-btn {
  padding: 8px 16px;
  background: #cfa97e;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.jump-btn:hover {
  background: #b37700;
  transform: translateY(-1px);
}

.detection-frames {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.frame-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 120px;
  overflow-y: auto;
  padding: 4px;
}

.frame-tag {
  padding: 6px 12px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 20px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
  min-width: 32px;
  text-align: center;
}

.frame-tag:hover {
  background: #e9ecef;
  transform: translateY(-1px);
}

.frame-tag.active {
  background: #cfa97e;
  color: white;
  border-color: #cfa97e;
}

.image-slider {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
}



.image-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 16px;
  min-height: 44px; /* 确保有足够的高度 */
  flex-wrap: nowrap; /* 防止换行 */
}

/* 左侧按钮组 */
.nav-controls-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0; /* 防止缩小 */
}

/* 中间帧信息 */
.frame-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap; /* 防止文字换行 */
  flex-shrink: 0; /* 防止缩小 */
  min-width: 120px; /* 确保有足够宽度 */
  justify-content: center;
}

/* 右侧按钮组 */
.nav-controls-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0; /* 防止缩小 */
}

.nav-btn {
  padding: 10px 16px;
  background: #cfa97e;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap; /* 防止文字换行 */
  min-width: 80px; /* 确保按钮有最小宽度 */
  justify-content: center;
}

.nav-btn:hover:not(:disabled) {
  background: #b37700;
  transform: translateY(-1px);
}

.nav-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.current-frame {
  color: #1e2124;
}

.total-frames {
  color: #666;
}

.auto-play-btn {
  padding: 10px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap; /* 防止文字换行 */
  min-width: 120px; /* 确保按钮有足够宽度 */
  justify-content: center;
}

.auto-play-btn:hover {
  background: #5a6268;
}

.auto-play-btn.active {
  background: #28a745;
}

.auto-play-btn.active:hover {
  background: #218838;
}

/* 响应式设计 - 小屏幕时调整 */
@media (max-width: 768px) {
  .image-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .nav-controls-left,
  .nav-controls-right {
    justify-content: center;
  }
  
  .frame-info {
    justify-content: center;
    order: -1; /* 在移动端将帧信息放在最上面 */
  }
  
  .nav-btn,
  .auto-play-btn {
    flex: 1;
    min-width: auto;
  }
}

@media (max-width: 480px) {
  .nav-controls-left,
  .nav-controls-right {
    flex-direction: column;
    gap: 8px;
  }
  
  .nav-btn,
  .auto-play-btn {
    width: 100%;
  }
}

.image-result {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 768px) {
  .image-result {
    grid-template-columns: 1fr;
  }
}

.image-column {
  display: flex;
  flex-direction: column;
}

.image-wrapper {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.annotated-frame {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.no-detection {
  background: rgba(255, 255, 255, 0.2);
  padding: 12px 24px;
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.info-column {
  display: flex;
  flex-direction: column;
}

.detection-info {
  background: #fefdf9;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 20px;
  font-size: 14px;
  line-height: 1.6;
  height: fit-content;
}

.detection-title {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.detection-count {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.detection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detection-item {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.detection-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.detection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.detection-class {
  font-weight: 700;
  color: #1e2124;
  font-size: 16px;
}

.detection-confidence {
  background: linear-gradient(135deg, #e7a74d, #b37700);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.detection-details {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.bbox-label {
  color: #666;
  font-weight: 500;
}

.bbox-values {
  color: #1e2124;
  font-weight: 600;
}

.no-detection-message {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.no-detection-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.no-detection-message p {
  margin: 0;
  font-size: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .detect-container {
    padding: 16px;
    margin: 16px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .upload-mode {
    flex-direction: column;
    align-items: center;
  }
  
  .upload-mode button {
    width: 100%;
    max-width: 300px;
  }
  
  .result-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .result-stats {
    justify-content: center;
    width: 100%;
  }
  
  .nav-controls {
    align-items: flex-start;
  }
  
  .jump-input {
    justify-content: flex-start;
  }
  
  .image-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .nav-btn, .auto-play-btn {
    justify-content: center;
  }
}
.bottom-dropdown {
  margin-top: 32px;
  text-align: center;
  padding: 16px 0;
  background: #fffbea;
  border-top: 1px solid #f0e6c1;
  border-radius: 0 0 12px 12px;
}

.dropdown-label {
  font-size: 14px;
  font-weight: 600;
  margin-right: 8px;
  color: #444;
}

.bottom-dropdown select {
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 8px;
  border: 1px solid #cfa97e;
  background: white;
  color: #333;
  cursor: pointer;
  transition: border-color 0.3s ease;
}

.bottom-dropdown select:focus {
  outline: none;
  border-color: #b37700;
}

</style>