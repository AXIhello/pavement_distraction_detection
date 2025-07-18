<template>
  <Navigation ref="navRef" />

  <div class="main-layout">
    <div class="content">
      <!-- 左侧 -->
      <aside class="sidebar left">
        <div class="card utc-time-card">
          <div class="card-title time-query-title">
            UTC时间查询
            <button @click="showTimeConvert = true" class="icon-btn time-convert-btn" title="时间转换">
              <span class="icon-clock">🕒</span>
            </button>
          </div>
          <div style="font-size: 16px; color: #888; margin-top: 4px;">快点击旁边的时钟试试吧!</div>
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
              <input v-model="carPlate" placeholder="如15053110001" required />
            </div>
            <button type="submit">查询车辆轨迹</button>
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
          <button @click="onClearMapOverlays" style="margin-left: 10px;">
            清空地图
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
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'population' }"
            @click="onTogglePopulation"
          >人口分布</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'shandong' }"
            @click="onGoToShandong"

          >山东省地图</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'flow' }"
            @click="activeAnalysis = 'flow'"
          >客流量查询</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'weather' }"
            @click="activeAnalysis = 'weather'"
          >客流与天气</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'speed' }"
            @click="activeAnalysis = 'speed'"
          >道路速度</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'heatmap' }"
            @click="activeAnalysis = 'heatmap'"
          >上客点查询</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'dynamicHeatmap' }"
            @click="activeAnalysis = 'dynamicHeatmap'"
          >动态热力图</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'bus' }"
            @click="activeAnalysis = 'bus'"
          >载客车数量</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'orders' }"
            @click="activeAnalysis = 'orders'"
          >路程的分析</button>
          <button
            :class="{ 'active-analysis-btn': activeAnalysis === 'orderStats' }"
            @click="activeAnalysis = 'orderStats'"
          >时间与距离</button>
        </div>

        <!-- 右侧内容区域 -->
        <div class="analysis-content">
          <div v-if="activeAnalysis === 'flow'">
            <form @submit.prevent="onQueryFlow">
              <div class="form-group">
                <label>起始时间：</label>
                <input type="datetime-local" v-model="flowStartTime" required />
              </div>
              <div class="form-group">
                <label>结束时间：</label>
                <input type="datetime-local" v-model="flowEndTime" required />
              </div>
              <div class="form-group">
                <label>时间间隔：</label>
                <input type="number" v-model="flowInterval" min="1" required style="width: 100px; display: inline-block;" />
                <span style="margin-left: 6px;">分钟</span>
              </div>
              <button type="submit">查询客流量</button>
            </form>
            <EchartsTable ref="flowChartRef" />
          </div>

          <div v-else-if="activeAnalysis === 'speed'">
            <form @submit.prevent="onQueryRoadSpeed">
              <div class="form-group">
                <label>查询时间：</label>
                <input type="datetime-local" v-model="speedQueryTime" required />
              </div>
              <button type="submit">查询道路速度</button>
            </form>
            <div class="info-text">
              <p style="color: #2C3E50;">💡 提示：查询后地图上将显示道路线条，颜色表示速度：<span style="color: #00cc00;">深绿色(快速)</span> | <span style="color: #CCCC00;">黄色(中等)</span> | <span style="color: #cc0000;">深红色(慢速)</span></p>
            </div>
          </div>
          <div v-else-if="activeAnalysis === 'heatmap'">
            <form @submit.prevent="onShowHeatmap">
              <div class="form-group">
                <label>查询时间：</label>
                <input type="datetime-local" v-model="heatmapQueryTime" required />
              </div>
              <button type="submit">查询上客点热力图</button>
            </form>
            <div class="info-text">
              <p style="color: #2C3E50;">💡 提示：查询后将显示该时间点后15分钟内的上客点热力图，颜色越深表示上客点越密集。</p>
            </div>
          </div>
          <div v-else-if="activeAnalysis === 'dynamicHeatmap'">
            <form @submit.prevent="onShowDynamicHeatmap">
              <div class="form-group">
                <label>起始时间：</label>
                <input type="datetime-local" v-model="dynamicHeatmapStartTime" required />
              </div>
              <div class="form-group">
                <label>结束时间：</label>
                <input type="datetime-local" v-model="dynamicHeatmapEndTime" required />
              </div>
              <div class="form-group">
                <label>时间间隔：</label>
                <select v-model="dynamicHeatmapInterval" required>
                  <option value="15">15分钟</option>
                  <option value="30">30分钟</option>
                  <option value="60">1小时</option>
                  <option value="120">2小时</option>
                  <option value="240">4小时</option>
                </select>
              </div>
              <button type="submit">显示动态热力图</button>
            </form>
            <div class="info-text">
              <p>💡 提示：点击"显示动态热力图"后，地图右上角会出现控制面板，可以手动切换不同时段的热力图显示。</p>
            </div>
          </div>
          <div v-if="activeAnalysis === 'bus'">
            <form @submit.prevent="onQueryBusCount">
              <label>起始时间：</label>
              <input type="datetime-local" v-model="busStartTime" required />
              <label>结束时间：</label>
              <input type="datetime-local" v-model="busEndTime" required />
              <label>间隔时间：</label>
              <select v-model="busInterval" required>
                <option value="15">15分钟</option>
                <option value="30">30分钟</option>
                <option value="60">1小时</option>
              </select>
              <button type="submit">查询载客车数量</button>
            </form>
            <EchartsTable ref="busChartRef" />
          </div>
          <div v-else-if="activeAnalysis === 'weather'">
            <form @submit.prevent="onQueryWeatherFlow">
              <div class="form-group">
                <label>起始时间：</label>
                <input type="datetime-local" v-model="weatherStartTime" required />
              </div>
              <div class="form-group">
                <label>结束时间：</label>
                <input type="datetime-local" v-model="weatherEndTime" required />
              </div>
              <div class="form-group">
                <label>时间间隔：</label>
                <select v-model="weatherInterval" required>
                  <option value="60">1小时</option>
                  <option value="120">2小时</option>
                  <option value="180">3小时</option>
                  <option value="240">4小时</option>
                  <option value="1440">1天</option>
                </select>
              </div>
              <button type="submit">查询客流与天气</button>
            </form>
            <EchartsTable ref="weatherChartRef" />
          </div>
          <div v-else-if="activeAnalysis === 'orders'">
            <form @submit.prevent="onQueryOrderDistribution">
              <div class="form-group">
                <label>起始时间：</label>
                <input type="datetime-local" v-model="orderStartTime" step="1" required />
              </div>
              <div class="form-group">
                <label>结束时间：</label>
                <input type="datetime-local" v-model="orderEndTime" step="1" required />
              </div>
              <button type="submit">查询订单占比</button>
            </form>
            <EchartsTable ref="orderChartRef" />
          </div>
          <div v-else-if="activeAnalysis === 'orderStats'">
            <form @submit.prevent="onQueryOrderStats">
              <div class="form-group">
                <label>起始时间：</label>
                <input type="datetime-local" v-model="statStartTime" required />
              </div>
              <div class="form-group">
                <label>结束时间：</label>
                <input type="datetime-local" v-model="statEndTime" required />
              </div>
              <div class="form-group">
                <label>时间间隔(分钟)：</label>
                <input type="number" v-model="statInterval" min="1" required />
              </div>
              <button type="submit">查询订单统计</button>
            </form>
            <EchartsTable ref="statChartRef" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 时间转换弹窗 -->
  <div v-if="showTimeConvert" class="time-convert-dialog" style="z-index:2000;">
    <div>
      <label>UTC时间戳：</label>
      <input v-model="utc" @input="utcToBeijing" placeholder="如 1721193600" />
    </div>
    <div>
      <label>北京时间：</label>
      <input v-model="beijing" @input="beijingToUtc" placeholder="如 2024-07-17 08:00:00" />
    </div>
    <div style="font-size:12px;color:#888;margin-top:4px;">
      支持互转，输入一个自动转换另一个
    </div>
    <button @click="showTimeConvert = false" class="close-btn">关闭</button>
  </div>
