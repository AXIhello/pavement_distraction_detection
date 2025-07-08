<template>
    <div class="header">
      <div class="title">交通检测系统</div>
      <div class="button-group">
        <button class="login-button">路面灾害检测</button>
        <button class="login-button">城市交通时空</button>
        <button class="login-button">日志</button>
        <button class="login-button" @click="goToHome">用户中心</button>
    </div>
    </div>
  </template>
  
  <script setup>
  import { useRouter } from 'vue-router'
  
  const router = useRouter()
  
  function goToHome() {
    router.push('/home')
  }
  </script>
  
  <style scoped>
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background-color: #f5f5f5;
    border-bottom: 1px solid #ddd;
  }
  
  .title {
    font-size: 20px;
    font-weight: bold;
    white-space: nowrap;
  }
  
  .button-group {
    display: flex;
    gap: 8px; /* 按钮之间的间距，可以根据需要调整 */
  }

  .login-button {
    background-color: #000;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    cursor: pointer;
    white-space: nowrap;
  
    /* 重点：取消默认宽度 */
    display: inline-block;
    width: auto;
  }
  
  .login-button:hover {
    background-color: #333;
  }
  </style>