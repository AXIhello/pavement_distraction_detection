<template>
  <div id="admin">
    <Header ref="headerRef" />

    <main class="centered-content">
      <!-- 用户管理区域 -->
      <div class="admin-container">
        <div class="header-section">
          <h2>
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            用户管理
          </h2>
          <div class="user-count">
            <span>共 {{ users.length }} 位用户</span>
          </div>
        </div>

        <!-- 搜索和添加用户区域 -->
        <div class="filters-card">
          <div class="filters-header">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="22,3 2,3 10,12.46 10,19 14,21 14,12.46"></polygon>
            </svg>
            <span>用户搜索</span>
          </div>
          
          <div class="admin-controls">
            <div class="search-group">
              <select v-model="searchType" class="search-type">
                <option value="name">姓名</option>
                <option value="account">邮箱</option>
                <option value="phone">角色</option>
              </select>
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="输入查询内容" 
                @keyup.enter="handleSearch"
                class="search-input"
              />
              <button @click="handleSearch" class="search-btn btn-primary">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <path d="m21 21-4.35-4.35"></path>
                </svg>
                查询
              </button>
            </div>
          </div>
        </div>

        <!-- 用户列表表格 -->
        <div class="table-card">
          <div class="table-container" v-if="users.length > 0">
            <table class="user-table">
              <thead>
                <tr>
                  <th>序号</th>
                  <th>姓名</th>
                  <th>邮箱</th>
                  <th>角色</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(user, index) in paginatedUsers" :key="user.id" class="user-row">
                  <td>{{ index + 1 + (currentPage - 1) * itemsPerPage }}</td>
                  <td>
                    <span v-if="!user.isEditing">{{ user.name }}</span>
                    <input v-else v-model="user.editedName" type="text" class="edit-input" />
                  </td>
                  <td>
                    <span v-if="!user.isEditing">{{ user.account }}</span>
                    <input v-else v-model="user.editedAccount" type="text" class="edit-input" />
                  </td>
                  <td>
                    <span v-if="!user.isEditing">
                      <span :class="['role-badge', getRoleClass(user.role)]">
                        {{ user.role }}
                      </span>
                    </span>
                    <input v-else v-model="user.editedPhone" type="text" class="edit-input" />
                  </td>
                  <td>
                    <template v-if="!user.isEditing">
                      <button class="edit-btn btn-secondary" @click="startEdit(user)">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                        修改
                      </button>
                      <button class="delete-btn btn-secondary" @click="confirmDelete(user)">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <polyline points="3 6 5 6 21 6"></polyline>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        删除
                      </button>
                    </template>
                    <template v-else>
                      <button class="save-btn btn-primary" @click="saveEdit(user)">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                          <polyline points="17 21 17 13 7 13 7 21"></polyline>
                          <polyline points="7 3 7 8 15 8"></polyline>
                        </svg>
                        保存
                      </button>
                      <button class="cancel-btn btn-secondary" @click="cancelEdit(user)">
                        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <line x1="18" y1="6" x2="6" y2="18"></line>
                          <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                        取消
                      </button>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else class="empty-state">
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="8" y1="15" x2="16" y2="15"></line>
              <line x1="9" y1="9" x2="9.01" y2="9"></line>
              <line x1="15" y1="9" x2="15.01" y2="9"></line>
            </svg>
            <h3>暂无用户数据</h3>
            <p>尝试调整搜索条件或添加新用户</p>
          </div>
        </div>

        <!-- 分页控制 -->
        <div class="pagination-card">
          <div class="pagination">
            <button 
              class="page-btn" 
              @click="prevPage" 
              :disabled="currentPage === 1"
            >
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="15,18 9,12 15,6"></polyline>
              </svg>
              上一页
            </button>
            
            <div class="page-info">
              <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
            </div>
            
            <button 
              class="page-btn" 
              @click="nextPage" 
              :disabled="currentPage === totalPages"
            >
              下一页
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9,18 15,12 9,6"></polyline>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 删除确认弹窗 -->
      <div v-if="showDeleteModal" class="modal-overlay">
        <div class="delete-modal">
          <div class="modal-header">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
            <h3>确认删除</h3>
          </div>
          <p>是否确定删除用户 "{{ userToDelete?.name }}"？</p>
          <div class="modal-buttons">
            <button class="cancel-delete btn-secondary" @click="showDeleteModal = false">取消</button>
            <button class="confirm-delete btn-danger" @click="deleteUser">删除</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Header from '@/components/Navigation.vue'

const router = useRouter()

// 头部导航高度
const headerRef = ref(null)
const headerHeight = ref(64) // 默认预估高度