</template>

<script setup>
import BaiDuMap from '@/components/BaiDuMap.vue'
import Navigation from '@/components/Navigation.vue'
import { useRouter } from 'vue-router'
import { ref } from 'vue'
import EchartsTable from '@/components/EchartsTable.vue'

const baiDuMapRef = ref(null)

const startTime = ref('2013-09-12T00:00:00')
const endTime = ref('2013-09-12T00:00:00')
const carStartTime = ref('2013-09-12T00:00:00')
const carEndTime = ref('2013-09-12T00:00:00')
const carPlate = ref('')

const showAnalysis = ref(false)
const activeAnalysis = ref('') // 初始无激活

const busStartTime = ref('2013-09-12T00:00:00')
const busEndTime = ref('2013-09-12T00:15:00')
const busInterval = ref('15')
const busChartRef = ref(null)

const weatherStartTime = ref('2013-09-12T08:00:00')
const weatherEndTime = ref('2013-09-12T18:00:00')
const weatherInterval = ref('60')
const weatherChartRef = ref(null)

const flowStartTime = ref('2013-09-12T00:00:00')
const flowEndTime = ref('2013-09-12T00:15:00')
const flowChartRef = ref(null)
const flowInterval = ref('30')

const dynamicHeatmapStartTime = ref('2013-09-12T08:00:00')
const dynamicHeatmapEndTime = ref('2013-09-12T12:00:00')
const dynamicHeatmapInterval = ref('30')

