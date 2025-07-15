<template>
    <div id="admin">
      <Header />
  
      <main class="centered-content">
        <!-- 用户管理区域 -->
        <div class="admin-container">
          <h2>用户管理</h2>
  
          <!-- 搜索和添加用户区域 -->
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
              <button @click="handleSearch" class="search-btn">查询</button>
            </div>
            <button class="add-user-btn" @click="goToFaceRegister">添加用户</button>
          </div>
  
          <!-- 用户列表表格 -->
          <div class="user-table-container">
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
                <tr v-for="(user, index) in users" :key="user.id">
                  <td>{{ index + 1 }}</td>
                  <td>
                    <span v-if="!user.isEditing">{{ user.name }}</span>
                    <input v-else v-model="user.editedName" type="text" />
                  </td>
                  <td>
                    <span v-if="!user.isEditing">{{ user.account }}</span>
                    <input v-else v-model="user.editedAccount" type="text" />
                  </td>
                  <td>
                    <span v-if="!user.isEditing">{{ user.role }}</span>
                    <input v-else v-model="user.role" type="tel" />
                  </td>
                  <td>
                    <template v-if="!user.isEditing">
                      <button class="edit-btn" @click="startEdit(user)">修改信息</button>
                      <button class="delete-btn" @click="confirmDelete(user)">删除用户</button>
                    </template>
                    <template v-else>
                      <button class="save-btn" @click="saveEdit(user)">保存信息</button>
                      <button class="cancel-btn" @click="cancelEdit(user)">取消</button>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
  
          <!-- 分页控制 -->
          <div class="pagination">
            <button 
              class="page-btn" 
              @click="prevPage" 
              :disabled="currentPage === 1"
            >上一页</button>
            <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
            <button 
              class="page-btn" 
              @click="nextPage" 
              :disabled="currentPage === totalPages"
            >下一页</button>
          </div>
        </div>
  
        <!-- 删除确认弹窗 -->
        <div v-if="showDeleteModal" class="modal-overlay">
          <div class="delete-modal">
            <p>是否确定删除用户 "{{ userToDelete?.name }}"？</p>
            <div class="modal-buttons">
              <button class="cancel-delete" @click="showDeleteModal = false">取消</button>
              <button class="confirm-delete" @click="deleteUser">删除</button>
            </div>
          </div>
        </div>
      </main>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import Header from '@/components/Navigation.vue'
  import { all } from 'axios'
  
  const router = useRouter()
  
  // 搜索相关
  const searchType = ref('name') // 默认按姓名搜索
  const searchQuery = ref('')
  
  // 用户数据（模拟数据，实际应从后端API获取）
  // const users = ref([
  //   { id: 1, name: '张三', account: 'zhangsan', phone: '13800138001', isEditing: false },
  //   { id: 2, name: '李四', account: 'lisi', phone: '13800138002', isEditing: false },
  //   { id: 3, name: '王五', account: 'wangwu', phone: '13800138003', isEditing: false }
  // ])

  const users = ref([])
  
  // 分页相关
  const currentPage = ref(1)
  const itemsPerPage = 10
  const totalPages = computed(() => Math.ceil(users.value.length / itemsPerPage))
  const paginatedUsers = computed(() => {
    const start = (currentPage.value - 1) * itemsPerPage
    const end = start + itemsPerPage
    return users.value.slice(start, end)
  })
  
  // 删除相关
  const showDeleteModal = ref(false)
  const userToDelete = ref(null)
  
  // 初始化时获取用户数据
  onMounted(() => {
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
            name: user.username, // 👈 匹配模板中用到的 user.name
            account: user.email, // 👈 匹配模板中用到的 user.account
            role: user.role,
            isEditing: false,
            editedName: user.username,
            editedAccount: user.email,
            editedPhone: user.phone || ''
        }))
      } else {
        console.error('获取用户数据失败:', data.message)
      }
    } catch (error) {
      console.error('请求用户数据失败:', error)
    }
  }
  
  const allUsers = ref([]) // 用于存储所有用户数据，便于搜索

  // 搜索处理
  function handleSearch() {
    currentPage.value = 1 // 搜索后重置到第一页
    // 实际应用中可能需要调用API进行搜索
    if (!searchQuery.value) {
      users.value = allUsers.value
      return
    }
    
    // 本地筛选逻辑
    const query = searchQuery.value.toLowerCase()
    users.value = allUsers.value.filter(user => {
      switch (searchType.value) {
        case 'name':
          return user.username.toLowerCase().includes(query)
        case 'account':
          return user.email.toLowerCase().includes(query)
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
    user.editedPhone = user.phone
  }
  
  function cancelEdit(user) {
    user.isEditing = false
  }
  
  async function saveEdit(user) {
    try {
      const token = localStorage.getItem('token')  // 从 localStorage 读取 JWT Token
      const response = await fetch(`http://127.0.0.1:8000/api/user_admin/${user.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + token  // ⬅️ 关键：加上这个
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
      // TODO: 替换为实际的后端API端点
      const response = await fetch(`http://127.0.0.1:8000/api/users/${userToDelete.value.id}`, {
        method: 'DELETE'
      })
      
      const data = await response.json()
      if (data.success) {
        users.value = users.value.filter(user => user.id !== userToDelete.value.id)
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
  </script>
  
  <style>
  #admin {
    font-family: Arial, sans-serif;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  .centered-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    box-sizing: border-box;
  }
  /* 固定 Header */
header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #333;
  color: white;
  padding: 10px 0;
  text-align: center;
  z-index: 1000;
}

/* 页面内容区 */
.admin-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-top: 80px; /* 防止被固定的 header 遮挡 */
}

  
  .admin-container {
    background-color: #fff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  h2 {
    margin-bottom: 20px;
    text-align: center;
    color: #333;
  }
  
  .admin-controls {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
    gap: 20px;
    flex-wrap: wrap;
  }
  
  .search-group {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .search-type {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
  }
  
  .search-input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    min-width: 200px;
  }
  
  .search-btn, .add-user-btn {
    padding: 8px 16px;
    background-color: #333;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
  }
  
  .user-table-container {
    overflow-x: auto;
    margin-bottom: 20px;
    width: 100%;
  }
  
  .user-table {
    width: 100%;
    border-collapse: collapse;
    margin: 0 auto;
  }
  
  .user-table th, .user-table td {
    padding: 12px 15px;
    text-align: center;
    border: 1px solid #ddd;
  }
  
  .user-table th {
    background-color: #f5f5f5;
    font-weight: bold;
  }
  
  .user-table tr:nth-child(even) {
    background-color: #f9f9f9;
  }
  
  .user-table tr:hover {
    background-color: #f1f1f1;
  }
  
  .user-table input {
    padding: 6px 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    width: 90%;
  }
  
  .edit-btn, .save-btn {
    padding: 6px 12px;
    background-color: #333;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 5px;
    white-space: nowrap;
  }
  
  .delete-btn {
    padding: 6px 12px;
    background-color: #ff4d4f;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
  }
  
  .cancel-btn {
    padding: 6px 12px;
    background-color: #ccc;
    color: #333;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-right: 5px;
    white-space: nowrap;
  }
  
  .pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
    margin-top: 20px;
    white-space: nowrap;
  }
  
  .page-btn {
    padding: 8px 16px;
    background-color: #333;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
  }
  
  .page-btn:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  
  .page-info {
    font-size: 14px;
    color: #666;
    display: inline-block;
  }
  
  /* 删除确认弹窗样式 */
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
  }
  
  .delete-modal {
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    max-width: 400px;
    width: 90%;
    text-align: center;
  }
  
  .delete-modal p {
    margin-bottom: 20px;
    font-size: 16px;
  }
  
  .modal-buttons {
    display: flex;
    justify-content: center;
    gap: 15px;
  }
  
  .cancel-delete {
    padding: 8px 16px;
    background-color: #333;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .confirm-delete {
    padding: 8px 16px;
    background-color: #ff4d4f;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  @media (max-width: 768px) {
    .admin-controls {
      flex-direction: column;
      align-items: center;
    }
    
    .search-group {
      width: 100%;
      max-width: 100%;
    }
    
    .add-user-btn {
      width: 100%;
    }
    
    .user-table th, .user-table td {
      padding: 8px;
      font-size: 14px;
    }
    
    .edit-btn, .delete-btn, .save-btn, .cancel-btn {
      padding: 4px 8px;
      font-size: 12px;
    }
  }
  </style>