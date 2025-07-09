<template>
  <div class="navigation">
    <div class="logo-title" @click="goToFirstPage">
      交通检测系统
    </div>
    <div class="items">
      <router-link
        to="/detect"
        class="nav-item"
        :class="{ active: isActive('/detect') }"
      >路面灾害检测</router-link>

      <router-link
        to="/traffic"
        class="nav-item"
        :class="{ active: isActive('/traffic') }"
      >城市交通时空</router-link>

      <router-link
        to="/log"
        class="nav-item"
        :class="{ active: isActive('/log') }"
      >日志</router-link>

      <button class="button" @click="goToHome">
        <div class="text-wrapper-3">用户中心</div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

function goToFirstPage() {
  router.push('/first_page')
}
function goToHome(){
  router.push('/home')
}

function isActive(path) {
  return route.path === path
}
</script>

<style scoped>
.navigation {
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
  box-sizing: border-box; /* 包含 padding */
}

.logo-title {
  color: #000000;
  font-family: "Inter-Medium", Helvetica, sans-serif;
  font-size: 28px; /* 增大字体大小 */
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.logo-title:hover {
  opacity: 0.7;
}

.items {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: flex-end; /* 确保右侧对齐 */
  max-width: calc(100% - 220px); /* 限制右侧区域宽度，减去左侧区域的宽度（logo宽度） */
  width: 100%;
  overflow: hidden; /* 防止超出 */
}

.nav-item {
  color: #000000;
  font-family: "Inter-Medium", Helvetica, sans-serif;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  padding: 5px 8px;
  border-radius: 3px;
  transition: background-color 0.3s;
}

.nav-item:hover {
  background-color: #dce7ef;
}

.nav-item.active {
  background-color: #F1D06F; /* 激活时颜色加深 */
}

.button {
  all: unset;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #000000;
  border-radius: 4px;
  padding: 7px 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  cursor: pointer;
}

.text-wrapper-3 {
  color: #ffffff;
  font-family: "Inter-Medium", Helvetica, sans-serif;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
  white-space: nowrap;
}
</style>