const orderStartTime = ref('2013-09-12T00:00:00')
const orderEndTime = ref('2013-09-12T23:59:59')
const orderChartRef = ref(null)

const statStartTime = ref('2013-09-12T00:00:00')
const statEndTime = ref('2013-09-12T12:00:00')
const statInterval = ref('60')
const statChartRef = ref(null)

const speedQueryTime = ref('2013-09-12T08:00:00')
const heatmapQueryTime = ref('2013-09-12T08:00:00')

const showTimeConvert = ref(false)
const utc = ref('')
const beijing = ref('')

function utcToBeijing() {
  if (!utc.value) {
    beijing.value = ''
    return
  }
  const ts = parseInt(utc.value)
  if (!isNaN(ts)) {
    const date = new Date(ts * 1000)
    // 北京时间 = UTC+8
    date.setHours(date.getHours() + 8)
    beijing.value = date.toISOString().replace('T', ' ').substring(0, 19)
  }
}

function beijingToUtc() {
  if (!beijing.value) {
    utc.value = ''
    return
  }
  const date = new Date(beijing.value.replace(' ', 'T'))
  if (!isNaN(date.getTime())) {
    // UTC = 北京时间 - 8小时
    date.setHours(date.getHours() - 8)
    utc.value = Math.floor(date.getTime() / 1000)
  }
}

async function onTimeQuery() {
  try {
    const response = await fetch(
      `/api/traffic_analysis/points/?start_time=${encodeURIComponent(startTime.value)}&end_time=${encodeURIComponent(endTime.value)}`
    );
    const data = await response.json();
    console.log('接口返回数据:', data)
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showPoints === 'function') {
      baiDuMapRef.value.showPoints(data);
    }
  } catch (error) {
    console.error('查询失败', error)
    alert('查询失败');
  }
}

async function onCarQuery() {
  try {
    // 先清空地图上的标识点
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showPoints === 'function') {
      baiDuMapRef.value.showPoints([]);
    }

    // 2. 切换地图样式为浅色版本（在请求数据前就切换）
    if (baiDuMapRef.value && typeof baiDuMapRef.value.setMapStyle === 'function') {
      baiDuMapRef.value.setMapStyle('light');
      console.log('✅ 已切换为浅色地图样式（车辆轨迹查询）');
    }

    // 3. 构建请求参数
    const params = new URLSearchParams({
      commaddr: carPlate.value,
      start_time: carStartTime.value,
      end_time: carEndTime.value
    });

    console.log('车辆轨迹查询参数:', params.toString());

    // 4. 请求数据
    const response = await fetch(`/api/traffic_analysis/car_points/?${params.toString()}`);
    const data = await response.json();

    console.log('车辆轨迹返回数据:', data);

    // 5. 显示车辆轨迹
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showVehicleTrack === 'function') {
      baiDuMapRef.value.showVehicleTrack(data);
    } else {
      alert('地图组件未实现 showVehicleTrack 方法');
    }
  } catch (error) {
    console.error('车辆轨迹查询失败:', error);
    alert('车辆轨迹查询失败: ' + (error && error.message ? error.message : error));
  }
}

