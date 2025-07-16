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

      <!-- 登录注册容器 -->
      <div class="auth-container">
        <!-- 主标签页 -->
        <div class="main-tabs">
          <button
            :class="{ active: mainTab === 'login' }"
            @click="mainTab = 'login'">登录</button>
          <button
            :class="{ active: mainTab === 'register' }"
            @click="mainTab = 'register'">注册</button>
        </div>

        <!-- 登录表单 -->
        <div v-if="mainTab === 'login'" class="form-container">
          <h2>登录</h2>

          <form @submit.prevent="handleLogin">
            <div v-if="loginMethod === 'password'">
              <div class="form-group">
                <label for="account">账号</label>
                <input
                  type="text"
                  id="account"
                  placeholder="账号"
                  v-model="account"
                  required />
              </div>

              <div class="form-group">
                <label for="password">密码</label>
                <input
                  type="password"
                  id="password"
                  v-model="password"
                  required
                />
        </div>

              <div class="form-group code-group">
                <label for="captcha">验证码</label>
                <input type="text" id="captcha" v-model="captcha" maxlength="4" required autocomplete="off" />
                <img :src="captchaImgUrl" @click="refreshCaptcha" alt="验证码" style="cursor:pointer;height:40px;border-radius:4px;border:1px solid #ccc;" title="点击刷新验证码" />
              </div>
            </div>

            <div v-else-if="loginMethod === 'sms'">
              <div class="form-group">
                <label for="email">账号</label>
                <input
                  type="tel"
                  id="email"
                  placeholder="账号"
                  v-model="email"
                  required />
              </div>

              <div class="form-group code-group">
                <label for="smsCode">验证码</label>
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
                @click="loginMethod = 'sms'">邮箱验证码登录</button>
            </div>
            <div class="register-hint">
              <span>没有账号？</span>
              <button type="button" class="link-button" @click="mainTab = 'register'">去注册</button>
            </div>
          </div>
        </div>

       <!-- 注册表单 -->
<div v-else-if="mainTab === 'register'" class="form-container">
  <h2>注册</h2>

  <form @submit.prevent="handleRegister">
    <div class="form-group">
      <label for="reg-account">账号</label>
      <input
        type="text"
        id="reg-account"
        placeholder="账号"
        v-model="regAccount"
        required />
    </div>

    <div class="form-group">
      <label for="reg-email">邮箱</label>
      <input
        type="email"
        id="reg-email"
        placeholder="邮箱"
        v-model="regEmail"
        required />
    </div>

    <div class="form-group">
      <label for="reg-password">密码</label>
      <input
        type="password"
        id="reg-password"
        v-model="regPassword"
        required
        @input="checkRegPasswordStrength"
      />
      <div :style="{ color: regStrengthColor }">
        密码强度：{{ regPasswordStrength }}
      </div>
      <div v-if="regPasswordStrength === '弱' && regPassword" style="color: red;">
        密码过于简单，请至少包含字母、数字和特殊字符中的两种，且不少于8位
      </div>
    </div>

    <div class="form-group">
      <label for="reg-confirm-password">确认密码</label>
      <input
        type="password"
        id="reg-confirm-password"
        v-model="regConfirmPassword"
        required />
    </div>

<!--    <button type="submit">注册</button>-->
    <button type="submit" :disabled="regPasswordStrength === '弱'">注册</button>

    <p :style="{ color: regMessageColor }">{{ regMessage }}</p>
  </form>

  <div class="register-hint">
    <span>已有账号？</span>
    <button type="button" class="link-button" @click="mainTab = 'login'">去登录</button>
  </div>
</div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import map from '@/assets/images/map.png'
import { jwtDecode } from 'jwt-decode'
import { useRouter } from 'vue-router'

const router = useRouter()

import Header from '@/components/Title.vue'

// 主标签页
const mainTab = ref('login')

// 登录相关
const loginMethod = ref('password')
const account = ref('')
const password = ref('')
// const phone = ref('')
const email = ref('')
const smsCode = ref('')
const message = ref('')
const messageColor = ref('red')
const countdown = ref(0)
let timer = null

