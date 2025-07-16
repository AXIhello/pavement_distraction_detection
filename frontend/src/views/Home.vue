<template>
  <Header />
  <div class="home-container">
    <h1>用户中心</h1>

    <!-- 加载与错误状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载用户信息中...</p>
    </div>
    <div v-else-if="error" class="error-state">
      <i class="icon-error">⚠️</i>
      <p>{{ error }}</p>
      <button @click="retryFetch" class="btn retry-btn">重试</button>
    </div>

    <!-- 主内容区 -->
    <div v-else class="user-info-card">
      <!-- 基本信息卡片 -->
      <div class="info-card">
        <h2 class="card-title">
          <div class="title-left">
            <i class="icon-title">👤</i> 基本信息
          </div>
          <!-- 右侧悬浮拉条 -->
          <div class="edit-sidebar" @mouseenter="showEditOptions = true" @mouseleave="showEditOptions = false">
            <div class="edit-handle">⚙️</div>
            <transition name="fade">
              <div v-if="showEditOptions" class="edit-options">
                <button @click="openUsernameDialog" class="btn small-btn">修改账号</button>
                <button @click="openPasswordDialog" class="btn small-btn">修改密码</button>
              </div>
            </transition>
          </div>
        </h2>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">账号：</span>
            <span class="info-value">{{ user.username }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">角色：</span>
            <span class="info-value role-badge">{{ user.role }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">邮箱：</span>
            <span class="info-value">{{ user.email || '未绑定' }}</span>
          </div>
        </div>
      </div>

      <!-- 人脸照片管理卡片 -->
      <div class="info-card">
        <h2 class="card-title no-action">
          <i class="icon-title">📷</i> 人脸照片管理
        </h2>
        <div class="face-container">
          <div v-if="faceImages.length" class="face-grid">
            <div v-for="(img, idx) in faceImages" :key="img.id" class="face-item">
              <div class="face-img-wrapper">
                <img :src="img.url" alt="人脸照片" class="face-image" />
                <button @click="deleteFace(img.id)" class="delete-btn" title="删除照片">
                  <i class="icon-delete">🗑️</i>
                </button>
              </div>
              <span class="face-index">{{ img.name || `照片 ${idx + 1}` }}</span>
            </div>
          </div>
          <div v-else class="empty-state">
            <i class="icon-empty">📷</i>
            <p>暂无已录入的人脸照片</p>
            <router-link to="/face_register" class="btn secondary-btn">录入人脸</router-link>
          </div>
        </div>
      </div>

      <!-- 修改账号弹窗 -->
      <dialog ref="usernameDialog" class="edit-dialog">
        <form @submit.prevent="changeUsername">
          <h3>修改账号</h3>
          <input v-model="newUsername" placeholder="请输入3-20位新用户名" />
          <div class="dialog-buttons">
            <button type="submit" class="btn primary-btn">确认修改</button>
            <button type="button" class="btn secondary-btn" @click="closeUsernameDialog">取消</button>
          </div>
        </form>
      </dialog>

      <!-- 修改密码弹窗 -->
      <dialog ref="passwordDialog" class="edit-dialog">
        <form @submit.prevent="changePassword">
          <h3>修改密码</h3>
          <input type="password" v-model="newPassword" placeholder="请输入至少8位新密码" />
          <input v-model="emailCode" placeholder="请输入6位邮箱验证码" />
          <button type="button" @click="sendEmailCode" :disabled="codeSent" class="btn secondary-btn code-btn">
            {{ codeSent ? `已发送 (${countdown}s)` : '获取验证码' }}
          </button>
          <div class="dialog-buttons">
            <button type="submit" class="btn primary-btn">确认修改密码</button>
            <button type="button" class="btn secondary-btn" @click="closePasswordDialog">取消</button>
          </div>
        </form>
      </dialog>

      <!-- 操作结果弹窗 -->
      <dialog ref="resultDialog" class="result-dialog">
        <div class="result-content">
          <i :class="resultIcon">{{ resultIcon === 'icon-success' ? '✓' : '⚠️' }}</i>
          <h3>{{ resultTitle }}</h3>
          <p>{{ resultMessage }}</p>
          <button @click="closeResultDialog" class="btn primary-btn">确定</button>
        </div>
      </dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Header from '@/components/Navigation.vue'

const user = ref({})
const loading = ref(true)
const error = ref('')
const faceImages = ref([])

// 新增重试功能
const retryFetch = async () => {
  loading.value = true
  error.value = ''
  await fetchUserData()
}

// 新增倒计时功能
const countdown = ref(0)
const countdownTimer = ref(null)

const token = localStorage.getItem('token')
const API_URL = 'http://127.0.0.1:8000/api/auth/me'
const FACE_API = 'http://127.0.0.1:8000/api/face/my_faces'

async function fetchUserData() {
  try {
    const res = await fetch(API_URL, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })
    const data = await res.json()
    if (data.success) {
      user.value = data.user
      await fetchFaceImages()
    } else {
      throw new Error(data.message || '获取用户信息失败')
    }
  } catch (err) {
    console.error(err)
    error.value = '请求失败，请检查网络连接或后端服务'
  } finally {
    loading.value = false
  }
}

async function fetchFaceImages() {
  try {
    const faceRes = await fetch(FACE_API, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const faceData = await faceRes.json()
    if (faceData.success) {
      faceImages.value = faceData.images.map(img => ({
        id: img.id,
        url: `http://127.0.0.1:8000${img.url}`,
        name: img.name
      }))
    } else {
      throw new Error(faceData.message || '加载人脸照片失败')
    }
  } catch (err) {
    console.error(err)
    error.value = '加载人脸照片失败，请检查后端服务'
  }
}

async function deleteFace(faceId) {
  if (!confirm('确定要删除这张人脸照片吗？删除后不可恢复')) return
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/auth/delete_face/${faceId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await res.json()
    if (data.success) {
      await fetchFaceImages()
      showResult('success', '删除成功', '人脸照片已成功删除')
    } else {
      showResult('error', '删除失败', data.message || '删除操作未能完成')
    }
  } catch (err) {
    console.error(err)
    showResult('error', '删除失败', '删除过程中出现错误，请稍后重试')
  }
}

onMounted(async () => {
  await fetchUserData()
})

// 修改用户名相关
const newUsername = ref('')

async function changeUsername() {
  if (!newUsername.value) {
    showResult('error', '修改失败', '新用户名不能为空')
    return
  }
  if (newUsername.value.length < 3) {
    showResult('error', '修改失败', '用户名长度不能少于3位')
    return
  }
  try {
    const res = await fetch('http://127.0.0.1:8000/api/auth/change_username', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ new_username: newUsername.value })
    })
    const data = await res.json()
    if (data.success) {
      user.value.username = newUsername.value
      newUsername.value = ''
      closeUsernameDialog()
      showResult('success', '修改成功', '用户名已成功修改')
    } else {
      showResult('error', '修改失败', data.message || '用户名修改失败')
    }
  } catch (err) {
    console.error(err)
    showResult('error', '修改失败', '修改过程中出现错误，请稍后重试')
  }
}

