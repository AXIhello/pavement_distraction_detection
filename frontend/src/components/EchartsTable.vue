<template>
  <div ref="chartRef" style="width:100%;height:400px;"></div>
</template>
<script setup>
import { ref, onMounted, onUnmounted, defineExpose } from 'vue'
import * as echarts from 'echarts'
// 导入3D扩展
import 'echarts-gl'

const chartRef = ref(null)
let chartInstance = null

function setChartData(option) {
  if (chartInstance) {
    // 清除之前的配置
    chartInstance.clear()
    // 设置新的配置
    chartInstance.setOption(option, true)
  }
}

defineExpose({ setChartData })

onMounted(() => { 
  chartInstance = echarts.init(chartRef.value) 
})

onUnmounted(() => { 
  chartInstance && chartInstance.dispose() 
})
</script>
