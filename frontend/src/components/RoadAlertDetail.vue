<template> 
  <div class="detail-view">
    <!-- 关闭按钮 -->
    <button @click="$emit('back')" class="detail-back-btn">×</button>

    <!-- 顶部信息 -->
 <div class="detail-header">
  <div class="detail-info-wrapper">
    <div class="detail-info">
      <p><strong>视频ID：</strong>{{ detail.id }}</p>
      <p><strong>告警帧数：</strong>{{ alertFrameCount }}</p>
      <p>
        <strong>类别统计：</strong> 
        <span v-for="(count, type) in diseaseTypeCount" :key="type" class="disease-type-tag">
          {{ type }} ({{ count }})
        </span>
      </p>
    </div>
    <div v-if="isAdmin" class="delete-wrapper">
      <button @click="confirmDeleteVideo" class="delete-btn">删除该视频及所有告警帧</button>
    </div>
  </div>
</div>

    <!-- 帧图像轮播区域 -->
    <div v-if="detail.frames && detail.frames.length" class="carousel-wrapper">
      <button @click="prevFrame" class="carousel-btn" aria-label="上一帧">◀️</button>
<div class="frame-display">
  <img
    :src="getFrameImageUrl(detail.frames[currentFrameIndex])"
    class="frame-image"
    alt="帧图像"
  />
  <div class="frame-details">
    <h3>帧详细信息</h3>
    <p><strong>类型：</strong>{{ detail.frames[currentFrameIndex].disease_type || '未知' }}</p>
    <p><strong>置信度：</strong>{{ (detail.frames[currentFrameIndex].confidence * 100).toFixed(1) }}%</p>

    <!-- 新增：帧索引与自动播放控制 -->
    <div class="frame-control">
      <p class="frame-index">
        当前帧：{{ currentFrameIndex + 1 }} / {{ detail.frames.length }}
      </p>
      <button class="autoplay-toggle-btn" @click="toggleAutoPlay">
        {{ isAutoPlaying ? '暂停轮播' : '开始轮播' }}
      </button>
    </div>
  </div>
</div>


      <button @click="nextFrame" class="carousel-btn" aria-label="下一帧">▶️</button>
    </div>

    <div v-else>
      <p style="color: #888; margin-top: 20px;">暂无帧图像可显示</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'

const isAdmin = ref(false)
onMounted(() => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  isAdmin.value = userInfo.role === 'admin'
})

async function confirmDeleteVideo() {
  if (!props.detail?.id) return

  const confirmed = window.confirm('确定要删除该视频及所有告警帧吗？此操作不可撤销。')
  if (!confirmed) return

  try {
    await axios.delete(`http://localhost:8000/api/face_alert_videos/${props.detail.id}`)
    alert('删除成功')
    emit('back')  // 触发返回到列表或上一页
  } catch (err) {
    console.error('删除失败:', err)
    alert('删除失败，请稍后重试')
  }
}

function getFrameImageUrl(frame) {
  if (!frame || !frame.image_url) return ''
  return `http://localhost:8000/${frame.image_url.replace(/\\/g, '/')}`
}

const props = defineProps({
  detail: Object
})
defineEmits(['back'])

const isAutoPlaying = ref(true)

function toggleAutoPlay() {
  if (isAutoPlaying.value) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  } else {
    startAutoPlay()
  }
  isAutoPlaying.value = !isAutoPlaying.value
}


function startAutoPlay() {
  if (autoPlayTimer || !isAutoPlaying.value) return
  autoPlayTimer = setInterval(() => {
    nextFrame()
  }, 1000)
}

function resetAutoPlay() {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
  if (isAutoPlaying.value) startAutoPlay()
}


const currentFrameIndex = ref(0)
let autoPlayTimer = null

const alertFrameCount = computed(() => {
  if (!props.detail?.frames) return 0
  return props.detail.frames.length
})

const diseaseTypeCount = computed(() => {
  const counts = {}
  if (!props.detail?.frames) return counts
  for (const frame of props.detail.frames) {
    const type = frame.disease_type || '未知'
    counts[type] = (counts[type] || 0) + 1
  }
  return counts
})

