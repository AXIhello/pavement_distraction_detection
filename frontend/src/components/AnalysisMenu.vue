<template>
  <div class="analysis-layout">
    <div class="button-group">
      <button class="menu-btn" @click="emitScroll('map')">上客点查询</button>
      <button class="menu-btn" @click="emitScroll('time-distance')">时间与距离</button>
      <button class="menu-btn" @click="emitScroll('heatmap-animation')">热力动态图</button>
      <button class="menu-btn" @click="emitScroll('population')">人口分布</button>
      <button class="menu-btn" @click="emitScroll('traffic-flow')">周客流量</button>
      <button class="menu-btn" @click="goHome">返回主界面</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisMenu',
  emits: ['scroll-to'],
  methods: {
    emitScroll(id) {
      this.$emit('scroll-to', id)
    },
    goHome() {
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.analysis-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;

  
}
.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  justify-content: center;
  margin-top: 2rem;
}
.menu-btn {
  background: #2176ff;
  color: #fff;
  font-size: 1.1rem;
  padding: 1rem 2.2rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.menu-btn:hover {
  background: #1856b8;
}
</style> 