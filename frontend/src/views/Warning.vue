<template>
  <div>
    <Navigation ref="navRef" />
    <main class="main-content">
      <RoadWarn />
      <FaceWarn />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navigation from '@/components/Navigation.vue'
import RoadWarn from '@/components/RoadWarn.vue'
import FaceWarn from '@/components/FaceWarn.vue'

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
  padding-top: 80px; /* 避免导航栏遮挡 */

  display: flex;
  flex-direction: column;   /* 改成纵向排列 */
  gap: 20px;               /* 两个组件之间间距 */
  
  /* 如果你希望组件宽度撑满 main-content 宽度 */
  align-items: stretch;
}

</style>
