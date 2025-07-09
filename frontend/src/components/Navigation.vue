<template>
  <div class="navigation" ref="navRef">
    <div class="logo-title" @click="goToFirstPage">
      交通检测系统
    </div>

    <div class="items">
      <!-- 人脸识别下拉菜单 -->
      <div
        class="nav-dropdown"
        @mouseenter="handleMouseEnter"
        @mouseleave="handleMouseLeave"
      >
        <div class="nav-item" @click="toggleDropdown">
          人脸识别 ▾
        </div>
        <div class="dropdown-menu" v-show="showDropdown" @mouseenter="handleMouseEnter" @mouseleave="handleMouseLeave">
          <router-link to="/face_register" class="dropdown-item" @click="closeDropdown">人脸录入</router-link>
          <router-link to="/face" class="dropdown-item" @click="closeDropdown">人脸认证</router-link>
        </div>
      </div>

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
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const showDropdown = ref(false)
const hoverTimeout = ref(null)
const navRef = ref(null)

function goToFirstPage() {
  router.push('/first_page')
}
function goToHome() {
  router.push('/home')
}
function isActive(path) {
  return route.path === path
}

// 鼠标进入，清除关闭定时器，显示菜单
function handleMouseEnter() {
  if (hoverTimeout.value) {
    clearTimeout(hoverTimeout.value)
    hoverTimeout.value = null
  }
  showDropdown.value = true
}
// 鼠标离开，延时关闭菜单（防止闪退）
function handleMouseLeave() {
  hoverTimeout.value = setTimeout(() => {
    showDropdown.value = false
  }, 200)
}

// 点击切换下拉菜单
function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

// 点击菜单选项后关闭菜单
function closeDropdown() {
  showDropdown.value = false
}

// 点击页面外部关闭菜单
function handleClickOutside(event) {
  if (navRef.value && !navRef.value.contains(event.target)) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
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
  box-sizing: border-box;
}

.logo-title {
  color: #000000;
  font-family: "Inter-Medium", Helvetica, sans-serif;
  font-size: 28px;
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
  justify-content: flex-end;
  max-width: calc(100% - 220px);
  width: 100%;
  overflow: visible;
  position: relative;
}

.nav-dropdown {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
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
  cursor: pointer;
  user-select: none;
}

.nav-item:hover {
  background-color: #dce7ef;
}

.nav-item.active {
  background-color: #F1D06F;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  background-color: #ffffff;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-top: 4px;
  z-index: 1001;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  min-width: 120px;
  display: flex;
  flex-direction: column;
}

.dropdown-item {
  display: block;
  padding: 8px 12px;
  color: #000000;
  text-decoration: none;
  font-size: 14px;
}

.dropdown-item:hover {
  background-color: #f0f0f0;
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
