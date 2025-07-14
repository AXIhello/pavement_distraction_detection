<template>
  <div id="mapContainer"></div>
</template>

<script setup>
import { onMounted } from 'vue'

const BMAP_AK = '08cA2cvSV7s3cXQvcKEoyp23ssubn8np'
let map = null
let view = null
let pointLayer = null
let heatmapLayer = null

function loadBMapGL() {
  return new Promise((resolve, reject) => {
    if (window.BMapGL) return resolve()
    window.onBMapCallback = () => resolve()
    const script = document.createElement('script')
    script.src = `https://api.map.baidu.com/api?v=1.0&type=webgl&ak=${BMAP_AK}&callback=onBMapCallback`
    script.onerror = () => reject(new Error('❌ 百度地图脚本加载失败'))
    document.head.appendChild(script)
  })
}

function loadMapVGL() {
  return new Promise((resolve, reject) => {
    if (window.mapvgl) return resolve()
    const script1 = document.createElement('script')
    script1.src = 'https://unpkg.com/mapvgl/dist/mapvgl.min.js'
    script1.onload = () => {
      const script2 = document.createElement('script')
      script2.src = 'https://unpkg.com/mapvgl/dist/mapvgl.threelayers.min.js'
      script2.onload = () => resolve()
      script2.onerror = () => reject(new Error('❌ mapvgl.threelayers.min.js 加载失败'))
      document.head.appendChild(script2)
    }
    script1.onerror = () => reject(new Error('❌ mapvgl.min.js 加载失败'))
    document.head.appendChild(script1)
  })
}

function showPoints(data) {
  if (!window.mapvgl || !view) {
    alert('MapVGL 脚本或视图尚未加载完成，请稍后再试！')
    return
  }
  // 清除所有已存在的标识点图层
  view && view.getLayers && view.getLayers().forEach(layer => {
    if (layer instanceof window.mapvgl.PointLayer) {
      view.removeLayer(layer)
    }
  })
  if (!data || !data.length) return
  const pointData = data.map(item => ({
    geometry: { type: 'Point', coordinates: [item.lng, item.lat] }
  }))
  pointLayer = new window.mapvgl.PointLayer({
    color: 'rgba(255,0,0,0.8)',
    size: 20
  })
  view.addLayer(pointLayer)
  pointLayer.setData(pointData)
}

function showHeatmap(data) {
  if (!window.mapvgl || !view) {
    alert('mapvgl 脚本或视图尚未加载完成，请稍后再试！');
    return;
  }
  // 清除所有点图层和热力图层
  if (view && view.getLayers) {
    view.getLayers().forEach(layer => {
      if (layer instanceof window.mapvgl.PointLayer || layer instanceof window.mapvgl.HeatmapLayer) {
        view.removeLayer(layer);
      }
    });
  }
  if (!data || !data.length) return;
  // 构造热力图数据
  const points = data.map(item => ({
    geometry: { type: 'Point', coordinates: [item.lng, item.lat] },
    count: 30 // 可自定义权重
  }));
  heatmapLayer = new window.mapvgl.HeatmapLayer({
    size: 60,
    max: 100,
    gradient: {
      0.25: 'rgb(0,0,255)',
      0.55: 'rgb(0,255,0)',
      0.85: 'yellow',
      1.0: 'red'
    }
  });
  view.addLayer(heatmapLayer);
  heatmapLayer.setData(points);
}
// eslint-disable-next-line no-undef
defineExpose({ showPoints, showHeatmap })

onMounted(async () => {
  try {
    await loadBMapGL()
    console.log('BMapGL loaded:', window.BMapGL) // 检查是否加载成功
    map = new window.BMapGL.Map('mapContainer')
    map.centerAndZoom(new window.BMapGL.Point(116.994917, 36.66123), 13)
    map.enableScrollWheelZoom(true)
    await loadMapVGL()
    console.log('mapvgl loaded:', window.mapvgl) // 检查是否加载成功
    view = new window.mapvgl.View({ map })
  } catch (e) {
    console.error('加载失败:', e)
    alert('地图加载失败: ' + e.message)
  }
})
</script>

<style scoped>
#mapContainer {
  width: 100%;
  height: 100%;
  min-height: 600px;
  flex: 1 1 0;
}
</style>
