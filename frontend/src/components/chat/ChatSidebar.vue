<template>
  <el-aside 
    :width="collapsed ? '60px' : '260px'" 
    class="chat-sidebar"
    :class="{ 'collapsed': collapsed }"
  >
    <div class="sidebar-content">
      <!-- Logo区域 -->
      <div class="sidebar-header">
        <div class="logo-section" @click="toggleCollapse">
          <div class="logo-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L15.09 8.26L22 9L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9L8.91 8.26L12 2Z"
                    fill="currentColor"/>
            </svg>
          </div>
          <div v-if="!collapsed" class="logo-text">
            <div class="logo-title">舌诊助手</div>
            <div class="logo-subtitle">AI智能诊断</div>
          </div>
        </div>
      </div>

      <!-- 开启新对话按钮 -->
      <div class="new-chat-section">
        <el-button 
          type="primary" 
          :icon="Plus" 
          @click="handleNewChat"
          :class="{ 'collapsed-button': collapsed }"
        >
          <span v-if="!collapsed">开启新对话</span>
          <span v-if="!collapsed" class="shortcut-hint">Ctrl K</span>
        </el-button>
      </div>

      <!-- 对话记录 -->
      <div class="conversation-section">
        <div v-if="!collapsed" class="section-header">
          <div class="section-title">对话记录</div>
          <div class="section-subtitle">最近7天</div>
        </div>
        <el-scrollbar class="conversation-list">
          <div 
            v-for="session in sessions" 
            :key="session.id"
            class="conversation-item"
            :class="{ 'active': activeSessionId === session.id }"
            @click="handleSelectSession(session.id)"
          >
            <el-icon class="conversation-icon"><ChatDotRound /></el-icon>
            <span v-if="!collapsed" class="conversation-title">{{ session.name }}</span>
          </div>
          <div v-if="sessions.length === 0 && !collapsed" class="empty-state">
            暂无对话记录
          </div>
        </el-scrollbar>
      </div>

      <!-- 底部链接 -->
      <div class="sidebar-footer">
        <div 
          v-if="!collapsed" 
          class="footer-link"
          @click="handleOpenPlatform"
        >
          <el-icon><Link /></el-icon>
          <span>舌诊助手开放平台</span>
        </div>
        <div 
          v-if="!collapsed" 
          class="footer-link"
          @click="handleDownload"
        >
          <el-icon><Download /></el-icon>
          <span>下载手机版</span>
        </div>
        <!-- 未登录时显示登录按钮 -->
        <div 
          v-if="!isAuthenticated"
          class="footer-link login-link"
          @click="handleLogin"
        >
          <el-icon><User /></el-icon>
          <span v-if="!collapsed">点击登录</span>
        </div>
        
        <!-- 已登录时显示用户下拉菜单 -->
        <el-dropdown 
          v-else
          trigger="click"
          placement="top"
          @command="handleUserCommand"
        >
          <div class="footer-link login-link user-dropdown-trigger">
            <el-icon><User /></el-icon>
            <span v-if="!collapsed">{{ userInfo.email || userInfo.name || '已登录' }}</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled class="user-info-item">
                <div class="user-info-display">
                  <el-icon><User /></el-icon>
                  <span>{{ userInfo.email || userInfo.name || '用户' }}</span>
                </div>
              </el-dropdown-item>
              <el-dropdown-item command="pipeline" class="pipeline-item">
                <el-icon><Monitor /></el-icon>
                <span>🔬 流水线展示</span>
              </el-dropdown-item>
              <el-dropdown-item divided command="logout" class="logout-item">
                <el-icon><SwitchButton /></el-icon>
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </el-aside>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, ChatDotRound, Link, Download, User, SwitchButton, Monitor } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle', 'select-session', 'new-chat'])

const router = useRouter()

// 会话列表
const sessions = ref([])
const activeSessionId = ref(null)

// 用户信息
const isAuthenticated = ref(false)
const userInfo = ref({
  name: '',
  email: ''
})

// 切换收缩
const toggleCollapse = () => {
  emit('toggle')
}

// 新建对话
const handleNewChat = () => {
  activeSessionId.value = null
  emit('new-chat')
}

// 选择会话
const handleSelectSession = (sessionId) => {
  activeSessionId.value = sessionId
  emit('select-session', sessionId)
}

// 加载会话列表
const loadSessions = async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    sessions.value = []
    return
  }
  
  try {
    const response = await axios.get('/model/session', {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 40000
    })
    
    if (response.data.code === 0 && response.data.data) {
      sessions.value = response.data.data.map(item => ({
        id: item.session_id,
        name: item.name,
        create_at: item.create_at
      }))
    }
  } catch (error) {
    console.error('加载会话列表失败:', error)
    sessions.value = []
  }
}