// 修改密码相关
const newPassword = ref('')
const emailCode = ref('')
const codeSent = ref(false)

async function sendEmailCode() {
  if (!user.value.email) {
    showResult('error', '操作失败', '未获取到用户邮箱信息')
    return
  }
  try {
    const res = await fetch('http://127.0.0.1:8000/api/auth/send_email_code', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: user.value.email })
    })
    const data = await res.json()
    if (data.success) {
      codeSent.value = true
      startCountdown()
      showResult('success', '验证码已发送', '验证码已发送至您的邮箱，请查收')
    } else {
      showResult('error', '发送失败', data.message || '验证码发送失败')
    }
  } catch (err) {
    console.error(err)
    showResult('error', '发送失败', '验证码发送过程中出现错误')
  }
}

// 新增倒计时功能
function startCountdown() {
  countdown.value = 60
  countdownTimer.value = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer.value)
      codeSent.value = false
    }
  }, 1000)
}

async function changePassword() {
  if (!newPassword.value) {
    showResult('error', '修改失败', '新密码不能为空')
    return
  }
  if (newPassword.value.length < 8) {
    showResult('error', '修改失败', '密码长度不能少于8位')
    return
  }
  if (!emailCode.value) {
    showResult('error', '修改失败', '请输入邮箱验证码')
    return
  }
  try {
    const res = await fetch('http://127.0.0.1:8000/api/auth/change_password', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code: emailCode.value, new_password: newPassword.value })
    })
    const data = await res.json()
    if (data.success) {
      newPassword.value = ''
      emailCode.value = ''
      codeSent.value = false
      clearInterval(countdownTimer.value)
      closePasswordDialog()
      showResult('success', '修改成功', '密码已成功修改')
    } else {
      showResult('error', '修改失败', data.message || '密码修改失败')
    }
  } catch (err) {
    console.error(err)
    showResult('error', '修改失败', '修改过程中出现错误，请稍后重试')
  }
}