async function onShowHeatmap() {
  try {
    // 先清空地图上的标识点
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showPoints === 'function') {
      baiDuMapRef.value.showPoints([]);
    }

    // 2. 切换地图样式为浅色版本（在请求数据前就切换）
    if (baiDuMapRef.value && typeof baiDuMapRef.value.setMapStyle === 'function') {
      baiDuMapRef.value.setMapStyle('light');
      console.log('✅ 已切换为浅色地图样式（热力图查询）');
    }

    // 3. 构建请求参数
    const params = new URLSearchParams({
      time: heatmapQueryTime.value
    });

    console.log('热力图查询参数:', params.toString());

    // 4. 请求数据
    const response = await fetch(`/api/traffic_analysis/pickup_points/?${params.toString()}`);
    const data = await response.json();
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showHeatmap === 'function') {
      baiDuMapRef.value.showHeatmap(data);
    } else {
      alert('地图组件未实现 showHeatmap 方法');
    }
  } catch (error) {
    console.error('热力图查询失败:', error);
    alert('热力图查询失败: ' + (error && error.message ? error.message : error));
  }
}

async function onShowDynamicHeatmap() {
  try {
    // 先清空地图上的标识点
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showPoints === 'function') {
      baiDuMapRef.value.showPoints([]);
    }

    // 2. 切换地图样式为浅色版本（在请求数据前就切换）
    if (baiDuMapRef.value && typeof baiDuMapRef.value.setMapStyle === 'function') {
      baiDuMapRef.value.setMapStyle('light');
      console.log('✅ 已切换为浅色地图样式（动态热力图）');
    }

    // 3. 构建请求参数
    const params = new URLSearchParams({
      start_time: dynamicHeatmapStartTime.value,
      end_time: dynamicHeatmapEndTime.value,
      time_interval: dynamicHeatmapInterval.value
    });

    console.log('动态热力图请求参数:', params.toString());

    // 4. 请求数据
    const response = await fetch(`/api/traffic_analysis/dynamic_heatmap/?${params.toString()}`);
    const data = await response.json();

    console.log('动态热力图返回数据:', data);

    // 5. 显示动态热力图
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showDynamicHeatmap === 'function') {
      baiDuMapRef.value.showDynamicHeatmap(data);
    } else {
      alert('地图组件未实现 showDynamicHeatmap 方法');
    }
  } catch (error) {
    console.error('动态热力图查询失败:', error);
    alert('动态热力图查询失败: ' + (error && error.message ? error.message : error));
  }
}

async function onQueryFlow() {
  try {
    // 直接使用本地时间格式，避免UTC转换
    const params = new URLSearchParams({
      start_time: flowStartTime.value,
      end_time: flowEndTime.value,
      interval: flowInterval.value
    })

    const response = await fetch(`/api/traffic_analysis/flow/?${params.toString()}`)
    const result = await response.json()

    if (result.time_slots && flowChartRef.value) {
      const option = {
        title: {
          text: '客流量分析',
          subtext: `时间间隔: ${flowInterval.value}分钟`
        },
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            return `${params[0].axisValue}<br/>订单数量: ${params[0].value}`
          }
        },
        xAxis: {
          type: 'category',
          data: result.time_slots.map(slot => slot.start_time.slice(11, 16)) // 只显示时:分
        },
        yAxis: {
          type: 'value',
          name: '订单数量',
          minInterval: 1
        },
        series: [{
          name: '订单数量',
          type: 'line',
          data: result.time_slots.map(slot => slot.order_count),
          itemStyle: {
            color: '#5470c6',
            borderColor: '#ffffff',
            borderWidth: 2,
            shadowBlur: 5,
            shadowColor: 'rgba(0,0,0,0.3)'
          },
          symbolSize: 8,
          lineStyle: { width: 3 },
          smooth: true
        }]
      }

      flowChartRef.value.setChartData(option)
      console.log('客流量图表已更新:', option)
    } else {
      console.error('返回数据格式错误:', result)
      alert('数据格式错误')
    }
  } catch (error) {
    console.error('查询失败:', error)
    alert('查询失败')
  }
}

