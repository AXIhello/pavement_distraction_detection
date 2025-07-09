<template>
  <div>
    <Navigation ref="navRef" />
    <main class="main-content">
      <RoadLog />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navigation from '@/components/Navigation.vue'
import RoadLog from '@/components/RoadWarn.vue'

const navRef = ref(null)
</script>

<style scoped>
/* 父容器撑满视口 */
html, body, #app, div {
  height: 100%;
  margin: 0;
}

/* Navigation使用相对定位 */
Navigation {
  position: relative;
  width: 100%;
  background-color: #333;
  padding: 20px 0; /* 导航栏的内边距 */
  z-index: 1; /* 保证它在其他内容之上 */
}

/* main-content 添加padding-top，避免内容被导航栏遮挡 */
.main-content {
  max-width: 960px;
  margin: auto;
  padding-left: 1rem;
  padding-right: 1rem;
  
  /* 给主内容区域留出空间，避免被导航栏遮挡 */
  padding-top: 80px; /* 假设导航栏高度是80px，视实际情况调整 */
  
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center;     /* 垂直居中 */
}
</style>
