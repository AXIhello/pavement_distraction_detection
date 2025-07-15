<template>
  <div class="detail-view">
    <!-- 返回按钮 -->
    <button @click="$emit('back')" class="detail-back-btn">×</button>

    <!-- 顶部信息 -->
   <div class="detail-header" v-if="detail">
  <div class="detail-info-wrapper">
    <div class="detail-info">
      <p><strong>告警帧 ID：</strong>{{ detail.id }}</p>
      <p><strong>帧索引：</strong>{{ detail.frame_index }}</p>
      <p><strong>时间：</strong>{{ detail.created_at }}</p>
      <p><strong>告警类型：</strong>{{ detail.alert_type }}</p>
      <p><strong>置信度：</strong>{{ (detail.confidence * 100).toFixed(1) }}%</p>
    </div>
    <button v-if="isAdmin" @click="confirmDelete" class="inline-delete-btn">删除</button>
  </div>
</div>



    <!-- 图片展示 -->
    <div v-if="detail?.image_url" class="image-wrapper">
      <img
        :src="getFrameImageUrl(detail.image_url)"
        alt="告警图片"
        class="alert-image"
        loading="lazy"
      />
    </div>

    <div v-else>
      <p style="color: #888; margin-top: 20px;">暂无图片显示</p>
    </div>
  </div>

</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  detail: Object
})

const emit = defineEmits(['back'])

// 是否管理员，从 localStorage 中判断
const isAdmin = ref(false)
onMounted(() => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  isAdmin.value = userInfo.role === 'admin'  // 根据你的用户结构调整
})

function getFrameImageUrl(imagePath) {
  if (!imagePath) return ''
  return `http://localhost:8000/${imagePath.replace(/\\/g, '/')}`
}

async function confirmDelete() {
  if (!props.detail?.id) return

  const confirmed = window.confirm('确定要删除该告警帧吗？此操作不可撤销。')
  if (!confirmed) return

  try {
    await axios.delete(`http://localhost:8000/api/face_alert_frames/${props.detail.id}`)
    alert('删除成功')
    emit('back')
  } catch (e) {
    console.error('删除失败', e)
    alert('删除失败，请稍后重试')
  }
}

watch(() => props.detail?.image_url, (newVal) => {
  if (newVal) {
    console.log('图片完整URL:', getFrameImageUrl(newVal))
  } else {
    console.log('无图片路径')
  }
}, { immediate: true })
</script>

<style scoped>
.detail-view {
  position: relative;
  padding: 24px 32px;
  background-color: #f9fafb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  max-width: 720px;
  width: 90vw;
  margin: 40px auto;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  color: #1f2937;
  overflow-x: hidden;
}

/* 返回按钮，右上角圆形X */
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

.detail-header {
  margin-bottom: 24px;
  margin-top: 20px;
}

.detail-info-wrapper {
  display: flex;
  align-items: center;            /* 垂直居中 */
  justify-content: space-between; /* 文字左，按钮右 */
  gap: 16px;
}

.detail-info {
  flex: 1 1 auto;                 /* 占满左边剩余空间 */
  max-width: calc(100% - 100px);  /* 给按钮留出宽度空间 */
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  user-select: none;
}

.detail-info p {
  margin: 6px 0;
}

.image-wrapper {
  text-align: center;
}

.alert-image {
  max-width: 100%;
  max-height: 450px;
  object-fit: contain;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  user-select: none;
}

.inline-delete-btn {
  width: 80px;                   /* 固定宽度 */
  height: 32px;                  /* 固定高度 */
  padding: 6px 0;                /* 左右内边距适中 */
  background: linear-gradient(45deg, #ef4444, #dc2626);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  text-align: center;
  line-height: 20px;
}

.inline-delete-btn:hover {
  background: linear-gradient(45deg, #dc2626, #b91c1c);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(239, 68, 68, 0.25);
}
</style>

