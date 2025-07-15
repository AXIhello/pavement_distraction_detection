<template>
  <div>
    <!-- 头部导航组件 -->
    <Navigation ref="headerRef" />
    
    <!-- 主体内容容器，顶部预留导航高度 -->
    <div class="log-view" :style="{ paddingTop: headerHeight + 'px' }">
      <div class="container">
        <div class="header-section">
          <h2>
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14,2 14,8 20,8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10,9 9,9 8,9"></polyline>
            </svg>
            系统日志
          </h2>
          <div class="log-count">
            <span>共 {{ total }} 条记录</span>
          </div>
        </div>

        <!-- 筛选区 -->
        <div class="filters-card">
          <div class="filters-header">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46"></polygon>
            </svg>
            <span>筛选条件</span>
          </div>
          
          <div class="filters">
            <div class="filter-item">
              <label>日志级别</label>
              <select v-model="filters.level">
                <option value="">全部</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
                <option value="DEBUG">DEBUG</option>
              </select>
            </div>

            <div class="filter-item">
              <label>开始时间</label>
              <input type="datetime-local" v-model="filters.start_time" />
            </div>

            <div class="filter-item">
              <label>结束时间</label>
              <input type="datetime-local" v-model="filters.end_time" />
            </div>

            <div class="filter-actions">
              <button @click="onFilter" class="btn-primary">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
                筛选
              </button>
              <button @click="resetFilters" class="btn-secondary">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                  <path d="M3 3v5h5"></path>
                </svg>
                重置
              </button>
            </div>
          </div>
        </div>

        <!-- 日志表格 -->
        <div class="table-card">
          <div class="table-container" v-if="logs.length > 0">
            <table class="log-table">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>级别</th>
                  <th>消息</th>
                  <th>模块</th>
                  <th>文件路径</th>
                  <th>行号</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in logs" :key="log.id" class="log-row">
                  <td class="timestamp">{{ formatDate(log.timestamp) }}</td>
                  <td>
                    <span :class="['level-badge', getLevelClass(log.level)]">
                      {{ log.level }}
                    </span>
                  </td>
                  <td class="message">{{ log.message }}</td>
                  <td class="module">{{ log.module }}</td>
                  <td class="pathname">{{ log.pathname }}</td>
                  <td class="lineno">{{ log.lineno }}</td>
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
            <h3>暂无日志数据</h3>
            <p>尝试调整筛选条件或检查系统状态</p>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-card" v-if="totalPages > 1">
          <div class="pagination">
            <button :disabled="page === 1" @click="prevPage" class="page-btn">
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="15,18 9,12 15,6"></polyline>
              </svg>
              上一页
            </button>
            
            <div class="page-info">
              <span>第 {{ page }} 页 / 共 {{ totalPages }} 页</span>
            </div>
            
            <button :disabled="page === totalPages" @click="nextPage" class="page-btn">
              下一页
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9,18 15,12 9,6"></polyline>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import axios from 'axios'
import Navigation from '@/components/Navigation.vue'

const logs = ref([])
const page = ref(1)
const perPage = 10
const total = ref(0)

const filters = ref({
  level: '',
  start_time: '',
  end_time: ''
})

const headerRef = ref(null)
const headerHeight = ref(64) // 默认预估高度

// 格式化时间
function formatDate(ts) {
  if (!ts) return '-'
  const d = new Date(ts)
  return d.toLocaleString()
}

// 获取日志级别样式类
function getLevelClass(level) {
  const levelMap = {
    'INFO': 'info',
    'WARNING': 'warning',
    'ERROR': 'error',
    'DEBUG': 'debug'
  }
  return levelMap[level] || 'default'
}

// 重置筛选条件
function resetFilters() {
  filters.value = {
    level: '',
    start_time: '',
    end_time: ''
  }
  page.value = 1
  fetchLogs()
}

async function fetchLogs() {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('http://localhost:8000/api/logs_alerts/logs', {
      headers: {
        Authorization: `Bearer ${token}`
      },
      params: {
        page: page.value,
        per_page: perPage,
        level: filters.value.level || undefined,
        start_time: filters.value.start_time || undefined,
        end_time: filters.value.end_time || undefined
      }
    })
    logs.value = response.data.logs || []
    total.value = response.data.total || 0
  } catch (err) {
    console.error('日志获取失败:', err)
    logs.value = []
    total.value = 0
  }
}

// 页数计算
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / perPage)))

// 筛选按钮点击
function onFilter() {
  page.value = 1
  fetchLogs()
}

// 翻页
function prevPage() {
  if (page.value > 1) {
    page.value--
  }
}
function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
  }
}

// 监听页码变化，自动刷新数据
watch(page, fetchLogs)

// 页面加载时先获取导航高度，然后加载日志数据
onMounted(async () => {
  await nextTick()
  if (headerRef.value?.$el) {
    headerHeight.value = headerRef.value.$el.offsetHeight
  }
  fetchLogs()
})
</script>

<style scoped>
.log-view {
  padding: 0;
  background: #fefdf9;
  min-height: calc(100vh - 64px);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-section h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1f2937;
  font-size: 28px;
  font-weight: 700;
  margin: 0;
}

.log-count {
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

.filter-item select,
.filter-item input {
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  background: white;
  font-size: 14px;
  transition: all 0.3s ease;
}

.filter-item select:focus,
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

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  background: linear-gradient(135deg, #00040a 0%, #1a1a2e 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 4, 10, 0.3);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #ebba25 0%, #f4d03f 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(235, 186, 37, 0.4);
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

.table-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 24px;
}

.table-container {
  overflow-x: auto;
}

.log-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 14px;
}

.log-table th {
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

.log-table th:first-child {
  border-top-left-radius: 0;
}

.log-table th:last-child {
  border-top-right-radius: 0;
}

.log-row {
  transition: all 0.3s ease;
  cursor: pointer;
}

.log-row:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  transform: scale(1.01);
}

.log-table td {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.timestamp {
  font-family: 'Courier New', monospace;
  color: #6b7280;
  font-size: 12px;
  min-width: 140px;
}

.level-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.level-badge.info {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.level-badge.warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.level-badge.error {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
}

.level-badge.debug {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
}

.level-badge.default {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
}

.message {
  max-width: 300px;
  word-wrap: break-word;
  color: #374151;
  font-weight: 500;
}

.module {
  font-family: 'Courier New', monospace;
  color: #6b7280;
  font-size: 12px;
}

.pathname {
  font-family: 'Courier New', monospace;
  color: #6b7280;
  font-size: 12px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lineno {
  font-family: 'Courier New', monospace;
  color: #6b7280;
  font-size: 12px;
  text-align: center;
}

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

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #374151;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

.pagination-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #000813 0%, #1a1a2e 100%);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 8, 19, 0.3);
}

.page-btn:disabled {
  background: linear-gradient(135deg, #ddb33d 0%, #f4d03f 100%);
  cursor: not-allowed;
  opacity: 0.6;
}

.page-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #030814 0%, #0f172a 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(3, 8, 20, 0.4);
}

.page-info {
  background: rgba(255, 255, 255, 0.8);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  color: #374151;
  font-weight: 500;
  border: 1px solid rgba(229, 231, 235, 0.5);
}

@media (max-width: 768px) {
  .container {
    padding: 16px;
  }
  
  .header-section {
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
  
  .pagination {
    flex-direction: column;
    gap: 16px;
  }
  
  .page-info {
    order: -1;
  }
}
</style>