async function onQueryBusCount() {
  console.log('onQueryBusCount 被调用')
  const params = new URLSearchParams({
    start_time: busStartTime.value,
    end_time: busEndTime.value,
    interval: busInterval.value
  })
  const response = await fetch(`/api/traffic_analysis/passenger_count/?${params.toString()}`)
  const data = await response.json()
  // 处理数据并渲染ECharts
  if (busChartRef.value && typeof busChartRef.value.setChartData === 'function') {
    // 生成时间区间标签，格式如 "00:00-00:15"
    const timeLabels = data.time_slots.map((slot, index) => {
      const startTime = slot.start_time.slice(11, 16) // 获取时:分
      // 根据时间间隔计算结束时间
      const intervalMinutes = parseInt(busInterval.value)
      const startDate = new Date(slot.start_time)
      const endDate = new Date(startDate.getTime() + intervalMinutes * 60 * 1000)
      const endTime = endDate.toTimeString().slice(0, 5) // 获取时:分
      return `${startTime}-${endTime}`
    })

    const option = {
      title: { text: '载客车数量-时段折线图' },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          return `${params[0].axisValue}<br/>载客车数量: ${params[0].value}`
        }
      },
      xAxis: {
        type: 'category',
        data: timeLabels,
        axisLabel: {
          rotate: 35,  // 标签旋转35度
          interval: 0, // 显示所有标签
          textStyle: {
            fontSize: 12
          }
        }
      },
      yAxis: { type: 'value', name: '载客车数量' },
      series: [{
        name: '载客车数量',
        type: 'line',
        data: data.time_slots.map(slot => slot.passenger_car_count),
        itemStyle: { color: '#5470c6' },
        lineStyle: { width: 3 },
        smooth: true
      }]
    }
    console.log('option:', option)
    busChartRef.value.setChartData(option)
    console.log('setChartData 被调用', option)
  }
}

async function onQueryWeatherFlow() {
  try {
    const params = new URLSearchParams({
      start_time: weatherStartTime.value,
      end_time: weatherEndTime.value,
      interval: weatherInterval.value
    })

    const response = await fetch(`/api/traffic_analysis/weather_flow/?${params.toString()}`)
    const result = await response.json()

    if (result.data && weatherChartRef.value) {
      // 构建多轴折线图配置，显示更多天气信息
      const option = {
        title: {
          text: '客流与天气关系图',
          subtext: `时间范围: ${result.start_time?.slice(11, 16)} - ${result.end_time?.slice(11, 16)}`
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          formatter: function(params) {
            let html = params[0].axisValue + '<br/>';
            params.forEach(param => {
              html += param.marker + param.seriesName + ': ' + param.value;
              if (param.seriesName === '温度') html += '°C';
              if (param.seriesName === '湿度') html += '%';
              if (param.seriesName === '风速') html += 'm/s';
              if (param.seriesName === '降水量') html += 'mm';
              html += '<br/>';
            });
            return html;
          }
        },
        legend: {
          data: ['客流量', '温度', '湿度', '风速', '降水量'],
          top: 30,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          top: 80,
          bottom: 60,
          left: 60,
          right: 120
        },
        xAxis: {
          type: 'category',
          data: result.data.map(item => item.time),
          axisLabel: {
            rotate: 35,
            interval: 0
          }
        },
        yAxis: [
          {
            type: 'value',
            name: '客流量',
            position: 'left',
            axisLine: { show: true },
            axisLabel: { color: '#5470c6' }
          },
          {
            type: 'value',
            name: '温度(°C)',
            position: 'right',
            offset: 0,
            axisLine: { show: true },
            axisLabel: { color: '#ff6b6b' }
          },
          {
            type: 'value',
            name: '湿度(%)',
            position: 'right',
            offset: 40,
            axisLine: { show: true },
            axisLabel: { color: '#91cc75' }
          },
          {
            type: 'value',
            name: '风速(m/s)',
            position: 'right',
            offset: 80,
            axisLine: { show: true },
            axisLabel: { color: '#fac858' }
          }
        ],
        series: [
          {
            name: '客流量',
            type: 'line',
            yAxisIndex: 0,
            data: result.data.map(item => item.passenger_flow),
            lineStyle: { width: 3 },
            itemStyle: {
              color: '#5470c6',
              borderColor: '#ffffff',
              borderWidth: 2,
              shadowBlur: 5,
              shadowColor: 'rgba(0,0,0,0.3)'
            },
            symbolSize: 8,
            smooth: true
          },
          {
            name: '温度',
            type: 'line',
            yAxisIndex: 1,
            data: result.data.map(item => item.weather.temperature),
            lineStyle: { color: '#ff6b6b', width: 2 },
            itemStyle: {
              color: '#ff6b6b',
              borderColor: '#ffffff',
              borderWidth: 2,
              shadowBlur: 5,
              shadowColor: 'rgba(0,0,0,0.3)'
            },
            symbolSize: 8,
            smooth: true
          },
          {
            name: '湿度',
            type: 'line',
            yAxisIndex: 2,
            data: result.data.map(item => item.weather.humidity),
            lineStyle: { color: '#91cc75', width: 2 },
            itemStyle: {
              color: '#91cc75',
              borderColor: '#ffffff',
              borderWidth: 2,
              shadowBlur: 5,
              shadowColor: 'rgba(0,0,0,0.3)'
            },
            symbolSize: 8,
            smooth: true
          },
          {
            name: '风速',
            type: 'line',
            yAxisIndex: 3,
            data: result.data.map(item => item.weather.wind_speed),
            lineStyle: { color: '#fac858', width: 2 },
            itemStyle: {
              color: '#fac858',
              borderColor: '#ffffff',
              borderWidth: 2,
              shadowBlur: 5,
              shadowColor: 'rgba(0,0,0,0.3)'
            },
            symbolSize: 8,
            smooth: true
          },
          {
            name: '降水量',
            type: 'bar',
            yAxisIndex: 0,
            data: result.data.map(item => item.weather.precip),
            itemStyle: {
              color: '#73c0de',
              opacity: 0.6
            },
            barWidth: '60%'
          }
        ]
      }

      weatherChartRef.value.setChartData(option)
      console.log('天气客流图表已更新:', option)
    } else {
      console.error('返回数据格式错误:', result)
      alert('数据格式错误')
    }
  } catch (error) {
    console.error('查询失败:', error)
    alert('查询失败')
  }
}

