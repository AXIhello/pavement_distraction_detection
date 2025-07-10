<template>
    <div class="header">
      <div class="title">交通检测系统</div>
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
    background-color: var(--navigation-bar, #EFE7DC);
    height: 82px;
    width: 100%;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 1000;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    display: flex;
    align-items: center;
    padding: 0 20px;
    box-sizing: border-box;
  }
  
  .title {
    font-size: 20px;
    font-weight: bold;
    white-space: nowrap;
  }
  </style>