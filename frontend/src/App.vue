<!-- src/App.vue -->
<template>
  <div id="app">
    <router-view /> <!-- 显示当前路由页面内容 -->
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
/* 可添加全局样式 */
body {
  margin: 0;
  font-family: Arial, sans-serif;
}
</style>