async function onQueryOrderDistribution() {
  try {
    // 直接使用本地时间格式，避免UTC转换
    const params = new URLSearchParams({
      start_time: orderStartTime.value,
      end_time: orderEndTime.value
    });

    const response = await fetch(`/api/traffic_analysis/order_distribution/?${params.toString()}`);
    const result = await response.json();

    if (result.categories && orderChartRef.value) {
      const option = {
        title: {
          text: '订单类型占比分析',
          subtext: `总订单数: ${result.total_orders}`
        },
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            return `${params.name}<br/>数量: ${params.value}<br/>占比: ${params.percent}%`
          }
        },
        legend: {
          orient: 'horizontal',
          top: 60,
          left: 'center',
          itemWidth: 24,
          itemHeight: 16,
          textStyle: {
            fontSize: 16
          }
        },
        series: [
          {
            name: '订单占比',
            type: 'pie',
            radius: '50%',
            center: ['60%', '50%'],
            data: result.categories.map(item => ({
              name: item.category_name,
              value: item.count,
              itemStyle: {
                color: getCategoryColor(item.category)
              }
            })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              formatter: function(params) {
                // params.name: 订单类型名
                // params.value: 数量
                // params.percent: 占比
                return `${params.name}: ${params.value}单 (${params.percent}%)`
              }
            }
          }
        ]
      }

      orderChartRef.value.setChartData(option)
      console.log('订单占比图表已更新:', option)
    } else {
      console.error('返回数据格式错误:', result)
      alert('数据格式错误')
    }
  } catch (error) {
    console.error('查询失败:', error)
    alert('查询失败')
  }
}

