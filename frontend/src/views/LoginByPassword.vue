<template>
  <div id="app">
    <header>
      <h1>交通检测系统</h1>
    </header>

    <main>
      <!-- 地图区域 -->
      <div class="map-container">
        <img :src="map" alt="地图图标" />
        <div class="map-markers">
          <div class="marker" style="left: 10%; top: 30%;">1</div>
          <div class="marker" style="left: 20%; top: 50%;">2</div>
          <div class="marker" style="left: 25%; top: 55%;">3</div>
          <div class="marker" style="left: 35%; top: 50%;">4</div>
          <div class="marker" style="left: 40%; top: 40%;">5</div>
        </div>
      </div>

      <!-- 登录表单 -->
      <div class="login-container">
        <form @submit.prevent="handleLogin">
          <h2>登录 | 注册</h2>

          <div class="form-group">
            <label for="account">账号</label>
            <input type="text" id="account" v-model="account" required />
          </div>

          <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" v-model="password" required />
          </div>

          <div class="form-group">
            <input type="checkbox" id="identity" v-model="identity" />
            <label for="identity">身份认证</label>
          </div>

          <button type="submit">登录</button>
          <button type="button" @click="faceRecognition">人脸识别</button>

          <!-- 登录反馈信息 -->
          <p :style="{ color: messageColor }">{{ message }}</p>
        </form>

        <!-- 其他登录方式 -->
        <div class="other-login-methods">
          <span>其他登录方式</span>
          <!-- <img src="/icons/phone-icon.png" alt="Phone" />
          <img src="/icons/email-icon.png" alt="Email" /> -->
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import map from '@/assets/images/map.png'
const account = ref('');
const password = ref('');
const identity = ref(false);
const message = ref('');
const messageColor = ref('red');

async function handleLogin() {
  message.value = '';

  try {
    const res = await fetch('http://127.0.0.1:5000/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: account.value,
        password: password.value
      })
    });

    const data = await res.json();

    if (data.success) {
      message.value = data.message;
      messageColor.value = 'green';
    } else {
      message.value = data.message;
      messageColor.value = 'red';
    }
  } catch (error) {
    message.value = '请求失败，请检查后端服务是否启动';
    messageColor.value = 'red';
  }
}

function faceRecognition() {
  alert('人脸识别功能暂未实现');
}
</script>

<style>
#app {
  font-family: Arial, sans-serif;
}

header {
  background-color: #f0f0f0;
  padding: 10px;
  text-align: center;
}

main {
  display: flex;
  justify-content: space-between;
  padding: 20px;
}

.map-container {
  position: relative;
  width: 50%;
}

.map-image {
  width: 100%;
  height: auto;
}

.map-markers {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.marker {
  position: absolute;
  background-color: red;
  color: white;
  border-radius: 50%;
  padding: 5px;
  font-size: 12px;
}

.login-container {
  width: 45%;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
}

.form-group input {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}

button {
  width: 100%;
  padding: 10px;
  margin-top: 10px;
  background-color: #000;
  color: #fff;
  border: none;
  cursor: pointer;
}

button[type="button"] {
  background-color: #ccc;
}

.other-login-methods {
  margin-top: 20px;
}

.other-login-methods span {
  margin-right: 10px;
}

.other-login-methods img {
  width: 24px;
  height: 24px;
  margin-right: 10px;
}
</style>
