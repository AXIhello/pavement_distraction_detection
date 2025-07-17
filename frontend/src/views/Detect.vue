<template>
  <Header2 ref="headerRef" />
  <div class="detect-container" :style="{ paddingTop: headerHeight + 'px' }">
    <div class="page-header">
      <h2 class="page-title">
        上传并分析路障
      </h2>
    </div>

    <div class="upload-mode">
      <button :class="{ active: mode === 'upload' }" @click="mode = 'upload'">📁 上传视频</button>
      <button :class="{ active: mode === 'record' }" @click="mode = 'record'">📹 现场录制</button>
    </div>

    <VideoUpload v-if="mode === 'upload'"
      v-model="videoFile"
      @urlChange="videoURL = $event" />

    <VideoRecorder v-if="mode === 'record'"
      @recorded="handleRecorded" />

    <!-- <video v-if="videoURL && !processing" :src="videoURL" controls /> -->

    <button @click="startAnalysis" :disabled="processing || !videoFile">🔍 开始分析</button>

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
import VideoUpload from '@/components/VideoUpload.vue'
import VideoRecorder from '@/components/VideoRecorder.vue'

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
})

// 模式切换
function handleRecorded({ file, url }) {
  videoFile.value = file
  videoURL.value = url
}

// 重置状态
function resetState() {
  frameResults.value = []
  currentImageIndex.value = 0
  currentFrameNumber.value = 1
  totalFrames.value = 0
  processedFrames.value = 0
  processing.value = false
  autoPlay.value = false
  allDetections.value = []
  uniqueDetectionClasses.value = []
  selectedFrameIndex.value = ''
  readyToShowResults.value = false
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
  frameResults.value = []
  processedFrames.value = 0
  currentImageIndex.value = 0
  currentFrameNumber.value = 1
  allDetections.value = []         
  uniqueDetectionClasses.value = [] 
  
  // 如果已有 socket，先断开连接
  if (socket) {
    socket.off('frame_result')
    socket.off('disconnect')
    socket.off('connect_error')
    socket.disconnect()
  }
  
  socket = io('http://127.0.0.1:8000')

  const analysisCompleted = ref(false)

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

        // 判断是否全部接收完毕，且只触发一次
        if (!analysisCompleted.value && frameResults.value.length >= totalFrames.value) {
          analysisCompleted.value = true
          processing.value = false
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

  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  const frameInterval = 0.2

  // 先监听 loadedmetadata
  video.addEventListener('loadedmetadata', () => {
    if (!isFinite(video.duration) || video.duration === 0) {
      // duration 是无穷大或者 0，尝试触发加载视频结尾以获取正确时长
      video.currentTime = 1e101

      video.ontimeupdate = () => {
        video.ontimeupdate = null
        video.currentTime = 0
        setTimeout(() => startExtraction(video, canvas, ctx, frameInterval), 100)
      }
    } else {
      // duration 是正常数字，直接开始提取帧
      startExtraction(video, canvas, ctx, frameInterval)
    }
  })

  video.addEventListener('error', (e) => {
    alert('视频加载失败，请检查视频格式')
    stopAnalysis()
    if (document.body.contains(video)) {
      document.body.removeChild(video)
    }
  })
}

// 抽出提取帧的函数，便于复用
function startExtraction(video, canvas, ctx, frameInterval) {
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  const duration = video.duration
  totalFrames.value = Math.ceil(duration / frameInterval)

  let currentTime = 0

  const extractFrame = () => {
    if (currentTime >= duration) {
      socket.emit('video_stream_end', { message: '视频帧发送完成' })
      if (document.body.contains(video)) {
        document.body.removeChild(video)
      }
      return
    }

    video.currentTime = currentTime

    video.addEventListener(
      'seeked',
      () => {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        const base64 = canvas.toDataURL('image/jpeg', 1.0)
        socket.emit('video_frame', {
          frame_index: processedFrames.value,
          image: base64
        })

        processedFrames.value++
        currentTime += frameInterval
        setTimeout(extractFrame, 50)
      },
      { once: true }
    )
  }

  extractFrame()
}


function stopAnalysis() {
  processing.value = false
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

.upload-mode {
  display: flex;
  gap: 12px;
  margin: 20px 0;
}

.upload-mode button {
  padding: 12px 28px;
  border: 2px solid #ccc;
  background: #f9f9f9;
  color: #555;
  border-radius: 12px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.25s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  user-select: none;
}

.upload-mode button:hover {
  border-color: #cfa97e;
  color: #b37700;
  background: #fff8e1;
  box-shadow: 0 2px 6px rgba(203,169,126,0.4);
}

.upload-mode button.active {
  border-color: #cfa97e;
  background: #cfa97e;
  color: white;
  box-shadow: 0 4px 12px rgba(203,169,126,0.6);
}


.button-icon {
  margin-right: 8px;
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
  white-space: nowrap;

}

.result-header {
  margin-bottom: 24px;
}

.result-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 16px;
}

.result-stats {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  color: #666;
  font-weight: 500;
}

.stat-value {
  font-weight: 600;
  color: #cfa97e;
}

.image-slider {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
}

.image-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.nav-controls-left, .nav-controls-right {
  display: flex;
  gap: 12px;
}

.frame-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}
.nav-btn, .auto-play-btn {
  padding: 10px 20px;
  border: 2px solid #ccc;
  background: #f9f9f9;
  color: #555;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.25s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  user-select: none;
   white-space: nowrap;
}

