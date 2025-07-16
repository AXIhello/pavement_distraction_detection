<template>
  <div class="road-warn-wrapper">
    <div class="title-section">
      <h3>
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 11H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h4l-2-7z"/>
          <path d="M15 11h4a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-4l2-7z"/>
          <path d="M12 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4z"/>
        </svg>
        路面灾害告警
      </h3>
      <div class="alert-count">
        <span>共 {{ displayedData.length }} 条记录</span>
      </div>
    </div>

    <!-- 弹窗形式展示细节 -->
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
      <!-- 筛选区域 -->
      <div class="filters-card">
        <div class="filters-header">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46"></polygon>
          </svg>
          <span>筛选条件</span>
        </div>
        
        <div class="filters">
          <div class="filter-item">
            <label>日期</label>
            <input type="date" v-model="filterDate" />
          </div>
          
          <div class="filter-actions">
            <button @click="clearFilters" class="btn-secondary">
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                <path d="M3 3v5h5"></path>
              </svg>
              清除筛选
            </button>
          </div>
        </div>
      </div>

      <!-- 表格容器 -->
      <div class="table-card">
        <div class="table-container" v-if="displayedData.length > 0">
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
                <th class="action-header">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in displayedData" :key="item.id" class="data-row">
                <td class="id-cell">
                  <span class="id-badge">{{ item.id }}</span>
                </td>
                <td class="date-cell">{{ item.date }}</td>
                <td class="action-cell">
                  <button @click="viewDetails(item)" class="detail-btn">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    查看详情
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="8" y1="15" x2="16" y2="15"></line>
            <line x1="9" y1="9" x2="9.01" y2="9"></line>
            <line x1="15" y1="9" x2="15.01" y2="9"></line>
          </svg>
          <h4>暂无告警数据</h4>
          <p>当前没有路面灾害告警记录</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import RoadAlertDetail from './RoadAlertDetail.vue'

const warnings = ref([])
const sortKey = ref('')
const sortOrder = ref(1)
const filterDate = ref('')

// 显示详情用
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
        date: item.created_at ? item.created_at.split('T')[0] : '未知'
      }))
    } else {
      console.warn('后端返回的数据格式不正确')
      warnings.value = []
    }
  } catch (e) {
    console.error('获取数据失败', e)
    warnings.value = []
  }
}

// 筛选后的数据
const filteredByFilter = computed(() => {
  return warnings.value.filter(item => {
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
  selectedItem.value = null
  detailData.value = null
  errorDetail.value = null
  loadingDetail.value = true
  
  try {
    const res = await axios.get(`http://localhost:8000/api/logs_alerts/alert_video_detail/${item.id}`)
    
    if (res.data) {
      detailData.value = res.data
      
      if (res.data.frames && res.data.frames.length) {
        res.data.frames.forEach((frame, idx) => {
          console.log(`第${idx + 1}帧图片链接:`, frame.image_url)
        })
      } else {
        console.log('没有帧图片链接数据')
      }
      
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
  selectedItem.value = null
  detailData.value = null
  errorDetail.value = null
  loadingDetail.value = false
  
  await nextTick()
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
.road-warn-wrapper {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: transparent;
}

.title-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title-section h3 {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1f2937;
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.alert-count {
  background: rgba(255, 255, 255, 0.9);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background-color: transparent;
  border-radius: 0;
  padding: 0;
  max-width: none;
  max-height: none;
  overflow: visible;
  box-shadow: none;
}

/* 筛选区域 */
.filters-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.filters-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  color: #374151;
  font-weight: 600;
  font-size: 16px;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  align-items: end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.filter-item input {
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  background: white;
  font-size: 14px;
  transition: all 0.3s ease;
}

.filter-item input:focus {
  outline: none;
  border-color: #00040a;
  box-shadow: 0 0 0 3px rgba(0, 4, 10, 0.1);
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: end;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: 2px solid #e5e7eb;
  background: white;
  color: #6b7280;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  border-color: #d1d5db;
  background: #f9fafb;
  transform: translateY(-1px);
}

/* 表格样式 */
.table-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 14px;
}

.data-table th {
  background: linear-gradient(135deg, #f9f4ecfa 0%, #e8d9c9 100%);
  padding: 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.sortable-header {
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s ease;
}

.sortable-header:hover {
  background: rgba(255, 255, 255, 0.1);
}

.action-header {
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

.data-row {
  transition: all 0.3s ease;
  cursor: pointer;
}

.data-row:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  transform: scale(1.01);
}

.data-table td {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.id-cell {
  min-width: 120px;
}

.id-badge {
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
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.action-cell {
  text-align: center;
}

.detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  background: linear-gradient(45deg, #10b981, #059669);
  color: white;
  border-radius: 8px;
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

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  opacity: 0.5;
}

.empty-state h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #374151;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .title-section {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .filters {
    grid-template-columns: 1fr;
  }
  
  .filter-actions {
    justify-content: stretch;
  }
  
  .filter-actions button {
    flex: 1;
  }
  
  .table-container {
    overflow-x: auto;
  }
  
  .data-table {
    font-size: 12px;
  }
  
  .data-table td {
    padding: 12px 8px;
  }
}
</style>