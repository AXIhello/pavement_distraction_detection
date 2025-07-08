<template>
    <div class="header">
      <div class="title">交通检测系统</div>
      <button class="login-button" @click="goToLogin">登录</button>
    </div>
  </template>
  
  <script setup>
  import { useRouter } from 'vue-router'
  
  const router = useRouter()
  
  function goToLogin() {
    router.push('/login')
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