// 搜索相关
const searchType = ref('name') // 默认按姓名搜索
const searchQuery = ref('')

// 用户数据
const users = ref([])
const allUsers = ref([]) // 用于存储所有用户数据，便于搜索

// 分页相关
const currentPage = ref(1)
const itemsPerPage = 10
const totalPages = computed(() => Math.max(1, Math.ceil(users.value.length / itemsPerPage)))
const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return users.value.slice(start, end)
})

// 删除相关
const showDeleteModal = ref(false)
const userToDelete = ref(null)

// 初始化时获取用户数据
onMounted(async () => {
  // 获取导航栏实际高度
  await nextTick()
  if (headerRef.value?.$el) {
    headerHeight.value = headerRef.value.$el.offsetHeight
  }
  fetchUsers()
})

// 从后端获取用户数据
async function fetchUsers() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/user_admin/', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      }
    })
    const data = await response.json()
    if (data.success) {
      users.value = data.data.map(user => ({
          id: user.id,
          name: user.username, 
          account: user.email, 
          role: user.role,
          isEditing: false,
          editedName: user.username,
          editedAccount: user.email,
          editedPhone: user.phone || ''
      }))
      allUsers.value = [...users.value] // 保存所有用户数据以便搜索
    } else {
      console.error('获取用户数据失败:', data.message)
    }
  } catch (error) {
    console.error('请求用户数据失败:', error)
  }
}

// 获取角色样式类
function getRoleClass(role) {
  const roleMap = {
    'admin': 'admin',
    'user': 'user',
    'guest': 'guest'
  }
  return roleMap[role] || 'default'
}

// 搜索处理
function handleSearch() {
  currentPage.value = 1 // 搜索后重置到第一页
  if (!searchQuery.value) {
    users.value = allUsers.value
    return
  }
  
  // 本地筛选逻辑
  const query = searchQuery.value.toLowerCase()
  users.value = allUsers.value.filter(user => {
    switch (searchType.value) {
      case 'name':
        return user.name.toLowerCase().includes(query)
      case 'account':
        return user.account.toLowerCase().includes(query)
      case 'phone':
        return user.role.toLowerCase().includes(query)
      default:
        return true
    }
  })
}

// 分页控制
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// 编辑用户
function startEdit(user) {
  user.isEditing = true
  user.editedName = user.name
  user.editedAccount = user.account
  user.editedPhone = user.role
}

function cancelEdit(user) {
  user.isEditing = false
}

