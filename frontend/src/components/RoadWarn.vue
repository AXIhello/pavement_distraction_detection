<template>
  <div class="table-wrapper">
  <div class="title">路面灾害告警</div>
    <!-- 独立的状态切换按钮组 -->
<!-- 弹窗形式展示细节-->
<div v-if="selectedItem" class="modal-overlay" @click.self="backToList">
  <div class="modal-content">
   <RoadAlertDetail
  v-if="selectedItem && detailData"
  :detail="detailData"
  @back="backToList"
/>
  </div>
</div>

<div v-else>
    <div class="status-toggle">
      <button
        @click="activeTab = 'unprocessed'"
        :class="['status-btn', { active: activeTab === 'unprocessed' }]"
      >
        未处理
      </button>
      <button
        @click="activeTab = 'processed'"
        :class="['status-btn', { active: activeTab === 'processed' }]"
      >
        已处理
      </button>
    </div>

    <!-- 综合查询过滤 -->
    <div class="filters">
      <div class="filter-group">
        
        <label class="filter-label">
          <span class="label-text">日期:</span>
          <input type="date" v-model="filterDate" class="filter-input" />
        </label>
        
        <button @click="clearFilters" class="clear-btn">
          <span class="btn-icon">🗑️</span>
          清除筛选
        </button>
      </div>
    </div>

    <!-- 表格容器 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th @click="sortBy('type')" class="sortable-header">
              <div class="header-content">
                <span>视频ID</span>
                <span v-if="sortKey === 'type'" class="sort-indicator">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </span>
              </div>
            </th>
            <th @click="sortBy('date')" class="sortable-header">
              <div class="header-content">
                <span>告警时间</span>
                <span v-if="sortKey === 'date'" class="sort-indicator">
                  {{ sortOrder === 1 ? '▲' : '▼' }}
                </span>
              </div>
            </th>
            <th class="action-header">查看详情</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in displayedData" :key="item.id" class="data-row">
            <td class="type-cell">
              <span class="type-tag">{{ item.id }}</span>
            </td>
            <td class="date-cell">{{ item.date }}</td>
            <td class="action-cell">
              <button @click="viewDetails(item)" class="detail-btn">
                <span class="btn-icon">👁️</span>
                查看详情
              </button>
            </td>
          </tr>
          <tr v-if="displayedData.length === 0" class="empty-row">
            <td colspan="3" class="empty-cell">
              <div class="empty-content">
                <span class="empty-icon">📋</span>
                <span class="empty-text">暂无数据</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import RoadAlertDetail from './RoadAlertDetail.vue'


const activeTab = ref('unprocessed')
const warnings = ref([])

const sortKey = ref('')
const sortOrder = ref(1)

// const filterType = ref('')
const filterDate = ref('')


//显示详情用
const selectedItem = ref(null)
const detailData = ref(null)
const loadingDetail = ref(false)
const errorDetail = ref(null)


// 从后端拉取数据
async function fetchData() {
  try {
    const res = await axios.get('http://localhost:8000/api/logs_alerts/alert_videos')
    
    if (res.data && Array.isArray(res.data)) {
      warnings.value = res.data.map(item => ({
        id: item.id,
        type: item.disease_type,
        date: item.created_at ? item.created_at.split('T')[0] : '未知',
        status: item.status || 'unprocessed'
      }))
    } else {
      console.warn('后端返回的数据格式不正确')
      warnings.value = []
    }
  } catch (e) {
    console.error('获取数据失败', e)
    warnings.value = []
    // 可以添加用户友好的错误提示
    // alert('获取数据失败，请刷新页面重试')
  }
}


// 当前标签页数据
const filteredByTab = computed(() =>
  warnings.value.filter(item => item.status === activeTab.value)
)


const filteredByFilter = computed(() => {
  return filteredByTab.value.filter(item => {
    const matchDate = filterDate.value
      ? item.date.startsWith(filterDate.value)
      : true
    return matchDate
  })
})


// 排序后最终显示
const displayedData = computed(() => {
  if (!sortKey.value) return filteredByFilter.value

  return [...filteredByFilter.value].sort((a, b) => {
    if (a[sortKey.value] < b[sortKey.value]) return -1 * sortOrder.value
    if (a[sortKey.value] > b[sortKey.value]) return 1 * sortOrder.value
    return 0
  })
})

function sortBy(key) {
  if (sortKey.value === key) {
    sortOrder.value = -sortOrder.value
  } else {
    sortKey.value = key
    sortOrder.value = 1
  }
}