.nav-btn:hover:not(:disabled), .auto-play-btn:hover {
  border-color: #cfa97e;
  color: #b37700;
  background: #fff8e1;
  box-shadow: 0 2px 6px rgba(203,169,126,0.4);
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
  border-color: #ddd;
  background: #f0f0f0;
  color: #999;
}

.auto-play-btn.active {
  background: #cfa97e;
  color: white;
  border-color: #cfa97e;
  box-shadow: 0 4px 12px rgba(203,169,126,0.6);
}


.bottom-dropdown {
  padding: 16px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
}

.dropdown-label {
  margin-right: 12px;
  font-weight: 500;
}

.image-result {
  display: flex;
  min-height: 400px;
}

.image-column {
  flex: 1;
  padding: 16px;
  border-right: 1px solid #e0e0e0;
}

.image-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.annotated-frame {
  width: 100%;
  height: auto;
  border-radius: 8px;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 8px;
}

.no-detection {
  color: white;
  font-size: 18px;
  font-weight: 500;
}

.info-column {
  flex: 0 0 300px;
  padding: 16px;
}

.detection-info {
  background: #fff;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgb(0 0 0 / 0.08);
  height: 100%;
  overflow-y: auto; /* 超出滚动 */
  border: 1px solid #ddd;
}

/* 每条检测项单独卡片，白底圆角，细边框，阴影 */
.detection-item {
  background: #fafafa;
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgb(0 0 0 / 0.05);
  transition: box-shadow 0.3s ease;
  cursor: default;
}

/* 悬浮时阴影变深，轻微浮起 */
.detection-item:hover {
  box-shadow: 0 8px 20px rgb(0 0 0 / 0.12);
}

/* 检测标题部分加粗加大，更醒目 */
.detection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 700;
  color: #222;
  font-size: 16px;
}

/* 置信度用暖色，更显眼 */
.detection-confidence {
  color: #d48806; /* 金黄色调 */
  font-weight: 600;
  font-size: 14px;
}

/* 坐标标签加点间距 */
.detection-details {
  font-size: 14px;
  color: #555;
  display: flex;
  gap: 6px;
  font-family: monospace;
}

/* 无检测提示加大字体，颜色柔和 */
.no-detection-message {
  background: #fff9f0;
  border: 1px solid #ffd591;
  color: #ad4e00;
  padding: 40px 20px;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgb(255 213 79 / 0.3);
  text-align: center;
  font-size: 18px;
  user-select: none;
}

/* 无检测图标加大并居中 */
.no-detection-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.bbox-label {
  font-weight: 500;
}

.bbox-values {
  font-family: monospace;
  margin-left: 8px;
}

.no-detection-message {
  text-align: center;
  padding: 32px;
  color: #666;
}

.no-detection-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
</style>