<template>
  <div id="app">
    <Header />

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
        <h2>登录</h2>

        <form @submit.prevent="handleLogin">
          <div v-if="loginMethod === 'password'">
            <div class="form-group">
              <label for="account">账号</label>
              <input type="text" id="account" v-model="account" required />
            </div>

            <div class="form-group">
              <label for="password">密码</label>
              <input type="password" id="password" v-model="password" required />
            </div>
          </div>

          <div v-else-if="loginMethod === 'sms'">
            <div class="form-group">
              <label for="phone">手机号</label>
              <input type="tel" id="phone" v-model="phone" required />
            </div>

            <div class="form-group code-group">
              <label for="smsCode">验证码：</label>
              <input type="text" id="smsCode" v-model="smsCode" required />
              <button type="button" :disabled="countdown > 0" @click="sendSmsCode">
                {{ countdown > 0 ? `${countdown}s 后重发` : '获取验证码' }}
              </button>
            </div>
          </div>

          <button type="submit">登录</button>

          <p :style="{ color: messageColor }">{{ message }}</p>
        </form>

        <div class="other-login-methods">
          <span>其他登录方式</span>
          <div class="login-method-buttons">
            <button 
              :class="{ active: loginMethod === 'password' }" 
              @click="loginMethod = 'password'">账号密码登录</button>
            <button 
              :class="{ active: loginMethod === 'sms' }" 
              @click="loginMethod = 'sms'">手机验证码登录</button>
          </div>
        </div>
      </div>
      <FaceRecognition v-if="showFaceModal" @close="showFaceModal = false" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import map from '@/assets/images/map.png'
import Header from '@/components/header.vue'

const loginMethod = ref('password')
const account = ref('')
const password = ref('')
const phone = ref('')
const smsCode = ref('')
const message = ref('')
const messageColor = ref('red')
const countdown = ref(0)
let timer = null

function sendSmsCode() {
  if (!phone.value) {
    message.value = '请输入手机号'
    messageColor.value = 'red'
    return
  }
  message.value = ''

  fetch('http://127.0.0.1:5000/api/send_sms_code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phone.value })
  }).then(res => res.json())
    .then(data => {
      if (data.success) {
        message.value = '验证码已发送'
        messageColor.value = 'green'
        startCountdown()
      } else {
        message.value = data.message || '发送验证码失败'
        messageColor.value = 'red'
      }
    }).catch(() => {
      message.value = '请求失败，请检查后端服务'
      messageColor.value = 'red'
    })
}

function startCountdown() {
  countdown.value = 60
  timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

async function handleLogin() {
  message.value = ''

  if (loginMethod.value === 'password') {
    try {
      const res = await fetch('http://127.0.0.1:5000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: account.value,
          password: password.value
        })
      })
      const data = await res.json()
      if (data.success) {
        message.value = data.message
        messageColor.value = 'green'
        showFaceModal.value = true
      } else {
        message.value = data.message
        messageColor.value = 'red'
      }
    } catch (error) {
      message.value = '请求失败，请检查后端服务是否启动'
      messageColor.value = 'red'
    }
  } else {
    if (!phone.value || !smsCode.value) {
      message.value = '请输入手机号和验证码'
      messageColor.value = 'red'
      return
    }
    try {
      const res = await fetch('http://127.0.0.1:5000/api/login_by_sms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phone.value,
          code: smsCode.value
        })
      })
      const data = await res.json()
      if (data.success) {
        message.value = data.message
        messageColor.value = 'green'
      } else {
        message.value = data.message
        messageColor.value = 'red'
      }
    } catch (error) {
      message.value = '请求失败，请检查后端服务是否启动'
      messageColor.value = 'red'
    }
  }
}
</script>

<style>
#app {
  font-family: Arial, sans-serif;
}

main {
  display: flex;
  gap: 40px;
  padding: 20px;
  align-items: flex-start;
}

.map-container {
  position: relative;
  flex: 1;
  max-width: 50%;
}

.map-container img {
  width: 100%;
  height: auto;
  display: block;
  border: 1px solid #ccc;
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
  flex: 1;
  max-width: 400px;
}

.form-group {
  margin-bottom: 15px;
  width: 100%;
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

.code-group {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.code-group label {
  width: 70px;
  margin: 0;
  flex-shrink: 0;
}

.code-group input {
  flex: 1;
  padding: 8px;
  box-sizing: border-box;
}

.code-group button {
  padding: 8px 12px;
  border: 1px solid #000;
  background-color: #eee;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  width: auto;
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

.login-method-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.login-method-buttons button {
  flex: 1;
  padding: 10px;
  border: none;
  cursor: pointer;
  background-color: #ccc;
  color: white;
  font-weight: bold;
  border-radius: 4px;
}

.login-method-buttons button.active {
  background-color: #000;
  color: #fff;
}
</style>