async function viewDetails(item) {
  // 先清理之前的状态
  selectedItem.value = null
  detailData.value = null
  errorDetail.value = null
  loadingDetail.value = true
  
  try {
    const res = await axios.get(`http://localhost:8000/api/logs_alerts/alert_video_detail/${item.id}`)
    
    // 检查返回的数据是否有效
    if (res.data) {
      detailData.value = res.data
      
      // 调试信息
      if (res.data.frames && res.data.frames.length) {
        res.data.frames.forEach((frame, idx) => {
          console.log(`第${idx + 1}帧图片链接:`, frame.image_url)
        })
      } else {
        console.log('没有帧图片链接数据')
      }
      
      // 只有数据获取成功才设置selectedItem
      selectedItem.value = item
    } else {
      throw new Error('返回数据为空')
    }
  } catch (e) {
    errorDetail.value = '获取详情失败，请稍后重试'
    console.error('获取详情失败', e)
    alert('获取详情失败，请稍后重试')
  } finally {
    loadingDetail.value = false
  }
}
import { nextTick } from 'vue'

async function backToList() {
  // 立即清理所有相关状态
  selectedItem.value = null
  detailData.value = null
  errorDetail.value = null
  loadingDetail.value = false
  
  // 等待DOM更新完成，确保子组件完全卸载
  await nextTick()
  
  // 重新获取最新数据
  await fetchData()
}

function clearFilters() {

  filterDate.value = ''
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* 弹窗遮罩层 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5); /* 半透明背景 */
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

/* 弹窗内容容器 */
.modal-content {
  background-color: transparent;
  border-radius: 0;
  padding: 0;
  max-width: none;
  max-height: none;
  overflow: visible;
  box-shadow: none;
}


/* 弹窗动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.table-wrapper {
  position: relative;
  margin-top: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.title {
  position: sticky;
  top: 20px;
  left: 20px;
  font-size: 24px;
  font-weight: bold;
  color: #1f2937;
  background-color: rgba(255, 255, 255, 0.7);
  padding: 8px 16px;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}
/* 独立的状态切换按钮组 */
.status-toggle {
  /* 取消绝对定位 */
  position: static;
  margin-bottom: 16px;
  
  display: flex;
  justify-content: center; /* 水平居中 */
  gap: 8px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}


.status-btn {
  padding: 8px 16px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  min-width: 80px;
  
  /* 未激活状态：灰底白字 */
  background-color: #6b7280;
  color: #ffffff;
}

.status-btn:first-child {
  border-radius: 8px 0 0 8px;
}

.status-btn:last-child {
  border-radius: 0 8px 8px 0;
}

.status-btn:hover:not(.active) {
  background-color: #4b5563;
  transform: translateY(-1px);
}

.status-btn.active {
  /* 激活状态：黑底白字 */
  background-color: #1f2937;
  color: #ffffff;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 过滤器区域 */
.filters {
  margin-top: 40px;
  margin-bottom: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.filter-group {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  user-select: none;
}

.label-text {
  color: #6b7280;
  font-weight: 400;
}

.filter-select,
.filter-input {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background-color: #ffffff;
  transition: all 0.2s ease;
  min-width: 120px;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: linear-gradient(45deg, #ef4444, #dc2626);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  user-select: none;
}

.clear-btn:hover {
  background: linear-gradient(45deg, #dc2626, #b91c1c);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

/* 表格容器 */
.table-container {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  background: white;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

/* 表头样式 */
.data-table thead {
  background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
}

.sortable-header {
  padding: 16px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease;
  color: #ffffff;
  font-weight: 600;
}

.sortable-header:hover {
  background: rgba(255, 255, 255, 0.1);
}

.action-header {
  padding: 16px;
  color: #ffffff;
  font-weight: 600;
  text-align: center;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.sort-indicator {
  color: #3b82f6;
  font-size: 12px;
  font-weight: bold;
}

/* 表格行样式 */
.data-row {
  transition: background-color 0.2s ease;
  border-bottom: 1px solid #e5e7eb;
}

.data-row:hover {
  background-color: #f9fafb;
}

.data-row:last-child {
  border-bottom: none;
}

.type-cell,
.date-cell,
.action-cell {
  padding: 16px;
  vertical-align: middle;
}

.type-tag {
  display: inline-block;
  padding: 4px 12px;
  background: linear-gradient(45deg, #3b82f6, #1d4ed8);
  color: white;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.date-cell {
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.action-cell {
  text-align: center;
}

.detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: linear-gradient(45deg, #10b981, #059669);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  user-select: none;
}

.detail-btn:hover {
  background: linear-gradient(45deg, #059669, #047857);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-icon {
  font-size: 14px;
}

/* 空数据样式 */
.empty-row {
  background-color: #f9fafb;
}

.empty-cell {
  padding: 40px;
  text-align: center;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-group {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .filter-label {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .filter-select,
  .filter-input {
    width: 100%;
  }
  
  .status-toggle {
    position: static;
    margin-bottom: 20px;
    align-self: flex-start;
  }
  
  .filters {
    margin-top: 0;
  }
  
  .data-table {
    font-size: 14px;
  }
  
  .type-cell,
  .date-cell,
  .action-cell {
    padding: 12px 8px;
  }
}
</style>