watch(() => props.detail?.frames, () => {
  currentFrameIndex.value = 0
  resetAutoPlay()
})

function prevFrame() {
  const frames = props.detail?.frames || []
  if (!frames.length) return
  currentFrameIndex.value =
    (currentFrameIndex.value - 1 + frames.length) % frames.length
  resetAutoPlay()
}

function nextFrame() {
  const frames = props.detail?.frames || []
  if (!frames.length) return
  currentFrameIndex.value = (currentFrameIndex.value + 1) % frames.length
  resetAutoPlay()
}

// function startAutoPlay() {
//   if (autoPlayTimer) return
//   autoPlayTimer = setInterval(() => {
//     nextFrame()
//   }, 3000) // 3秒切换一帧
// }

// function resetAutoPlay() {
//   if (autoPlayTimer) {
//     clearInterval(autoPlayTimer)
//     autoPlayTimer = null
//   }
//   startAutoPlay()
// }

onMounted(() => {
  startAutoPlay()
})

onUnmounted(() => {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
})
</script>

<style scoped>
.detail-view {
  position: relative;
  padding: 16px 20px;
  background-color: #f9fafb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  max-width: 800px;
  width: 90vw;
  margin: 40px auto;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  color: #1f2937;
  overflow-x: hidden;
}

.detail-back-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  font-size: 24px;
  font-weight: 400;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  z-index: 10;
}

.detail-back-btn:hover {
  color: #ef4444;
  background-color: rgba(254, 242, 242, 0.6);
  transform: scale(1.05);
}

/* 顶部信息区域 */
.detail-header {
  margin-bottom: 24px;
  margin-top: 20px;
}

.detail-info-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.detail-info {
  flex: 1 1 auto;
  min-width: 200px; /* 根据需要调整 */
}

.delete-wrapper {
  flex: 0 0 auto;
  margin-top: 4px; /* 让按钮和文字顶部对齐 */
}


.disease-type-tag {
  display: inline-block;
  background: #e0f2fe;
  color: #0369a1;
  padding: 4px 10px;
  margin-right: 8px;
  margin-bottom: 4px;
  border-radius: 14px;
  font-weight: 500;
  font-size: 12px;
}

/* 轮播区域 */
.carousel-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-top: 20px;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
}

.carousel-btn {
  font-size: 18px;
  padding: 12px 16px;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel-btn:hover {
  background-color: #f3f4f6;
  border-color: #d1d5db;
  transform: translateY(-1px);
}

/* 图片 + 详情横向展示卡片 */
.frame-display {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  flex: 1;
  user-select: none;
  max-width: calc(100% - 140px);
  background: #ffffff;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  overflow-wrap: break-word;
}

.frame-image {
  width: auto;
  max-width: 70%;
  max-height: 450px;
  height: auto;
  object-fit: contain;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

/* 更简洁的详情样式 */
.frame-details {
  flex: 1;
  background: transparent;
  border-radius: 12px;
  padding: 0;
  font-size: 16px;
  color: #374151;
  user-select: text;
}

.frame-details h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-weight: 700;
  color: #111827;
}

.frame-details p {
  margin: 6px 0;
}

/* 小屏幕适配 */
@media (max-width: 768px) {
  .frame-display {
    flex-direction: column;
    max-width: 100%;
  }

  .frame-image {
    max-width: 100%;
    max-height: 350px;
    margin-bottom: 16px;
  }

  .frame-details {
    padding: 0;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .frame-image {
    max-height: 250px;
  }

  .frame-details {
    font-size: 13px;
  }
}
.frame-control {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.frame-index {
  font-size: 14px;
  color: #6b7280;
}

.autoplay-toggle-btn {
  padding: 6px 14px;
  font-size: 14px;
  border: 1px solid #cbd5e1;
  background-color: #f1f5f9;
  color: #1e293b;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.autoplay-toggle-btn:hover {
  background-color: #e2e8f0;
  border-color: #94a3b8;
}

</style>
