<template>
  <div id="mapContainer"></div>
  
  <!-- 动态热力图控制面板 -->
  <div v-if="showDynamicControls" class="dynamic-heatmap-controls">
    <div class="control-panel">
      <div class="time-display">{{ currentTimeSlot }}</div>
      <div class="control-buttons">
        <button @click="prevTimeSlot" :disabled="currentIndex === 0">◀ 上一时段</button>
        <button @click="nextTimeSlot" :disabled="currentIndex === timeSlotsData.length - 1">下一时段 ▶</button>
        <button @click="resetAnimation">🔄 重置</button>
        <button @click="isAutoPlaying ? stopAutoPlay() : startAutoPlay()" :class="{ 'playing': isAutoPlaying }">
          {{ isAutoPlaying ? '⏸️ 暂停' : '▶️ 自动播放' }}
        </button>
        <button @click="closeDynamicControls">✕ 关闭</button>
      </div>
      <div class="progress-info">
        {{ currentIndex + 1 }} / {{ timeSlotsData.length }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, defineExpose } from 'vue'

const BMAP_AK = '20FcUoEvheMHZMHXkCOdDIh5kEFm8gOo'
let map = null
let view = null
let pointLayer = null
let heatmapLayer = null
let roadSpeedLayer = null
let roadSpeedOverlays = [] // 保存道路速度覆盖物

// 人口数据提升到全局 - 2013年济南市分地区人口（单位：万人）
const districtPopulation = {
  '历下区': 56.25,
  '市中区': 59.53,
  '槐荫区': 39.00,
  '天桥区': 51.12,
  '历城区': 93.90,
  '长清区': 50.00,
  '平阴县': 37.16,
  '济阳县': 56.08,
  '商河县': 62.77,
  '章丘市': 101.86
}

// 人口显示开关
const showPopulation = ref(false)
let districtPolygons = [] // 保存所有区县 Polygon

// 动态热力图相关状态
const showDynamicControls = ref(false)
const timeSlotsData = ref([])
const currentIndex = ref(0)
const currentTimeSlot = ref('')
const isAutoPlaying = ref(false)
const autoPlayInterval = ref(null)

// 清空地图覆盖物的方法
function clearMapOverlays() {
  console.log('🗑️ 正在清除地图覆盖物')

  if (map) {
    map.clearOverlays()
    // 恢复默认地图样式
    setMapStyle('normal');
  }

  if (view) {
    console.log('🗑️ 调用 view.removeAllLayers() 清除所有 MapVGL 图层')
    view.removeAllLayers()
    console.log('🗑️ view.removeAllLayers() 执行完毕')
  }

  pointLayer = null
  heatmapLayer = null
  roadSpeedLayer = null
  
  // 清除道路速度覆盖物
  roadSpeedOverlays.forEach(overlay => {
    if (map && map.removeOverlay) {
      map.removeOverlay(overlay)
    }
  })
  roadSpeedOverlays = []
  
  removeDistrictBoundaries() // 清空地图时也同步清空区县边界
}