// 注册相关
// 注册相关状态
const regAccount = ref('')
const regEmail = ref('')
const regPassword = ref('')
const regConfirmPassword = ref('')
const regMessage = ref('')
const regMessageColor = ref('red')

const captcha = ref('')
const captchaImgUrl = ref('http://127.0.0.1:8000/api/auth/captcha?'+Date.now())
function refreshCaptcha() {
  captchaImgUrl.value = 'http://127.0.0.1:8000/api/auth/captcha?' + Date.now()
}


//验证邮箱格式
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

//验证密码强度（先不启用）
function isStrongPassword(password) {
  // 至少 8 位，包含大写、小写、数字、特殊字符
  const strongRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/
  return strongRegex.test(password)
}


function sendSmsCode() {
  if (!email.value) {
    message.value = '请输入邮箱'
    messageColor.value = 'red'
    return
  }
  if (!isValidEmail(email.value)) {
  message.value = '邮箱格式不正确'
  messageColor.value = 'red'
  return
}

  message.value = ''

  fetch('http://127.0.0.1:8000/api/auth/send_email_code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email.value })
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

function startRegCountdown() {
  regCountdown.value = 60
  regTimer = setInterval(() => {
    regCountdown.value--
    if (regCountdown.value <= 0) {
      clearInterval(regTimer)
      regTimer = null
    }
  }, 1000)
}

import http from '@/utils/http'  // 导入配置的 axios 实例

// async function handleLogin() {
//   message.value = ''
//
//   if (loginMethod.value === 'password') {
//     try {
//       const res = await http.post('/auth/login', {
//         username: account.value,
//         password: password.value,
//         captcha: captcha.value
//       })
//
//       if (res.data.success) {
//         message.value = res.data.message
//         messageColor.value = 'green'
//
//  const token = res.data.access_token
//   localStorage.setItem('token', token)
//
//   // 🔥 解码 token，获取角色信息
//   const decoded = jwtDecode(token)
//   const userInfo = {
//     id: decoded.user_id,
//     username: decoded.username,
//     role: decoded.role  // ← 确保你的后端 token 里有这一项
//   }
//
//   localStorage.setItem('userInfo', JSON.stringify(userInfo))
//
//         // 跳转页面
//         router.push('/first_page')
//       } else {
//         message.value = res.data.message
//         messageColor.value = 'red'
//       }
//     } catch (error) {
//       message.value = '请求失败，请检查后端服务是否启动'
//       messageColor.value = 'red'
//     }
//   } else {
//     // 验证码登录
//     try {
//       const res = await http.post('/auth/login_email', {
//         email: email.value,
//         code: smsCode.value
//       })
//
//       if (res.data.success) {
//         message.value = res.data.message
//         messageColor.value = 'green'
//
//         // 保存 token ✅
//         localStorage.setItem('token', res.data.access_token)
//
//         router.push('/first_page')
//       } else {
//         message.value = res.data.message
//         messageColor.value = 'red'
//       }
//     } catch (error) {
//       message.value = '请求失败，请检查后端服务是否启动'
//       messageColor.value = 'red'
//     }
//   }
// }
async function handleLogin() {
  message.value = ''

  if (loginMethod.value === 'password') {
    try {
      const res = await http.post('/auth/login', {
        username: account.value,
        password: password.value,
        captcha: captcha.value
      })
      if (res.data && typeof res.data.message === 'string') {
        message.value = res.data.message
        messageColor.value = res.data.success ? 'green' : 'red'
      } else {
        message.value = '登录失败'
        messageColor.value = 'red'
      }
      if (res.data.success) {
        const token = res.data.access_token
        localStorage.setItem('token', token)
        const decoded = jwtDecode(token)
        const userInfo = {
          id: decoded.user_id,
          username: decoded.username,
          role: decoded.role
        }
        localStorage.setItem('userInfo', JSON.stringify(userInfo))
        router.push('/first_page')
      }
    } catch (error) {
      if (error.response && error.response.data && error.response.data.message) {
        message.value = error.response.data.message
        messageColor.value = 'red'
      } else {
        message.value = '请求失败，请检查后端服务是否启动'
        messageColor.value = 'red'
      }
    }
  } else {
    // 验证码登录
    try {
      const res = await http.post('/auth/login_email', {
        email: email.value,
        code: smsCode.value
      })
      if (res.data && typeof res.data.message === 'string') {
        message.value = res.data.message
        messageColor.value = res.data.success ? 'green' : 'red'
      } else {
        message.value = '登录失败'
        messageColor.value = 'red'
      }
      if (res.data.success) {
        localStorage.setItem('token', res.data.access_token)
        router.push('/first_page')
      }
    } catch (error) {
      if (error.response && error.response.data && error.response.data.message) {
        message.value = error.response.data.message
        messageColor.value = 'red'
      } else {
        message.value = '请求失败，请检查后端服务是否启动'
        messageColor.value = 'red'
      }
    }
  }
}

async function handleRegister() {
  regMessage.value = ''

  if (!regAccount.value || !regEmail.value || !regPassword.value || !regConfirmPassword.value) {
    regMessage.value = '请填写所有字段'
    regMessageColor.value = 'red'
    return
  }

  if (!isValidEmail(regEmail.value)) {
    regMessage.value = '邮箱格式不正确'
    regMessageColor.value = 'red'
    return
  }

  if (regPassword.value !== regConfirmPassword.value) {
    regMessage.value = '两次输入的密码不一致'
    regMessageColor.value = 'red'
    return
  }

  try {
    const res = await fetch('http://127.0.0.1:8000/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: regAccount.value,
        email: regEmail.value,
        password: regPassword.value
      })
    })
    const data = await res.json()
    if (data.success) {
      regMessage.value = data.message
      regMessageColor.value = 'green'
      setTimeout(() => {
        mainTab.value = 'login'
      }, 1500)
    } else {
      regMessage.value = data.message
      regMessageColor.value = 'red'
    }
  } catch (error) {
    regMessage.value = '请求失败，请检查后端服务是否启动'
    regMessageColor.value = 'red'
  }
}

