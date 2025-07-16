<template>
    <div id="mapContainer"></div>
  </template>

  <script setup>
  import { onMounted } from 'vue'

  const BMAP_AK = '20FcUoEvheMHZMHXkCOdDIh5kEFm8gOo'

  const loadBMapWithCallback = () => {
    return new Promise((resolve, reject) => {
      if (window.BMapGL) {
        return resolve()
      }
  1
      // 声明回调函数，供百度地图加载完后调用
      window.onBMapCallback = () => {
        resolve()
      }

      const script = document.createElement('script')
      script.src = `https://api.map.baidu.com/api?v=1.0&type=webgl&ak=${BMAP_AK}&callback=onBMapCallback`
      script.onerror = () => reject(new Error('❌ 百度地图脚本加载失败'))
      document.head.appendChild(script)
    })
  }

  const initMap = () => {
    const map = new window.BMapGL.Map('mapContainer')
    const point = new window.BMapGL.Point(116.404, 39.915)
    map.centerAndZoom(point, 12)
    map.enableScrollWheelZoom(true)

    const trafficLayer = new window.BMapGL.TrafficLayer()
    map.addTileLayer(trafficLayer)
  }

  onMounted(async () => {
    try {
      await loadBMapWithCallback()
      initMap()
    } catch (err) {
      console.error(err)
    }
  })
  </script>

  <style scoped>
  #mapContainer {
    width: 100%;
    height: 600px;
    display: block;
  }
  </style>