// 专门用于清空热力图的方法，保持地图样式不变
function clearHeatmapOnly() {
  console.log('🔥 正在清除热力图数据，保持地图样式')
  
  if (view && heatmapLayer) {
    console.log('🔥 移除热力图图层')
    view.removeLayer(heatmapLayer)
    console.log('🔥 热力图图层移除完毕')
  }
  
  heatmapLayer = null
}

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
  console.log('showPoints收到数据:', data)
  if (!window.mapvgl || !view) {
    alert('MapVGL 脚本或视图尚未加载完成，请稍后再试！')
    return
  }
  clearMapOverlays()
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
  console.log('🔥 showHeatmap 被调用', data);
  if (!window.mapvgl || !view) {
    alert('mapvgl 脚本或视图尚未加载完成，请稍后再试！');
    return;
  }
  
  // 如果是动态热力图模式，只清空热力图数据，保持地图样式
  if (showDynamicControls.value) {
    clearHeatmapOnly();
  } else {
    // 非动态热力图模式，清空所有覆盖物
    clearMapOverlays();
  }
  
  if (!data || !data.length) return;
  
  // 构造热力图数据
  const points = data.map(item => ({
    geometry: { type: 'Point', coordinates: [item.lng, item.lat] },
    count: item.count || 30 // 使用数据中的count值，默认为30
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

// 动态热力图相关方法
function showDynamicHeatmap(data) {
  console.log('🔥 showDynamicHeatmap in BaiDuMap.vue 被调用', data);
  if (!data || !data.timeSlots || !data.timeSlots.length) {
    alert('动态热力图数据格式错误或为空！');
    return;
  }
  
  // 确保地图样式为浅色
  setMapStyle('light');
  
  // 处理数据，每个时段只显示起始时间作为标识
  const processedTimeSlots = data.timeSlots.map((slot, index) => {
    const startTime = new Date(slot.startTime);
    
    return {
      timeSlot: `时段 ${index + 1} (${startTime.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })})`,
      startTime: slot.startTime,
      points: slot.points || []
    };
  });
  
  timeSlotsData.value = processedTimeSlots;
  currentIndex.value = 0;
  showDynamicControls.value = true;
  
  // 显示第一个时段的数据
  updateCurrentTimeSlot();
}

function updateCurrentTimeSlot() {
  if (timeSlotsData.value.length === 0) return;
  
  const currentSlot = timeSlotsData.value[currentIndex.value];
  currentTimeSlot.value = currentSlot.timeSlot;
  
  // 直接调用 showHeatmap 方法，传入当前时段的数据
  showHeatmap(currentSlot.points || []);
}

function prevTimeSlot() {
  if (currentIndex.value > 0) {
    currentIndex.value--;
    const currentSlot = timeSlotsData.value[currentIndex.value];
    currentTimeSlot.value = currentSlot.timeSlot;
    showHeatmap(currentSlot.points || []);
    console.log('切换到上一时段', currentIndex.value, currentSlot.points);
  }
}

function nextTimeSlot() {
  if (currentIndex.value < timeSlotsData.value.length - 1) {
    currentIndex.value++;
    const currentSlot = timeSlotsData.value[currentIndex.value];
    currentTimeSlot.value = currentSlot.timeSlot;
    showHeatmap(currentSlot.points || []);
    console.log('切换到下一时段', currentIndex.value, currentSlot.points);
  }
}

function resetAnimation() {
  // 重置到第一个时段
  currentIndex.value = 0;
  if (timeSlotsData.value.length > 0) {
    updateCurrentTimeSlot();
  } else {
    // 如果没有时段数据，清空地图并关闭控制面板
    clearMapOverlays();
    showDynamicControls.value = false;
  }
}

function closeDynamicControls() {
  showDynamicControls.value = false;
  clearMapOverlays(); // 关闭时清空所有覆盖物并恢复默认样式
  stopAutoPlay();
}

function startAutoPlay() {
  if (isAutoPlaying.value) return;
  
  isAutoPlaying.value = true;
  autoPlayInterval.value = setInterval(() => {
    if (currentIndex.value < timeSlotsData.value.length - 1) {
      nextTimeSlot();
    } else {
      // 播放完毕，重置到开始
      resetAnimation();
    }
  }, 2000); // 每2秒切换一次
}

function stopAutoPlay() {
  if (autoPlayInterval.value) {
    clearInterval(autoPlayInterval.value);
    autoPlayInterval.value = null;
  }
  isAutoPlaying.value = false;
}

// 根据速度获取颜色
function getSpeedColor(speed) {
  if (speed >= 60) return '#00ff00' // 绿色 - 快速
  if (speed >= 30) return '#ffff00' // 黄色 - 中等
  return '#ff0000' // 红色 - 慢速
}

// 设置地图样式的方法
function setMapStyle(style) {
  try {
    if (typeof map.setMapStyleV2 === 'function') {
      if (style === 'light') {
        map.setMapStyleV2({ styleId: 'f6283d269df3e47a16dd34611de7ece2' });
        console.log('✅ 使用 setMapStyleV2切换为浅色样式');
      } else if (style === 'normal') {
        map.setMapStyleV2({ styleId: 'default' });
        console.log('✅ 使用 setMapStyleV2 恢复默认样式');
      }
    } else {
      console.warn('⚠️ 地图对象不支持 setMapStyleV2 方法');
    }
  } catch (error) {
    console.warn('⚠️ 地图样式切换失败:', error);
  }
}

// 显示道路速度
function showRoadSpeed(data) {
  console.log('🚗 showRoadSpeed 被调用', data);
  
  if (!map) {
    alert('地图尚未加载完成，请稍后再试！');
    return;
  }
  
  // 清空之前的道路速度覆盖物
  roadSpeedOverlays.forEach(overlay => {
    map.removeOverlay(overlay);
  });
  roadSpeedOverlays = [];
  
  if (!data || !data.roads || !data.roads.length) {
    console.log('没有道路速度数据');
    return;
  }
  
  // 计算所有道路的边界，用于调整地图视野
  let minLat = Infinity, maxLat = -Infinity;
  let minLng = Infinity, maxLng = -Infinity;
  
  data.roads.forEach(road => {
    minLat = Math.min(minLat, road.start_lat, road.end_lat);
    maxLat = Math.max(maxLat, road.start_lat, road.end_lat);
    minLng = Math.min(minLng, road.start_lng, road.end_lng);
    maxLng = Math.max(maxLng, road.start_lng, road.end_lng);
  });
  
  // 调整地图视野以显示所有道路
  const centerLat = (minLat + maxLat) / 2;
  const centerLng = (minLng + maxLng) / 2;
  const latDiff = maxLat - minLat;
  const lngDiff = maxLng - minLng;
  const maxDiff = Math.max(latDiff, lngDiff);
  
  // 根据道路分布计算合适的缩放级别
  let zoom = 13;
  if (maxDiff > 0.1) zoom = 10;
  else if (maxDiff > 0.05) zoom = 11;
  else if (maxDiff > 0.02) zoom = 12;
  else if (maxDiff > 0.01) zoom = 13;
  else zoom = 14;
  
  map.centerAndZoom(new window.BMapGL.Point(centerLng, centerLat), zoom);
  
  // 为每条道路创建线条和信息窗口
  data.roads.forEach((road, index) => {
    const startPoint = new window.BMapGL.Point(road.start_lng, road.start_lat);
    const endPoint = new window.BMapGL.Point(road.end_lng, road.end_lat);
    
    console.log(`绘制道路 ${index + 1}: 从 (${road.start_lat}, ${road.start_lng}) 到 (${road.end_lat}, ${road.end_lng}), 速度: ${road.speed} km/h`);
    
    // 创建道路线条
    const polyline = new window.BMapGL.Polyline([startPoint, endPoint], {
      strokeColor: getSpeedColor(road.speed),
      strokeWeight: 6,
      strokeOpacity: 0.8,
      strokeStyle: 'solid'
    });
    
    // 添加流动动画效果
    const dashArray = [20, 10]; // 虚线样式
    polyline.setStrokeStyle(dashArray);
    
    // 创建信息窗口
    const infoWindow = new window.BMapGL.InfoWindow(
      `<div style="padding: 10px;">
        <h4 style="margin: 0 0 8px 0; color: #333;">道路速度信息</h4>
        <p style="margin: 5px 0; color: #666;">起点: (${road.start_lat.toFixed(6)}, ${road.start_lng.toFixed(6)})</p>
        <p style="margin: 5px 0; color: #666;">终点: (${road.end_lat.toFixed(6)}, ${road.end_lng.toFixed(6)})</p>
        <p style="margin: 5px 0; font-weight: bold; color: ${getSpeedColor(road.speed)};">
          速度: ${road.speed} km/h
        </p>
      </div>`,
      {
        width: 250,
        height: 120,
        title: '道路速度详情'
      }
    );
    
    // 鼠标悬停事件
    polyline.addEventListener('mouseover', function(e) {
      const point = e.latLng || e.latlng || e.point;
      map.openInfoWindow(infoWindow, point);
      
      // 悬停时线条变粗
      polyline.setStrokeWeight(10);
    });
    
    // 鼠标移出事件
    polyline.addEventListener('mouseout', function() {
      map.closeInfoWindow();
      polyline.setStrokeWeight(6);
    });
    
    // 点击事件
    polyline.addEventListener('click', function(e) {
      const point = e.latLng || e.latlng || e.point;
      map.openInfoWindow(infoWindow, point);
    });
    
    // 添加到地图
    map.addOverlay(polyline);
    roadSpeedOverlays.push(polyline);
  });
  
  console.log(`已显示 ${data.roads.length} 条道路的速度信息，地图中心: (${centerLat}, ${centerLng}), 缩放级别: ${zoom}`);
}

// 显示车辆轨迹
function showVehicleTrack(data) {
  console.log('🚗 showVehicleTrack 被调用', data);
  
  if (!map) {
    alert('地图尚未加载完成，请稍后再试！');
    return;
  }
  
  // 清空之前的车辆轨迹覆盖物
  roadSpeedOverlays.forEach(overlay => {
    map.removeOverlay(overlay);
  });
  roadSpeedOverlays = [];
  
  if (!data || !data.length) {
    console.log('没有车辆轨迹数据');
    return;
  }
  
  // 按时间排序数据点
  const sortedData = data.sort((a, b) => {
    const timeA = new Date(a.timestamp || a.time || a.datetime);
    const timeB = new Date(b.timestamp || b.time || b.datetime);
    return timeA - timeB;
  });
  
  console.log('排序后的车辆轨迹数据:', sortedData);
  console.log('排序后轨迹点数量:', sortedData.length);
  
  // 去除重复的经纬度点
  const uniqueData = [];
  const seenCoordinates = new Set();
  
  sortedData.forEach((point, index) => {
    const timeField = point.timestamp || point.time || point.datetime;
    const coordinateKey = `${point.lat.toFixed(6)},${point.lng.toFixed(6)}`;
    
    if (!seenCoordinates.has(coordinateKey)) {
      seenCoordinates.add(coordinateKey);
      uniqueData.push(point);
      console.log(`保留轨迹点 ${uniqueData.length}: 时间=${timeField}, 位置=(${point.lat}, ${point.lng})`);
    } else {
      console.log(`跳过重复轨迹点 ${index + 1}: 位置=(${point.lat}, ${point.lng})`);
    }
  });
  
  console.log('去重后轨迹点数量:', uniqueData.length);
  console.log('去重后车辆轨迹数据:', uniqueData);
  
  // 创建轨迹线条的点数组
  const trackPoints = uniqueData.map(point => 
    new window.BMapGL.Point(point.lng, point.lat)
  );
  
  // 创建轨迹线条
  const polyline = new window.BMapGL.Polyline(trackPoints, {
    strokeColor: '#ff0000',  // 红色轨迹线
    strokeWeight: 4,
    strokeOpacity: 0.8,
    strokeStyle: 'solid'
  });
  
  // 添加流动动画效果
  const dashArray = [15, 8]; // 虚线样式
  polyline.setStrokeStyle(dashArray);
  
  // 添加到地图
  map.addOverlay(polyline);
  roadSpeedOverlays.push(polyline);
  
  // 为每个轨迹点创建标记和信息窗口
  uniqueData.forEach((point, index) => {
    console.log(`创建轨迹点 ${index + 1}: 位置=(${point.lat}, ${point.lng})`);
    
    const pointObj = new window.BMapGL.Point(point.lng, point.lat);
    
    // 创建标记点 - 简化版本，避免标签设置问题
    const marker = new window.BMapGL.Marker(pointObj, {
      icon: new window.BMapGL.Icon('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iNiIgZmlsbD0iIzAwZmYwMCIgc3Ryb2tlPSIjZmZmZmZmIiBzdHJva2Utd2lkdGg9IjIiLz4KPC9zdmc+', new window.BMapGL.Size(24, 24))
    });
    
    // 创建信息窗口
    const infoWindow = new window.BMapGL.InfoWindow(
      `<div style="padding: 10px;">
        <h4 style="margin: 0 0 8px 0; color: #333;">轨迹点 ${index + 1}</h4>
        <p style="margin: 5px 0; color: #666;">经度: ${point.lng.toFixed(6)}</p>
        <p style="margin: 5px 0; color: #666;">纬度: ${point.lat.toFixed(6)}</p>
        ${point.speed ? `<p style="margin: 5px 0; color: #666;">速度: ${point.speed} km/h</p>` : ''}
        <p style="margin: 5px 0; color: #999; font-size: 12px;">点击轨迹点可查看详细信息</p>
      </div>`,
      {
        width: 280,
        height: 140,
        title: `车辆轨迹 - 第${index + 1}个轨迹点`
      }
    );
    
    // 鼠标悬停事件
    marker.addEventListener('mouseover', function(e) {
      const point = e.latLng || e.latlng || e.point;
      map.openInfoWindow(infoWindow, point);
    });
    
    // 鼠标移出事件
    marker.addEventListener('mouseout', function() {
      map.closeInfoWindow();
    });
    
    // 点击事件
    marker.addEventListener('click', function(e) {
      const point = e.latLng || e.latlng || e.point;
      map.openInfoWindow(infoWindow, point);
    });
    
    // 添加到地图
    map.addOverlay(marker);
    roadSpeedOverlays.push(marker);
  });
  
  console.log(`已显示车辆轨迹，共 ${uniqueData.length} 个轨迹点`);
}

// 切换人口显示开关
function togglePopulation() {
  console.log('togglePopulation 被调用')
  showPopulation.value = !showPopulation.value
  if (showPopulation.value) {
    drawDistrictBoundaries()
  } else {
    removeDistrictBoundaries()
    if (map && map.closeInfoWindow) map.closeInfoWindow()
  }
}

function drawDistrictBoundaries() {
  console.log('drawDistrictBoundaries 被调用')
  
  // 先清空之前的区县边界
  removeDistrictBoundaries();
  
  // 不调整地图中心和缩放等级，保持用户当前的地图视野
  console.log('保持当前地图视野，不调整中心点和缩放等级');
  
  const boundary = new window.BMapGL.Boundary();
  let processedCount = 0;
  const totalDistricts = Object.keys(districtPopulation).length;
  
  // 使用固定的区县顺序，确保每次显示一致
  const districtNames = [
    '历下区', '市中区', '槐荫区', '天桥区', '历城区', 
    '长清区', '平阴县', '济阳县', '商河县', '章丘市'
  ];
  
  districtNames.forEach(districtName => {
    boundary.get('济南市' + districtName, function(rs){
      console.log(`获取 ${districtName} 边界数据:`, rs);
      processedCount++;
      
      if (rs.boundaries && rs.boundaries.length) {
        rs.boundaries.forEach(boundaryStr => {
          const points = boundaryStr.split(';').map(item => {
            const [lng, lat] = item.split(',').map(Number);
            return new window.BMapGL.Point(lng, lat);
          });
          
          // 创建区县边界多边形
          const polygon = new window.BMapGL.Polygon(points, {
            strokeColor: "#0066cc", 
            strokeWeight: 3, 
            strokeOpacity: 0.8, 
            fillColor: "#0066cc",
            fillOpacity: 0.1
          });
          
          map.addOverlay(polygon);
          districtPolygons.push(polygon);

          // 鼠标移动时显示人口信息
          polygon.addEventListener('mousemove', function(e){
            if (showPopulation.value) {
              const pt = e.latLng || e.latlng || e.point;
              const info = new window.BMapGL.InfoWindow(
                `<div style="padding: 8px; text-align: center;">
                  <h4 style="margin: 0 0 5px 0; color: #333;">${districtName}</h4>
                  <p style="margin: 0; color: #0066cc; font-weight: bold; font-size: 16px;">
                    人口：${districtPopulation[districtName]}万
                  </p>
                </div>`, 
                {
                  width: 150,
                  height: 80,
                  title: `${districtName}人口信息`
                }
              );
              map.openInfoWindow(info, pt);
            }
          });
          
          // 鼠标移出时关闭
          polygon.addEventListener('mouseout', function(){
            map.closeInfoWindow();
          });
          
          // 点击时也显示信息
          polygon.addEventListener('click', function(e){
            if (showPopulation.value) {
              const pt = e.latLng || e.latlng || e.point;
              const info = new window.BMapGL.InfoWindow(
                `<div style="padding: 8px; text-align: center;">
                  <h4 style="margin: 0 0 5px 0; color: #333;">${districtName}</h4>
                  <p style="margin: 0; color: #0066cc; font-weight: bold; font-size: 16px;">
                    人口：${districtPopulation[districtName]}万
                  </p>
                </div>`, 
                {
                  width: 150,
                  height: 80,
                  title: `${districtName}人口信息`
                }
              );
              map.openInfoWindow(info, pt);
            }
          });
        });
        
        console.log(`✅ ${districtName} 边界已绘制`);
      } else {
        console.warn(`⚠️ ${districtName} 未获取到边界数据`);
      }
      
      // 当所有区县都处理完成后的日志
      if (processedCount === totalDistricts) {
        console.log(`所有区县边界绘制完成，共绘制了 ${districtPolygons.length} 个区县边界`);
        console.log('地图视野保持用户当前设置，未进行调整');
      }
    });
  });
}

function removeDistrictBoundaries() {
  districtPolygons.forEach(polygon => map.removeOverlay(polygon))
  districtPolygons = []
}

// 组件卸载时清理定时器
onUnmounted(() => {
  // 清空地图覆盖物
  clearMapOverlays();
  // 停止自动播放
  stopAutoPlay();
});

// eslint-disable-next-line no-undef
defineExpose({
  showPoints,
  showHeatmap,
  showDynamicHeatmap,
  showRoadSpeed,
  showVehicleTrack,
  setMapStyle,
  clearMapOverlays,
  clearHeatmapOnly,
  togglePopulation,
  goToShandong,
  prevTimeSlot,
  nextTimeSlot,
  resetAnimation,
  closeDynamicControls,
  startAutoPlay,
  stopAutoPlay,
})

onMounted(async () => {
  try {
    await loadBMapGL()
    map = new window.BMapGL.Map('mapContainer')
    map.centerAndZoom(new window.BMapGL.Point(116.994917, 36.66123), 13)
    map.enableScrollWheelZoom(true)
    
    await loadMapVGL()
    view = new window.mapvgl.View({ map })

    // addDistrictPolygonsWithBoundary(districtPopulation); // 移除此行，改为在 togglePopulation 中控制

  } catch (e) {
    console.error('加载失败:', e)
    alert('地图加载失败: ' + e.message)
  }
})

function goToShandong() {
  if (map) {
    // 山东省中心经纬度大致为 117.000923, 36.675807，缩放级别建议 7
    map.centerAndZoom(new window.BMapGL.Point(117.000923, 36.675807), 7)
  }
}

</script>

<style scoped>
#mapContainer {
  width: 100%;
  height: 100%;
  min-height: 600px;
  flex: 1 1 0;
}

/* 动态热力图控制面板样式 */
.dynamic-heatmap-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

.control-panel {
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 15px;
  border-radius: 8px;
  min-width: 200px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.time-display {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 10px;
  text-align: center;
  padding: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 10px;
}

.control-buttons button {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.control-buttons button:hover:not(:disabled) {
  background: #0056b3;
}

.control-buttons button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.control-buttons button.playing {
  background: #28a745;
}

.control-buttons button.playing:hover {
  background: #218838;
}

.progress-info {
  text-align: center;
  font-size: 12px;
  color: #ccc;
}
</style>
