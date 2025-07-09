<template>
  <div>
    <!-- 顶部导航栏 -->
    <Navigation ref="navRef" />

    <!-- 页面内容区 -->
    <main class="main-content">
      <section class="intro-section">
        <h1>欢迎使用交通检测系统</h1>
        <p>
          本系统提供路面灾害检测、城市交通时空分析和日志管理功能，
          助力城市交通安全与智能化管理。
        </p>
        <img src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80" alt="交通图片" />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navigation from '@/components/Navigation.vue'
const navRef = ref(null)
</script>

<style scoped>
.main-content {
  padding-top: 82px; /* 顶部导航栏高度，避免遮挡 */
  max-width: 960px;
  margin: 0 auto;
  padding-left: 20px;
  padding-right: 20px;
}

.intro-section {
  text-align: center;
  margin-top: 60px;
}

.intro-section h1 {
  font-size: 36px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 20px;
}

.intro-section p {
  font-size: 18px;
  color: #4b5563;
  margin-bottom: 40px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.5;
}

.intro-section img {
  max-width: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
</style>
