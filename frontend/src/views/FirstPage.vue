<template>
  <div>
    <!-- 顶部导航栏 -->
    <Navigation ref="navRef" />

    <!-- 页面内容区 -->
    <main class="main-content">
      <section class="feature-section">
        <FeatureCard
          title="人脸识别"
          desc="高效精准的人脸识别，助力身份核验与安全管理。"
          :imgSrc="faceImg"
          detail="系统集成先进的人脸检测与识别算法，支持陌生人与deepFake报警。"
          route="/face"
        />
        <FeatureCard
          title="路面灾害监测"
          desc="智能识别路面破损、坑洞等灾害，保障道路安全。"
          imgSrc="https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=400&q=80"
          detail="基于深度学习的图像识别技术，自动检测路面裂缝、坑洞等异常，及时报警，提升城市道路管理效率。"
          route="/detect"
        />
        <FeatureCard
          title="城市交通时空分析"
          desc="多维度分析城市交通流，辅助科学决策。"
          imgSrc="https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=400&q=80"
          detail="通过对交通流量、速度、拥堵等数据的时空分析，提供可视化报表，助力城市交通优化与智能调度。"
          route="/traffic"
        />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Navigation from '@/components/Navigation.vue'
import FeatureCard from '@/components/FeatureCard.vue'
import faceImg from '@/assets/images/face.png'
const navRef = ref(null)
</script>

<style scoped>
.main-content {
  padding-top: 82px; /* 顶部导航栏高度，避免遮挡 */
  max-width: 1260px;
  margin: 0 auto;
  padding-left: 20px;
  padding-right: 20px;
}
.feature-section {
  display: flex;
  justify-content: center;
  align-items: stretch;
  gap: 32px;
  margin-top: 80px;
  flex-wrap: nowrap;
}
@media (max-width: 1100px) {
  .feature-section {
    flex-wrap: wrap;
    gap: 24px;
  }
}
</style>