async function onQueryOrderStats() {
  try {
    // 直接使用本地时间格式，避免UTC转换
    const params = new URLSearchParams({
      start_time: statStartTime.value,
      end_time: statEndTime.value,
      interval: statInterval.value
    })
    const response = await fetch(`/api/traffic_analysis/order_stats/?${params.toString()}`)
    const result = await response.json()

    if (result.time_slots && statChartRef.value) {
      // 构建3D散点图数据
      const scatterData = []
      const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']

      result.time_slots.forEach((slot, slotIndex) => {
        const timeLabel = slot.start_time.slice(11, 16) // 获取时:分作为Z轴标签
        const color = colors[slotIndex % colors.length]

        // 处理每个时段内的订单数据
        if (slot.orders && slot.orders.length > 0) {
          // 如果有详细的订单数据，使用实际数据
          slot.orders.forEach(order => {
            scatterData.push([
              order.duration_minutes,  // X轴：耗时
              order.distance_km,       // Y轴：距离
              slotIndex,               // Z轴：时段索引（数值）
              color                    // 颜色
            ])
          })
        } else {
          // 如果没有详细订单数据，使用统计数据的平均值作为示例点
          scatterData.push([
            slot.avg_duration_minutes || 0,  // X轴：平均耗时
            slot.avg_distance_km || 0,       // Y轴：平均距离
            slotIndex,                       // Z轴：时段索引（数值）
            color                            // 颜色
          ])
        }
      })

      const option = {
        title: {
          text: '订单耗时-距离3D散点图',
          subtext: `时间范围: ${result.start_time?.slice(11, 16)} - ${result.end_time?.slice(11, 16)}`
        },
        tooltip: {
          formatter: function(params) {
            return `时段: ${params.value[2]}<br/>耗时: ${params.value[0]}分钟<br/>距离: ${params.value[1]}公里`
          }
        },
        legend: {
          data: ['订单分布'],
          top: 30
        },
        grid3D: {
          viewControl: {
            // 3D视角控制
            alpha: 20,
            beta: 40,
            distance: 200,
            autoRotate: false
          },
          light: {
            main: {
              intensity: 1.2
            },
            ambient: {
              intensity: 0.3
            }
          }
        },
        xAxis3D: {
          type: 'value',
          name: '耗时(分钟)',
          nameTextStyle: {
            color: '#333'
          }
        },
        yAxis3D: {
          type: 'value',
          name: '距离(公里)',
          nameTextStyle: {
            color: '#333'
          }
        },
        zAxis3D: {
          type: 'value',
          name: '时段',
          nameTextStyle: {
            color: '#333'
          },
          axisLabel: {
            formatter: function(value) {
              // 将数值映射回时间标签
              const timeLabels = result.time_slots.map(slot => slot.start_time.slice(11, 16))
              return timeLabels[Math.floor(value)] || value
            }
          }
        },
        series: [
          {
            name: '订单分布',
            type: 'scatter3D',
            data: scatterData,
            symbolSize: 8,
            itemStyle: {
              opacity: 0.8
            },
            emphasis: {
              itemStyle: {
                opacity: 1,
                symbolSize: 12
              }
            }
          }
        ]
      }

      console.log('3D散点图数据:', scatterData)
      console.log('3D散点图配置:', option)
      statChartRef.value.setChartData(option)
      console.log('3D散点图已更新')
    } else {
      alert('数据格式错误')
    }
  } catch (error) {
    console.error('查询失败:', error)
    alert('查询失败')
  }
}

function getCategoryColor(category) {
  const colors = {
    'short': '#588b71',   // 浅蓝 - 短途
    'medium': '#eae2cf',  // 浅绿 - 中途
    'long': '#d24f6b'     // 粉红 - 长途
  }
  return colors[category] || '#87CEEB'
}

function calculateOptimalInterval(startTime, endTime) {
  const start = new Date(startTime);
  const end = new Date(endTime);
  const diffHours = (end - start) / (1000 * 60 * 60);

  if (diffHours <= 3) return '15';
  if (diffHours <= 6) return '30';
  if (diffHours <= 12) return '60';
  if (diffHours <= 18) return '90';
  if (diffHours <= 24) return '120';
  if (diffHours <= 168) return '240';
  return '1440';
}

function onClearMapOverlays() {
  if (baiDuMapRef.value && typeof baiDuMapRef.value.clearMapOverlays === 'function') {
    baiDuMapRef.value.clearMapOverlays();
  }
}

// 人口显示
function onTogglePopulation() {
  baiDuMapRef.value?.togglePopulation()
  activeAnalysis.value = 'population'

  // 滚动到地图区域
  const mapMain = document.querySelector('.map-main')
  if (mapMain) {
    mapMain.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    })
  }
}