import { computed } from 'vue'

const regPasswordStrength = ref('弱')

function getPasswordStrength(password) {
  if (password.length < 8) return '弱'
  let hasLower = /[a-z]/.test(password)
  let hasUpper = /[A-Z]/.test(password)
  let hasDigit = /\d/.test(password)
  let hasSpecial = /[^A-Za-z0-9]/.test(password)
  let types = [hasLower, hasUpper, hasDigit, hasSpecial].filter(Boolean).length

  // 必须包含字母和数字才算“中”或“强”
  if ((hasLower || hasUpper) && hasDigit && types === 2) return '中'
  if ((hasLower || hasUpper) && hasDigit && types >= 3) return '强'
  return '弱'
}

function checkRegPasswordStrength() {
  regPasswordStrength.value = getPasswordStrength(regPassword.value)
}

const regStrengthColor = computed(() => {
  if (regPasswordStrength.value === '强') return 'green'
  if (regPasswordStrength.value === '中') return 'orange'
  return 'red'
})
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
  margin-top: 80px;
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

.auth-container {
  flex: 1;
  max-width: 400px;
}

.main-tabs {
  display: flex;
  margin-bottom: 20px;
  border-bottom: 2px solid #eee;
}

.main-tabs button {
  flex: 1;
  padding: 15px;
  border: none;
  background-color: transparent;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  color: #666;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
}

.main-tabs button.active {
  color: #000;
  border-bottom-color: #000;
}

.main-tabs button:hover {
  color: #000;
}

.form-container {
  width: 100%;
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

.register-hint {
  margin-top: 15px;
  text-align: center;
  font-size: 12px;
  color: #666;
}

.register-hint span {
  margin-right: 5px;
}

.link-button {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  text-decoration: underline;
  font-size: 12px;
  padding: 0;
  width: auto;
  margin: 0;
}

.link-button:hover {
  color: #0056b3;
}
button:disabled {
  background-color: #ccc !important;
  color: #fff !important;
  cursor: not-allowed !important;
  border: none !important;
  opacity: 0.7;
}
</style>
