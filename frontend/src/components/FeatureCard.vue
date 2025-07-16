<template>
  <div
    class="feature-card"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
    :style="cardStyle"
  >
    <img :src="imgSrc" :alt="title" class="feature-img" />
    <h2>{{ title }}</h2>
    <p>{{ desc }}</p>
    <transition name="expand">
      <div v-if="hover" class="expand-content">
        <slot name="detail">{{ detail }}</slot>
        <button class="exp-btn" @click.stop="goExperience">马上体验</button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
const props = defineProps({
  title: String,
  desc: String,
  imgSrc: String,
  detail: String,
  route: String
})
const hover = ref(false)
const router = useRouter()
const cardStyle = computed(() => ({
  transform: hover.value ? 'scale(1.06)' : 'scale(1)',
  boxShadow: hover.value ? '0 12px 32px rgba(255,193,7,0.18)' : '0 2px 8px rgba(0,0,0,0.08)',
  transition: 'all 0.3s cubic-bezier(.25,.8,.25,1)'
}))
const goExperience = () => {
  if (props.route) router.push(props.route)
}
</script>

<style scoped>
.feature-card {
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  cursor: pointer;
  padding: 24px 18px 18px 18px;
  text-align: center;
  margin: 0;
  min-width: 0;
  max-width: 340px;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  min-height: 260px;
  box-shadow: 0 4px 24px 0 rgba(255,193,7,0.10), 0 1.5px 8px 0 rgba(0,0,0,0.08);
  border: 2px solid transparent;
  transition: box-shadow 0.3s, border 0.3s, transform 0.3s;
}
.feature-card:hover {
  box-shadow: 0 8px 48px 0 rgba(255,193,7,0.18), 0 2px 16px 0 rgba(0,0,0,0.18);
  border: 2px solid #FFD54F;
  transform: scale(1.08) rotateZ(-1deg);
}
.feature-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 16px;
  margin-bottom: 18px;
  box-shadow: 0 2px 12px rgba(255,193,7,0.18);
  border: 2px solid #fffbe7;
}
.feature-card h2 {
  font-size: 22px;
  margin-bottom: 10px;
  color: #FFA000;
  font-weight: bold;
  letter-spacing: 1px;
  text-shadow: none;
}
.feature-card p {
  color: #444;
  font-size: 15px;
  min-height: 36px;
}
.expand-content {
  margin-top: 18px;
  background: rgba(255, 223, 120, 0.18);
  border-radius: 12px;
  padding: 18px 12px 12px 12px;
  color: #333;
  font-size: 15px;
  box-shadow: 0 2px 16px rgba(255,193,7,0.10);
  min-width: 200px;
  min-height: 60px;
  z-index: 2;
  backdrop-filter: blur(2px);
  border: 1px solid #FFD54F;
}
.exp-btn {
  margin-top: 18px;
  background: linear-gradient(90deg, #FFD54F 0%, #FFB300 100%);
  color: #232526;
  border: none;
  border-radius: 8px;
  padding: 10px 28px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 2px 12px #ffe082, 0 1px 4px #ffb300;
  transition: background 0.2s, box-shadow 0.2s, color 0.2s;
  letter-spacing: 1px;
}
.exp-btn:hover {
  background: linear-gradient(90deg, #FFB300 0%, #FFD54F 100%);
  color: #fff;
  box-shadow: 0 4px 24px #ffc107, 0 2px 8px #ffb300;
}
.expand-enter-active, .expand-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}
.expand-enter-from, .expand-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
