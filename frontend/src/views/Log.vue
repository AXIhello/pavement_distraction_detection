<template>
  <div>
    <Navigation ref="navRef" />
    <main class="main-content">
      <RoadLog />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Navigation from '@/components/Navigation.vue'
import RoadLog from '@/components/RoadLog.vue'

const navRef = ref(null)
// 这里如果不想用 js 计算高度，可以让导航用固定高度或者flex布局撑开

// 如果导航高度不固定，也可以用css变量或纯css解决
</script>

<style scoped>
/* 父容器撑满视口 */
html, body, #app, div {
  height: 100%;
  margin: 0;
}

/* main-content 高度取视口高度的90%（示例），让其垂直空间足够 */
.main-content {
  max-width: 960px;
  margin: auto;
  padding-left: 1rem;
  padding-right: 1rem;

  height: 90vh; /* 这里用相对高度 */
  
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center;     /* 垂直居中 */
}
</style>