const showEditOptions = ref(false)

// 弹窗引用
const usernameDialog = ref(null)
const passwordDialog = ref(null)
const resultDialog = ref(null)
const resultTitle = ref('')
const resultMessage = ref('')
const resultIcon = ref('icon-success')

function showResult(type, title, message) {
  resultIcon.value = type === 'success' ? 'icon-success' : 'icon-error'
  resultTitle.value = title
  resultMessage.value = message
  resultDialog.value.showModal()
}

function closeResultDialog() {
  resultDialog.value.close()
}

function openUsernameDialog() {
  usernameDialog.value.showModal()
  showEditOptions.value = false
}

function closeUsernameDialog() {
  usernameDialog.value.close()
}

function openPasswordDialog() {
  passwordDialog.value.showModal()
  showEditOptions.value = false
}

function closePasswordDialog() {
  passwordDialog.value.close()
}

</script>

<style scoped>
/* 基础样式重置与变量定义 */
:root {
  --primary-color: #4285f4;
  --primary-light: #e8f0fe;
  --success-color: #34a853;
  --error-color: #ea4335;
  --warning-color: #fbbc05;
  --text-primary: #333333;
  --text-secondary: #666666;
  --border-color: #e0e0e0;
  --card-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  --transition: all 0.3s ease;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
}

/* 容器样式 */
.home-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 30px;
  font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  color: var(--text-primary);
  margin-top: 100px;
  background-color: #f8f9fa;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
  border-radius: var(--radius-lg);
}

h1 {
  text-align: center;
  color: var(--text-primary);
  margin-bottom: 30px;
  font-weight: 600;
  font-size: 28px;
  position: relative;
  padding-bottom: 15px;
  letter-spacing: 0.5px;
}

h1::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-color), #d7c480);
  border-radius: 2px;
}

/* 加载状态样式 */
.loading-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid var(--primary-light);
  border-top: 5px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误状态样式 */
.error-state {
  color: var(--error-color);
  text-align: center;
  padding: 40px 20px;
  background-color: rgba(234, 67, 53, 0.05);
  border-radius: var(--radius-md);
  border: 1px solid rgba(234, 67, 53, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.icon-error {
  font-size: 40px;
}

.retry-btn {
  background-color: var(--error-color);
  color: white;
  padding: 10px 25px;
  margin-top: 15px;
}

.retry-btn:hover {
  background-color: #d33426;
  transform: translateY(-2px);
}

/* 卡片容器 */
.user-info-card {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* 信息卡片样式 */
.info-card {
  background-color: #fff;
  border-radius: var(--radius-md);
  padding: 25px;
  box-shadow: var(--card-shadow);
  transition: var(--transition);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0 0 20px 0;
  font-size: 20px;
  color: var(--text-primary);
  font-weight: 600;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.card-title.no-action {
  justify-content: flex-start; /* 让内容靠左 */
  gap: 10px;                    /* 图标和文字的间距 */
}

.title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.icon-title {
  font-size: 22px;
}

/* 基本信息网格布局 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  padding: 12px 15px;
  background-color: #f8f9fa;
  border-radius: var(--radius-sm);
}

.info-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-weight: 500;
}

.info-value {
  font-size: 16px;
  font-weight: 500;
}

.role-badge {
  display: inline-block;
  padding: 3px 10px;
  background-color: #e0e0e0;
  border-radius: 12px;
  font-size: 14px;
  color: #555;
}

/* 人脸照片区域 */
.face-container {
  padding: 10px 0;
}

.face-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 15px;
}

.face-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.face-img-wrapper {
  width: 180px;
  height: 180px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border-color);
  position: relative;
  transition: var(--transition);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.05);
}

.face-img-wrapper:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.face-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.9);
  border: none;
  color: var(--error-color);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: var(--transition);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.face-img-wrapper:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background-color: white;
  transform: scale(1.1);
}

