<template>
  <div class="video-upload-container">
    <div 
      class="upload-area" 
      @click="triggerFileInput" 
      @dragover.prevent 
      @drop.prevent="handleDrop"
    >
      <input 
        ref="fileInput"
        type="file"
        accept="video/*"
        @change="handleFileSelect"
        style="display: none"
      />
      
      <!-- 上传前显示图标和文字 -->
      <div v-if="!selectedFile" class="upload-content">
        <div class="upload-icon">📁</div>
        <div class="upload-text">
          <h3>上传视频文件</h3>
          <p>点击选择或拖拽视频文件到此区域</p>
        </div>
      </div>

      <!-- 上传后显示视频预览 -->
      <div v-else class="video-preview-wrapper">
        <video
          :src="videoURL"
          controls
          class="video-preview"
        ></video>

        <div class="file-info">
          <div class="file-details">
            <div class="file-name">{{ selectedFile.name }}</div>
            <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
          </div>
          <button @click.stop="removeFile" class="remove-btn">✕</button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const fileInput = ref(null)
const selectedFile = ref(null)
const videoURL = ref('')

const emit = defineEmits(['urlChange', 'update:modelValue'])

const props = defineProps({
  modelValue: {
    type: File,
    default: null
  }
})

watch(() => props.modelValue, (newValue) => {
  selectedFile.value = newValue
  if (newValue) {
    videoURL.value = URL.createObjectURL(newValue)
  } else {
    videoURL.value = ''
  }
})

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (file) {
    processFile(file)
  }
}

function handleDrop(event) {
  const file = event.dataTransfer.files?.[0]
  if (file && file.type.startsWith('video/')) {
    processFile(file)
  }
}

function processFile(file) {
  selectedFile.value = file
  emit('update:modelValue', file)

  videoURL.value = URL.createObjectURL(file)
  emit('urlChange', videoURL.value)
}

function removeFile() {
  selectedFile.value = null
  videoURL.value && URL.revokeObjectURL(videoURL.value)
  videoURL.value = ''

  emit('update:modelValue', null)
  emit('urlChange', '')

  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.video-upload-container {
  margin: 20px 0;
}

.upload-area {
  border: 2px dashed #cfa97e;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fefefe;
  position: relative;
  user-select: none;
  min-height: 250px; /* 保证有足够高度 */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-area:hover {
  border-color: #b37700;
  background: #f5e9d7;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-icon {
  font-size: 48px;
  color: #cfa97e;
}

.upload-text h3 {
  font-size: 20px;
  color: #333;
  margin: 0 0 8px 0;
}

.upload-text p {
  color: #666;
  margin: 4px 0;
}

.upload-hint {
  font-size: 14px;
  color: #999;
}

/* 视频预览区 */
.video-preview-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  user-select: none;
}

.video-preview {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  background: black;
}

/* 文件信息栏 */
.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: auto;               /* 不撑满整个父容器 */
  max-width: 320px;          /* 限制最大宽度，可以按需调 */
  padding: 6px 12px;         /* 缩小内边距 */
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  box-sizing: border-box;
}

.file-details {
  flex: 1;
  overflow: hidden;
}

.file-name {
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  font-size:12px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 12px;
  color: #666;
}

.remove-btn {
  background: #ff4444;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.remove-btn:hover {
  background: #cc0000;
}
</style>
