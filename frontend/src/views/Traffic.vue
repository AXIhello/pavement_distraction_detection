<template>
  <Navigation ref="navRef" />

  <div class="main-layout">
    <div class="content">
      <!-- 左侧 -->
      <aside class="sidebar left">
        <div class="card">
          <div class="card-title"><span class="icon">🕒</span> UTC时间查询</div>
        </div>
        <div class="card">
          <div class="card-title"><span class="icon">📈</span> 按时间查询</div>
          <form @submit.prevent="onTimeQuery">
            <div class="form-group">
              <label>请输入起始时间:</label>
              <input type="datetime-local" v-model="startTime" step="1" required />
            </div>
            <div class="form-group">
              <label>请输入终止时间:</label>
              <input type="datetime-local" v-model="endTime" step="1" required />
            </div>
            <button type="submit">提交</button>
          </form>
        </div>
        <div class="card">
          <div class="card-title"><span class="icon">🚗</span> 按车辆查询</div>
          <form @submit.prevent="onCarQuery">
            <div class="form-group">
              <label>请输入起始时间:</label>
              <input type="datetime-local" v-model="carStartTime" step="1" required />
            </div>
            <div class="form-group">
              <label>请输入终止时间:</label>
              <input type="datetime-local" v-model="carEndTime" step="1" required />
            </div>
            <div class="form-group">
              <label>请输入车牌标识:</label>
              <input v-model="carPlate" placeholder="请输入车牌标识(如15053110001)" required />
            </div>
            <button type="submit">提交</button>
          </form>
        </div>
      </aside>

      <!-- 右侧地图 -->
      <main class="map-main">
        <div class="map-title">
          <h2>地图</h2>
        </div>

        <BaiDuMap ref="baiDuMapRef" />

        <!-- 地图下方按钮 -->
        <div class="map-analysis-btn">
          <button @click="showAnalysis = !showAnalysis">
            {{ showAnalysis ? '隐藏分析数据' : '显示分析数据' }}
          </button>
        </div>
      </main>
    </div>
  </div>

  <!-- 分析数据区域 -->
  <div class="analysis-footer" v-if="showAnalysis">
    <div class="card analysis-card">
      <div class="card-title"><span class="icon">📊</span> 分析数据</div>

      <!-- 分析布局：左按钮 + 右内容 -->
      <div class="analysis-body">
        <!-- 左侧按钮栏 -->
        <div class="analysis-sidebar">
          <button @click="activeAnalysis = 'population'">人口分布</button>
          <button @click="activeAnalysis = 'flow'">客流量</button>
          <button @click="activeAnalysis = 'weather'">天气与客流</button>
          <button @click="activeAnalysis = 'speed'">道路速度</button>
        </div>

        <!-- 右侧内容区域 -->
        <div class="analysis-content">
          <div v-if="activeAnalysis === 'population'">
            <p>人口分布分析结果内容...</p>
          </div>
          <div v-else-if="activeAnalysis === 'flow'">
            <p>客流量分析结果内容...</p>
          </div>
          <div v-else-if="activeAnalysis === 'weather'">
            <p>天气与客流关系分析结果内容...</p>
          </div>
          <div v-else-if="activeAnalysis === 'speed'">
            <p>道路速度分析结果内容...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import BaiDuMap from '@/components/BaiDuMap.vue'
import Navigation from '@/components/Navigation.vue'
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const baiDuMapRef = ref(null)
const router = useRouter()

const startTime = ref('2013-09-12T00:00:00')
const endTime = ref('2013-09-12T00:00:00')
const carStartTime = ref('2013-09-12T00:00:00')
const carEndTime = ref('2013-09-12T00:00:00')
const carPlate = ref('')

const showAnalysis = ref(false)
const activeAnalysis = ref('population')

async function onTimeQuery() {
  try {
    baiDuMapRef.value?.showPoints([])
    const response = await fetch(`/api/points/?start_time=${encodeURIComponent(startTime.value)}&end_time=${encodeURIComponent(endTime.value)}`)
    const data = await response.json()
    baiDuMapRef.value?.showPoints(data)
  } catch (error) {
    alert('查询失败')
  }
}

async function onCarQuery() {
  try {
    baiDuMapRef.value?.showPoints([])
    const response = await fetch(`/api/car_points/?commaddr=${encodeURIComponent(carPlate.value)}&start_time=${encodeURIComponent(carStartTime.value)}&end_time=${encodeURIComponent(carEndTime.value)}`)
    const data = await response.json()
    baiDuMapRef.value?.showPoints(data)
  } catch (error) {
    alert('查询失败')
  }
}

async function onShowHeatmap() {
  try {
    baiDuMapRef.value?.showPoints([])
    const response = await fetch(`/api/pickup_points/?time=${encodeURIComponent(startTime.value)}`)
    const data = await response.json()
    if (typeof baiDuMapRef.value?.showHeatmap === 'function') {
      baiDuMapRef.value.showHeatmap(data)
    } else {
      alert('地图组件未实现 showHeatmap 方法')
    }
  } catch (error) {
    alert('热力图查询失败: ' + (error?.message || error))
  }
}
</script>

<style>
.main-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.content {
  flex: 1;
  display: flex;
  min-height: 0;
}
.sidebar {
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem 1rem;
  box-sizing: border-box;
  padding-top: 100px;
}
.map-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}
.map-toolbar {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}
.map-analysis-btn {
  padding: 1rem;
  text-align: center;
}
.card {
  background: #efdb9384;
  border-radius: 8px;
  padding: 1.2rem 1rem;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.card-title {
  font-size: 1.1rem;
  font-weight: bold;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.icon {
  font-size: 1.2rem;
}
input[type="datetime-local"], input[type="text"] {
  width: 100%;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  border: none;
  outline: none;
  margin-bottom: 0.5rem;
}
button {
  margin: 0.3rem 0;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: none;
  background: #000000;
  color: #fff;
  cursor: pointer;
  width: 100%;
  transition: background 0.2s;
}
button:hover {
  background: #5d5d5d;
}
.heatmap-btn {
  background: #ff9800;
  color: #fff;
  border-radius: 4px;
  padding: 0.5rem 1.2rem;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: background 0.2s;
}
.analysis-footer {
  padding: 1rem;
}

/* 分析数据布局样式 */
.analysis-body {
  display: flex;
  gap: 1rem;
}
.analysis-sidebar {
  width: 140px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.analysis-sidebar button {
  background: #000000;
  color: white;
  border-radius: 4px;
  border: none;
  padding: 0.5rem 1rem;
  cursor: pointer;
  text-align: left;
  transition: background 0.2s;
}
.analysis-sidebar button:hover {
  background: #003d73;
}
.analysis-sidebar button:active {
  background: #002a4d;
}
.analysis-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 6px;
  min-height: 150px;
}

.map-title {
  padding: 1rem 1.5rem 0 1.5rem;
}
.map-title h2 {
  font-size: 1.4rem;
  color: #333;
  margin: 0;
}
</style>