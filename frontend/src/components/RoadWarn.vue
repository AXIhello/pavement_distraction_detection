<template>
  <div class="table-wrapper">
    <div class="title">路障告警</div>

    <!-- 状态切换按钮 -->
    <div class="status-toggle">
      <button
        @click="activeTab = 'unprocessed'"
        :class="['status-btn', { active: activeTab === 'unprocessed' }]"
      >未处理</button>
      <button
        @click="activeTab = 'processed'"
        :class="['status-btn', { active: activeTab === 'processed' }]"
      >已处理</button>
    </div>

    <!-- 筛选区 -->
    <div class="filters">
      <div class="filter-group">
        <label class="filter-label">
          <span class="label-text">类型:</span>
          <select v-model="filterType" class="filter-select">
            <option value="">全部</option>
            <option v-for="type in uniqueTypes" :key="type" :value="type">{{ type }}</option>
          </select>
        </label>

        <label class="filter-label">
          <span class="label-text">日期:</span>
          <input type="date" v-model="filterDate" class="filter-input" />
        </label>

        <button @click="clearFilters" class="clear-btn">
          <span class="btn-icon">🗑️</span> 清除筛选
        </button>
      </div>
    </div>

    <!-- 表格展示 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th @click="sortBy('type')" class="sortable-header">
              <div class="header-content">
                <span>类型</span>
                <span v-if="sortKey === 'type'" class="sort-indicator">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </div>
            </th>
            <th @click="sortBy('date')" class="sortable-header">
              <div class="header-content">
                <span>告警时间</span>
                <span v-if="sortKey === 'date'" class="sort-indicator">{{ sortOrder === 1 ? '▲' : '▼' }}</span>
              </div>
            </th>
            <th class="action-header">查看详情</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in displayedData" :key="item.id" class="data-row">
            <td class="type-cell"><span class="type-tag">{{ item.type }}</span></td>
            <td class="date-cell">{{ item.date }}</td>
            <td class="action-cell">
              <button @click="viewDetails(item)" class="detail-btn">
                <span class="btn-icon">👁️</span> 查看详情
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

    <!-- 分页器 -->
    <el-pagination
      v-model:current-page="currentPage"
      :page-size="perPage"
      :total="total"
      layout="total, prev, pager, next"
      background
      style="margin: 24px auto; text-align: center"
      @current-change="fetchData"
    />
  </div>
</template>


<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { ElMessageBox, ElMessage } from 'element-plus'

const activeTab = ref('unprocessed')
const warnings = ref([])

const sortKey = ref('')
const sortOrder = ref(1)

const filterType = ref('')
const filterDate = ref('')

const currentPage = ref(1)
const perPage = 10
const total = ref(0)

// 拉取接口数据
async function fetchData() {
  try {
    const res = await axios.get('/api/logs_alerts/alerts', {
      params: {
        page: currentPage.value,
        per_page: perPage,
        type: filterType.value || undefined,
        status: activeTab.value === 'unprocessed' ? '活跃' : '已处理',
      }
    })
    warnings.value = res.data.alerts.map(item => ({
      id: item.alert_id,
      type: item.type,
      date: item.timestamp,
      status: item.status,
      raw: item
    }))
    total.value = res.data.total
  } catch (e) {
    console.error('获取数据失败', e)
    ElMessage.error('获取告警信息失败')
  }
}

// 类型选项
const uniqueTypes = computed(() => {
  const set = new Set()
  warnings.value.forEach(w => set.add(w.type))
  return [...set]
})

// 排序 & 过滤展示
const displayedData = computed(() => {
  let result = warnings.value
  if (filterDate.value) {
    result = result.filter(item => item.date.startsWith(filterDate.value))
  }
  if (filterType.value) {
    result = result.filter(item => item.type === filterType.value)
  }

  if (!sortKey.value) return result

  return [...result].sort((a, b) => {
    if (a[sortKey.value] < b[sortKey.value]) return -1 * sortOrder.value
    if (a[sortKey.value] > b[sortKey.value]) return 1 * sortOrder.value
    return 0
  })
})

// 排序切换
function sortBy(key) {
  if (sortKey.value === key) {
    sortOrder.value *= -1
  } else {
    sortKey.value = key
    sortOrder.value = 1
  }
}

// 查看详情：调用播放接口
async function viewDetails(item) {
  try {
    const res = await axios.get(`/api/logs_alerts/alerts/playback/${item.id}`)
    const { alert_info, media_url } = res.data
    await ElMessageBox.alert(
      `类型: ${alert_info.type}<br>描述: ${alert_info.description}<br>媒体: ${media_url}`,
      '告警详情',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确定'
      }
    )
  } catch (e) {
    console.error('查看详情失败', e)
    ElMessage.error('查看详情失败')
  }
}

function clearFilters() {
  filterType.value = ''
  filterDate.value = ''
  currentPage.value = 1
  fetchData()
}

// 监听切换状态、筛选变化时自动刷新
watch([activeTab, filterType, filterDate], () => {
  currentPage.value = 1
  fetchData()
})

onMounted(fetchData)
</script>

<style scoped>
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