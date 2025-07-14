<template>
  <div class="log-view">
    <h2>系统日志</h2>

    <!-- 筛选区 -->
    <div class="filters">
      <label>日志级别:
        <select v-model="filters.level">
          <option value="">全部</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
          <option value="DEBUG">DEBUG</option>
        </select>
      </label>

      <label>开始时间:
        <input type="datetime-local" v-model="filters.start_time" />
      </label>

      <label>结束时间:
        <input type="datetime-local" v-model="filters.end_time" />
      </label>

      <button @click="fetchLogs">筛选</button>
    </div>

    <!-- 日志表格 -->
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
        <tr v-for="log in logs" :key="log.timestamp + log.message">
          <td>{{ log.timestamp }}</td>
          <td>{{ log.level }}</td>
          <td>{{ log.message }}</td>
          <td>{{ log.module }}</td>
          <td>{{ log.pathname }}</td>
          <td>{{ log.lineno }}</td>
        </tr>
      </tbody>
    </table>

    <!-- 分页 -->
    <div class="pagination">
      <button :disabled="page <= 1" @click="page--">上一页</button>
      <span>第 {{ page }} 页 / 共 {{ totalPages }} 页</span>
      <button :disabled="page >= totalPages" @click="page++">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

const logs = ref([])
const page = ref(1)
const perPage = 10
const total = ref(0)

const filters = ref({
  level: '',
  start_time: '',
  end_time: ''
})

// 获取日志
const fetchLogs = async () => {
  try {
    const response = await axios.get('/api/logs_alerts/logs', {
      params: {
        page: page.value,
        per_page: perPage,
        level: filters.value.level || undefined,
        start_time: filters.value.start_time || undefined,
        end_time: filters.value.end_time || undefined
      }
    })
    logs.value = response.data.logs
    total.value = response.data.total
  } catch (err) {
    console.error('日志获取失败:', err)
  }
}

// 页码变动时重新获取数据
watch(page, fetchLogs)

// 初始化加载
fetchLogs()

const totalPages = computed(() => Math.ceil(total.value / perPage))
</script>

<style scoped>
.log-view {
  padding: 20px;
  background: #fff;
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  align-items: center;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}
.log-table th, .log-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: left;
}
.log-table th {
  background-color: #f5f5f5;
}

.pagination {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>