async function saveEdit(user) {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`http://127.0.0.1:8000/api/user_admin/${user.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token  
      },
      body: JSON.stringify({
        name: user.editedName,
        email: user.editedAccount,
        role: user.editedPhone
      })
    })
    
    const data = await response.json()
    if (data.success) {
      user.name = data.data.username
      user.account = data.data.email
      user.role = data.data.role
      user.isEditing = false
    } else {
      console.error('更新用户信息失败:', data.message)
    }
  } catch (error) {
    console.error('请求更新用户信息失败:', error)
  }
}

// 删除用户
function confirmDelete(user) {
  userToDelete.value = user
  showDeleteModal.value = true
}

async function deleteUser() {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/user_admin/${userToDelete.value.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      }
    })
    
    const data = await response.json()
    if (data.success) {
      users.value = users.value.filter(user => user.id !== userToDelete.value.id)
      allUsers.value = [...users.value]
      showDeleteModal.value = false
    } else {
      console.error('删除用户失败:', data.message)
    }
  } catch (error) {
    console.error('请求删除用户失败:', error)
  }
}

// 跳转到人脸注册页面
function goToFaceRegister() {
  router.push('/face_register')
}

// 监听页码变化
watch(currentPage, () => {
  // 滚动到表格顶部
  const tableContainer = document.querySelector('.table-container')
  if (tableContainer) {
    tableContainer.scrollTop = 0
  }
})
</script>

<style>
#admin {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #fefdf9;
  min-height: 100vh;
}

/* 固定宽度的居中内容容器 */
.centered-content {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 0 20px;
  box-sizing: border-box;
  padding-top: 20px;
  padding-bottom: 20px;
}

.admin-container {
  width: 100%;
  padding-top: calc(20px + var(--header-height, 64px));
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-section h2 {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1f2937;
  font-size: 28px;
  font-weight: 700;
  margin: 0;
}

.user-count {
  background: rgba(255, 255, 255, 0.9);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* 搜索区域样式 */
.filters-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.filters-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  color: #374151;
  font-weight: 600;
  font-size: 16px;
}

.admin-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0;
  gap: 20px;
  flex-wrap: wrap;
}

.search-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 300px;
}

.search-type {
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  background: white;
  font-size: 14px;
  transition: all 0.3s ease;
  min-width: 120px;
}

.search-input {
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid #e5e7eb;
  background: white;
  font-size: 14px;
  transition: all 0.3s ease;
  flex: 1;
  min-width: 200px;
}

.search-type:focus,
.search-input:focus {
  outline: none;
  border-color: #00040a;
  box-shadow: 0 0 0 3px rgba(0, 4, 10, 0.1);
}

/* 按钮样式 */
.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  background: linear-gradient(135deg, #00040a 0%, #1a1a2e 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 4, 10, 0.3);
  white-space: nowrap;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #ebba25 0%, #f4d03f 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(235, 186, 37, 0.4);
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 2px solid #e5e7eb;
  background: white;
  color: #374151;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-secondary:hover {
  border-color: #00040a;
  background: #f9fafb;
  transform: translateY(-1px);
}

.btn-danger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.btn-danger:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(220, 38, 38, 0.4);
}

/* 表格样式 */
.table-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 24px;
}

.table-container {
  overflow-x: auto;
}

.user-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 14px;
}

.user-table th {
  background: linear-gradient(135deg, #f9f4ecfa 0%, #e8d9c9 100%);
  padding: 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.user-row {
  transition: all 0.3s ease;
}

.user-row:hover {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  transform: scale(1.005);
}

.user-table td {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.user-table th:nth-child(1),
.user-table td:nth-child(1) {
  width: 60px; /* 序号 */
}

.user-table th:nth-child(2),
.user-table td:nth-child(2) {
  width: 200px; /* 姓名 */
}

.user-table th:nth-child(3),
.user-table td:nth-child(3) {
  width: 250px; /* 邮箱 */
}

.user-table th:nth-child(4),
.user-table td:nth-child(4) {
  width: 120px; /* 角色 */
}

.user-table th:nth-child(5),
.user-table td:nth-child(5) {
  width: 200px; /* 操作 */
}

.edit-input {
  padding: 8px 12px;
  border-radius: 6px;
  border: 2px solid #e5e7eb;
  background: white;
  font-size: 14px;
  width: 100%;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

.edit-input:focus {
  outline: none;
  border-color: #00040a;
  box-shadow: 0 0 0 3px rgba(0, 4, 10, 0.1);
}

/* 角色标签样式 */
.role-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.role-badge.admin {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.role-badge.user {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.role-badge.guest {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.role-badge.default {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #374151;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* 分页样式 */
.pagination-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #000813 0%, #1a1a2e 100%);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 8, 19, 0.3);
  align-items: center;
  justify-content: center;
}

.page-btn:disabled {
  background: linear-gradient(135deg, #ddb33d 0%, #f4d03f 100%);
  cursor: not-allowed;
  opacity: 0.6;
}

.page-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #030814 0%, #0f172a 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(3, 8, 20, 0.4);
}

.page-info {
  background: rgba(255, 255, 255, 0.8);
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  color: #374151;
  font-weight: 500;
  min-width: 160px; /* 你可以按实际调整 */
  text-align: center;
  white-space: nowrap; /* 强制一行显示 */
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.delete-modal {
  background-color: white;
  padding: 24px;
  border-radius: 16px;
  max-width: 400px;
  width: 90%;
  text-align: center;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 16px;
  color: #dc2626;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.delete-modal p {
  margin-bottom: 24px;
  font-size: 16px;
  color: #374151;
  line-height: 1.5;
}

.modal-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
}

.search-btn {
  width: 100px;            /* 固定宽度 */
  padding: 10px 0;         /* 上下内边距，左右去掉 */
  font-size: 14px;
  border-radius: 8px;
  background: linear-gradient(135deg, #00040a 0%, #1a1a2e 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;  /* 图标和文字水平居中 */
  gap: 6px;
  box-shadow: 0 4px 12px rgba(0, 4, 10, 0.3);
  transition: all 0.3s ease;
  white-space: nowrap;      /* 防止换行 */
}

.search-btn:hover {
  background: linear-gradient(135deg, #ebba25 0%, #f4d03f 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(235, 186, 37, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .admin-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-group {
    width: 100%;
    min-width: auto;
  }
  
  .add-user-btn {
    width: 100%;
    justify-content: center;
  }
  
  .pagination {
    flex-direction: column;
    gap: 16px;
  }
  
  .page-info {
    order: -1;
  }
  
  .user-table th, 
  .user-table td {
    padding: 12px 8px;
  }
  
  .header-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .user-row td:last-child {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .search-group {
    flex-wrap: wrap;
  }
  
  .search-type,
  .search-input,
  .search-btn {
    width: 100%;
  }
}
</style>