// 加载用户信息（添加防抖和重复请求检查）
let loadUserInfoTimer = null
const loadUserInfo = async () => {
  // 防抖：300ms 内只执行一次
  if (loadUserInfoTimer) {
    clearTimeout(loadUserInfoTimer)
  }
  loadUserInfoTimer = setTimeout(async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      isAuthenticated.value = false
      return
    }
    
    // 如果正在加载，跳过
    if (isLoadingUserInfo) return
    
    try {
      isLoadingUserInfo = true
      const response = await axios.get('/user/info', {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      if (response.data.code === 0) {
        isAuthenticated.value = true
        if (response.data.data) {
          userInfo.value = { ...userInfo.value, ...response.data.data, name: response.data.data.email || userInfo.name }
        }
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      isAuthenticated.value = false
      localStorage.removeItem('token')
    } finally {
      isLoadingUserInfo = false
    }
  }, 300)
}

// 登录
const handleLogin = () => {
  if (isAuthenticated.value) {
    // 已登录，显示用户菜单（可以扩展）
    return
  }
  router.push('/register')
}

// 处理用户菜单命令
const handleUserCommand = async (command) => {
  if (command === 'pipeline') {
    // 跳转到流水线展示页面
    window.open(`${window.location.origin}/#/pipeline`, '_blank')
    return
  }
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm(
        '确定要退出登录吗？',
        '提示',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
      
      // 清除token和用户信息
      localStorage.removeItem('token')
      isAuthenticated.value = false
      userInfo.value = {
        name: '',
        email: ''
      }
      sessions.value = []
      
      ElMessage.success('已退出登录')
      
      // 刷新页面或跳转到登录页
      router.push('/register')
    } catch {
      // 用户取消
    }
  }
}

// 开放平台
const handleOpenPlatform = () => {
  ElMessage.info('开放平台功能开发中')
}

// 下载
const handleDownload = () => {
  ElMessage.info('手机版下载功能开发中')
}

// 监听登录状态变化（修复：使用 ref 来正确监听 localStorage 变化）
const tokenRef = ref(localStorage.getItem('token'))
watch(tokenRef, (newToken, oldToken) => {
  if (newToken !== oldToken) {
    loadUserInfo()
    loadSessions()
  }
})

// 监听 storage 事件（跨标签页同步）
window.addEventListener('storage', (e) => {
  if (e.key === 'token') {
    tokenRef.value = e.newValue
  }
})

// 监听 localStorage 变化（同标签页内）
const originalSetItem = localStorage.setItem
localStorage.setItem = function(key, value) {
  if (key === 'token') {
    tokenRef.value = value
  }
  originalSetItem.apply(this, arguments)
}

const originalRemoveItem = localStorage.removeItem
localStorage.removeItem = function(key) {
  if (key === 'token') {
    tokenRef.value = null
  }
  originalRemoveItem.apply(this, arguments)
}

// 添加请求标记，避免重复请求
let isLoadingUserInfo = false
let isLoadingSessions = false

onMounted(() => {
  // 只在未加载时才加载
  if (!isLoadingUserInfo) {
    isLoadingUserInfo = true
    loadUserInfo().finally(() => {
      isLoadingUserInfo = false
    })
  }
  if (!isLoadingSessions) {
    isLoadingSessions = true
    loadSessions().finally(() => {
      isLoadingSessions = false
    })
  }
  
  // 监听键盘快捷键 Ctrl+K
  const handleKeyDown = (e) => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault()
      handleNewChat()
    }
  }
  window.addEventListener('keydown', handleKeyDown)
  
  // 清理
  return () => {
    window.removeEventListener('keydown', handleKeyDown)
  }
})
</script>

<style scoped>
.chat-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  background: linear-gradient(180deg, #f0f9ff 0%, #fdf2ff 100%);
  border-right: 1px solid rgba(226, 232, 240, 0.9);
  transition: width 0.3s ease;
  z-index: 100;
  overflow: hidden;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px;
}

.sidebar-header {
  margin-bottom: 16px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.logo-section:hover {
  background: rgba(102, 126, 234, 0.1);
}

.logo-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  flex-shrink: 0;
}

.logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.logo-title {
  font-size: 1rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1.2;
}

.logo-subtitle {
  font-size: 0.75rem;
  color: #667eea;
  line-height: 1.2;
}

.new-chat-section {
  margin-bottom: 16px;
}

.new-chat-section :deep(.el-button) {
  width: 100%;
  justify-content: flex-start;
  position: relative;
}

.collapsed-button {
  padding: 0 !important;
  width: 40px !important;
  min-width: 40px !important;
}

.shortcut-hint {
  position: absolute;
  right: 8px;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.conversation-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-header {
  margin-bottom: 8px;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.section-subtitle {
  font-size: 0.75rem;
  color: #8b95a1;
}

.conversation-list {
  flex: 1;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  color: #5a6c7d;
}

.conversation-item:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.conversation-item.active {
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.conversation-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.conversation-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.875rem;
}

.empty-state {
  text-align: center;
  color: #8b95a1;
  font-size: 0.875rem;
  padding: 20px;
}

.sidebar-footer {
  border-top: 1px solid rgba(226, 232, 240, 0.9);
  padding-top: 12px;
  margin-top: 12px;
}

.footer-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #5a6c7d;
  font-size: 0.875rem;
  margin-bottom: 4px;
}

.footer-link:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.login-link {
  color: #667eea;
  font-weight: 500;
}

.user-dropdown-trigger {
  cursor: pointer;
}

.user-info-display {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #2c3e50;
}

.user-info-item {
  cursor: default;
}

.logout-item {
  color: #f56565;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logout-item:hover {
  background-color: #fee;
}

.pipeline-item {
  color: #667eea;
  display: flex;
  align-items: center;
  gap: 8px;
}

.pipeline-item:hover {
  background-color: #eef2ff;
}

.chat-sidebar.collapsed .logo-text,
.chat-sidebar.collapsed .section-header,
.chat-sidebar.collapsed .conversation-title,
.chat-sidebar.collapsed .footer-link span {
  display: none;
}

.chat-sidebar.collapsed .logo-section {
  justify-content: center;
}

.chat-sidebar.collapsed .conversation-item {
  justify-content: center;
  padding: 10px;
}

.chat-sidebar.collapsed .footer-link {
  justify-content: center;
  padding: 10px;
}
</style>

