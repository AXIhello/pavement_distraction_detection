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
        <h2>登录 | 注册</h2>

        <!-- 登录方式切换按钮 -->
        <div class="login-method-switch">
          <button 
            :class="{ active: loginMethod === 'password' }" 
            @click="loginMethod = 'password'">账号密码登录</button>
          <button 
            :class="{ active: loginMethod === 'sms' }" 
            @click="loginMethod = 'sms'">手机验证码登录</button>
        </div>

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
              <label for="smsCode">验证码</label>
              <input type="text" id="smsCode" v-model="smsCode" required />
              <button type="button" :disabled="countdown > 0" @click="sendSmsCode">
                {{ countdown > 0 ? `${countdown}s 后重发` : '获取验证码' }}
              </button>
            </div>
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
          <!-- 你可以加第三方登录按钮等 -->
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import map from '@/assets/images/map.png'

const loginMethod = ref('password') // 登录方式，默认账号密码登录

// 账号密码登录用
const account = ref('')
const password = ref('')

// 手机验证码登录用
const phone = ref('')
const smsCode = ref('')

// 其他状态
const identity = ref(false)
const message = ref('')
const messageColor = ref('red')

// 验证码倒计时
const countdown = ref(0)
let timer = null

// 发送验证码
function sendSmsCode() {
  if (!phone.value) {
    message.value = '请输入手机号'
    messageColor.value = 'red'
    return
  }
  message.value = ''
  
  // 这里写发送验证码的请求示例（替换为你后端接口）
  fetch('http://127.0.0.1:5000/api/send_sms_code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone: phone.value })
  }).then(res => res.json())
    .then(data => {
      if(data.success){
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

// 倒计时函数
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

// 登录处理
async function handleLogin() {
  message.value = ''

  if(loginMethod.value === 'password'){
    // 账号密码登录
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
      } else {
        message.value = data.message
        messageColor.value = 'red'
      }
    } catch (error) {
      message.value = '请求失败，请检查后端服务是否启动'
      messageColor.value = 'red'
    }
  } else {
    // 手机验证码登录
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

// 人脸识别按钮
function faceRecognition() {
  alert('人脸识别功能暂未实现')
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

.login-method-switch {
  margin-bottom: 15px;
}

.login-method-switch button {
  padding: 6px 15px;
  margin-right: 10px;
  border: 1px solid #000;
  background-color: #fff;
  cursor: pointer;
}

.login-method-switch button.active {
  background-color: #000;
  color: #fff;
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

.code-group {
  display: flex;
  align-items: center;
}

.code-group input {
  flex-grow: 1;
}

.code-group button {
  margin-left: 10px;
  padding: 8px 12px;
  cursor: pointer;
  border: 1px solid #000;
  background-color: #eee;
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
