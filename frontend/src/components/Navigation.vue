<template>
  <div class="navigation">
    <div class="text-wrapper">交通检测系统</div>
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

function goToHome() {
  router.push('/home')
}

function isActive(path) {
  return route.path === path
}
</script>

<style scoped>
.navigation {
  background-color: var(--navigation-bar, #f5f5f5);
  height: 82px;               
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); 
}

.text-wrapper {
  color: #000000;
  font-family: "Inter-Medium", Helvetica, sans-serif;
  font-size: 22.5px;          
  font-weight: 500;
  position: absolute;
  top: 23.5px;                
  left: 40px;                 
  white-space: nowrap;
  line-height: 33.75px;       
}

.items {
  display: flex;
  align-items: center;
  gap: 16px;                  
  position: absolute;
  top: 21.5px;                
  right: 40px;                
  height: 39px;               
}

.nav-item {
  color: #000000;
  font-family: "Inter-Medium", Helvetica, sans-serif;
  font-size: 12px;            
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
  background-color: #a9cde3; /* 激活时颜色加深 */
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