function onGoToShandong() {
  baiDuMapRef.value?.goToShandong()
  activeAnalysis.value = 'shandong'
}

async function onQueryRoadSpeed() {
  try {
    // 先清空地图上的标识点
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showPoints === 'function') {
      baiDuMapRef.value.showPoints([]);
    }

    //2. 先切换地图样式为浅色版本（在请求数据前就切换）
    if (baiDuMapRef.value && typeof baiDuMapRef.value.setMapStyle === 'function') {
      baiDuMapRef.value.setMapStyle('light');
      console.log('✅ 已切换为浅色地图样式');
    }

    // 3. 构建请求参数
    const params = new URLSearchParams({
      query_time: speedQueryTime.value
    });

    console.log('道路速度查询参数:', params.toString());

    const response = await fetch(`/api/traffic_analysis/road_speed/?${params.toString()}`);
    const data = await response.json();

    console.log('道路速度返回数据:', data);

    // 5. 绘制道路线条
    if (baiDuMapRef.value && typeof baiDuMapRef.value.showRoadSpeed === 'function') {
      baiDuMapRef.value.showRoadSpeed(data);
    } else {
      alert('地图组件未实现 showRoadSpeed 方法');
    }
  } catch (error) {
    console.error('道路速度查询失败:', error);
    alert('道路速度查询失败: ' + (error && error.message ? error.message : error));
  }
}
</script>

<style>
:root {
  font-size: 18px;
}
.analysis-content, .analysis-sidebar, .form-group, .info-text, .card, .analysis-footer {
  font-size: 18px;
}
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
.sidebar .card-title {
  font-size: 19px;
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
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px; /* 按钮间距 */
}
.map-analysis-btn button {
  width: auto;
  min-width: 120px;
  margin: 0;
}
.card {
  background: #efdb9384;
  color: #2C3E50;      /* 藏青色字体 */
  border-radius: 8px;
  padding: 1.21rem;
  box-shadow: 0 2px8px rgba(0,0,0,0.08);
}
.utc-time-card {
  padding: 0.8rem 1rem;
}
.card-title {
  font-size: 1.4rem;
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
  background: #bae686;
  color: #2C3E50;
  border-radius: 4px;
  border: none;
  padding: 0.5rem 1rem;
  cursor: pointer;
  text-align: center;
  font-size: 16px;
  margin-bottom: 8px;
  transition: background 0.2s, color 0.2s;
  font-weight: bold;
  box-shadow: none;
}
.analysis-sidebar button:hover {
  background: #bae686;
}
.analysis-sidebar button.active-analysis-btn {
  background: #395168 !important;
  color: #fff !important;
  font-weight: bold;
  text-align: center;
  box-shadow: 0 2px 8px rgba(44,62,80,0.10);
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

.info-text {
  margin-top: 1rem;
  padding: 0.8rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  border-left: 4px solid #007bff;
}

.info-text p {
  margin: 0;
  font-size: 0.9rem;
  color: #fff;
  line-height: 1.4;
}

.time-convert-dialog {
  position: fixed;
  left: 50%;
  top: 30%;
  transform: translate(-50%, -50%);
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.18);
  padding: 18px 20px 12px 20px;
  min-width: 260px;
}
.close-btn {
  margin-top: 10px;
  background: #f56c6c;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 4px 12px;
  cursor: pointer;
  float: right;
}
.icon-btn {
  background: none;
  border: none;
  font-size: 18px;
  margin-left: 6px;
  cursor: pointer;
  color: #409eff;
  transition: color 0.2s;
}
.icon-btn:hover {
  color: #66b1ff;
}
.time-query-title {
  display: flex;
  align-items: center;         /* 垂直居中 */
  justify-content: space-between;
  font-weight: bold;
  font-size: 18px;
  color: #2C3E50;
  min-height: 44px;            /* 保证按钮能完整显示，且不会太高 */
}

.time-convert-btn {
  margin-left: 10px;
  background: #2C3E50;
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(44,62,80,0.08);
}
.time-convert-btn:hover {
  background: #223A5E;
}
.icon-clock {
  color: #fff;
  font-size: 18px;
  line-height: 1;
}
.analysis-card .card-title {
  font-size: 22px;
}
</style>