.face-index {
  font-size: 14px;
  color: var(--text-secondary);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
  background-color: #f9f9f9;
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.icon-empty {
  font-size: 50px;
  opacity: 0.7;
}

/* 表单样式 */
.form-group {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-label {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-input {
  padding: 12px 15px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 16px;
  transition: var(--transition);
  width: 100%;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
}

.form-input::placeholder {
  color: #aaa;
  font-size: 14px;
}

.code-btn {
  width: 100%;
  margin-bottom: 15px;
}

/* 按钮样式 */
.btn {
  padding: 12px 24px;
  border-radius: var(--radius-sm);
  border: none;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-decoration: none;
}

.primary-btn {
  background-color: #d7c480;
  color: black;
  font-weight: 600;
}

.primary-btn:hover {
  background-color: #c9b674;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.primary-btn:active {
  transform: translateY(0);
}

.secondary-btn {
  background-color: #f0f0f0;
  color: var(--text-primary);
}

.secondary-btn:hover {
  background-color: #e0e0e0;
  transform: translateY(-2px);
}

.secondary-btn.disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background-color: #e0e0e0;
  color: #999;
  transform: none !important;
}

.icon-confirm {
  font-size: 18px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .home-container {
    padding: 20px 15px;
    margin-top: 70px;
    border-radius: 0;
  }

  h1 {
    font-size: 24px;
    margin-bottom: 20px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .face-img-wrapper {
    width: 140px;
    height: 140px;
  }

  .form-group {
    gap: 10px;
  }
  
  .code-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .home-container {
    padding: 15px 10px;
  }
  
  .info-card {
    padding: 20px 15px;
  }
  
  .face-img-wrapper {
    width: 120px;
    height: 120px;
  }
  
  .btn {
    padding: 10px 15px;
    font-size: 15px;
  }
}

.basic-info-wrapper {
  position: relative;
  display: flex;
  align-items: flex-start;
}

/* 右侧悬浮拉条 */
.edit-sidebar {
  width: auto;
  height: auto;
  background-color: transparent;
  box-shadow: none;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  position: relative;
}

.edit-handle {
  font-size: 26px;
  margin-bottom: 10px;
  user-select: none;
}

/* 编辑按钮组 */
.edit-options {
  position: absolute;
  top: 30px;
  right: 0;
  background-color: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 1000;
}

.small-btn {
  padding: 6px 8px;
  font-size: 13px;
  border-radius: 6px;
  font-weight: 600;
  white-space: nowrap; /* 防止文字换行 */
}

/* 弹窗样式 */
.edit-dialog::backdrop {
  background: rgba(0,0,0,0.3);
}

.edit-dialog {
  border-radius: 10px;
  padding: 25px;
  width: 350px;
  max-width: 90%;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  border: none;
}

.edit-dialog h3 {
  margin-top: 0;
  margin-bottom: 20px;
  font-weight: 700;
  color: var(--text-primary);
  text-align: center;
}

.edit-dialog input {
  padding: 12px 15px;
  font-size: 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  outline: none;
  transition: 0.3s;
  width: 100%;
  margin-bottom: 15px;
  box-sizing: border-box;
}

.edit-dialog input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 8px rgba(66, 133, 244, 0.3);
}

.dialog-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.dialog-buttons .btn {
  flex: 1;
  padding: 12px;
}

/* 结果弹窗样式 */
.result-dialog::backdrop {
  background: rgba(0,0,0,0.3);
}

.result-dialog {
  border-radius: 10px;
  padding: 30px;
  width: 300px;
  max-width: 90%;
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
  border: none;
  text-align: center;
}

.result-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.result-content h3 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}

.result-content p {
  margin: 0 0 20px 0;
  color: var(--text-secondary);
  font-size: 16px;
}

.icon-success {
  font-size: 50px;
  color: var(--success-color);
  margin-bottom: 10px;
}

.icon-error {
  font-size: 50px;
  color: var(--error-color);
  margin-bottom: 10px;
}

.result-dialog .btn {
  width: 100%;
  padding: 12px;
}

/* 淡入淡出动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>