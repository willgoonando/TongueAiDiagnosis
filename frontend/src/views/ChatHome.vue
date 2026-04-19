<template>
  <div class="chat-home-container">
    <!-- 左侧侧边栏 -->
    <ChatSidebar 
      :collapsed="sidebarCollapsed"
      @toggle="toggleSidebar"
      @select-session="handleSelectSession"
      @new-chat="handleNewChat"
    />
    
    <!-- 主内容区 -->
    <div class="chat-main-content" :class="{ 'sidebar-expanded': !sidebarCollapsed }">
      <!-- 聊天消息区域（可滚动） -->
      <div class="chat-messages-area">
        <!-- 欢迎区域 -->
        <WelcomeSection v-if="!hasMessages && !currentSessionId" />
        
        <!-- 聊天区域 -->
        <ChatMain 
          v-if="hasMessages || currentSessionId"
          :category="selectedCategory"
          :session-id="currentSessionId"
          :messages="messages"
          @message-updated="handleMessageUpdated"
        />
      </div>
      
      <!-- 输入区域（固定在底部） -->
      <div class="chat-input-area">
        <ChatInput 
          :category="selectedCategory"
          :collapsed="sidebarCollapsed"
          @category-change="handleCategoryChange"
          @send-message="handleSendMessage"
          @send-image="handleSendImage"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import WelcomeSection from '@/components/chat/WelcomeSection.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ChatMain from '@/components/chat/ChatMain.vue'
import axios from 'axios'
import settings from '@/config/config.js'

/** 解析后端 JSON 错误体中的 message（如 OCR/503） */
const readHttpErrorMessage = async (response) => {
  const fallback = `请求失败 (${response.status})`
  try {
    const ct = response.headers.get('content-type') || ''
    if (ct.includes('application/json')) {
      const errData = await response.json()
      if (errData?.message) return errData.message
    }
  } catch (_) {
    /* ignore */
  }
  return fallback
}

const router = useRouter()

// 侧边栏状态
const sidebarCollapsed = ref(false)

// 当前选择的类目
const selectedCategory = ref('coating') // coating, report, drugbox

// 当前会话ID（用于舌苔检测）
const currentSessionId = ref(null)

// 消息列表
const messages = ref([])

// 是否有消息
const hasMessages = computed(() => messages.value.length > 0)

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 切换类目
const handleCategoryChange = (category) => {
  selectedCategory.value = category
  // 切换类目时清空当前会话和消息
  currentSessionId.value = null
  messages.value = []
}

// 选择会话（从侧边栏）
const handleSelectSession = (sessionId) => {
  currentSessionId.value = sessionId
  // 加载会话历史记录
  loadSessionHistory(sessionId)
}

// 新建对话
const handleNewChat = () => {
  currentSessionId.value = null
  messages.value = []
}

// 加载会话历史
const loadSessionHistory = async (sessionId) => {
  const token = localStorage.getItem('token')
  if (!token) return
  
  try {
    const response = await axios.get(`/model/record/${sessionId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (response.data.code === 0 && response.data.data?.records) {
      messages.value = response.data.data.records.map(item => ({
        text: item.content,
        isUser: item.role === 1,
        time: new Date(item.create_at).toLocaleString('default', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        }),
        loading: false,
        isPicture: false
      }))
    }
  } catch (error) {
    console.error('加载会话历史失败:', error)
  }
}

// 发送消息
const handleSendMessage = async (content) => {
  // 检查登录状态
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessageBox.confirm(
      '发送消息需要登录，是否前往登录？',
      '提示',
      {
        confirmButtonText: '去登录',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      router.push('/register')
    }).catch(() => {})
    return
  }
  
  // 添加用户消息
  messages.value.push({
    text: content,
    isUser: true,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: false,
    isPicture: false
  })
  
  // 根据类目调用不同的API
  if (selectedCategory.value === 'coating') {
    // 舌苔检测 - 文本对话
    await sendCoatingMessage(content)
  } else if (selectedCategory.value === 'report') {
    // 报告解读 - 文本
    await sendReportMessage(content)
  } else if (selectedCategory.value === 'drugbox') {
    // 药盒识别 - 文本
    await sendDrugboxMessage(content)
  }
}

// 发送图片
const handleSendImage = async (file, question = '') => {
  // 检查登录状态
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessageBox.confirm(
      '上传图片需要登录，是否前往登录？',
      '提示',
      {
        confirmButtonText: '去登录',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      router.push('/register')
    }).catch(() => {})
    return
  }
  
  // 添加用户消息（显示图片）
  messages.value.push({
    text: question || '[图片]',
    isUser: true,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: false,
    isPicture: true,
    imageFile: file
  })
  
  // 根据类目调用不同的API
  if (selectedCategory.value === 'coating') {
    // 舌苔检测 - 上传图片创建新会话
    await sendCoatingImage(file)
  } else if (selectedCategory.value === 'report') {
    // 报告解读 - 图片
    await sendReportImage(file, question)
  } else if (selectedCategory.value === 'drugbox') {
    // 药盒识别 - 图片
    await sendDrugboxImage(file, question)
  }
}

// 舌苔检测 - 发送文本消息
const sendCoatingMessage = async (content) => {
  if (!currentSessionId.value) {
    // 如果没有会话，需要先创建（但文本消息不能创建会话，需要图片）
    ElMessage.warning('请先上传舌象图片开始对话')
    messages.value.pop() // 移除刚添加的用户消息
    return
  }
  
  const token = localStorage.getItem('token')
  
  // 添加AI回复占位
  messages.value.push({
    text: '',
    isUser: false,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: true,
    isPicture: false,
    receivedContent: false
  })
  
  try {
    const response = await fetch(`${settings.ServerUrl}/api/model/session/${currentSessionId.value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        input: content
      })
    })
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    if (!response.body) throw new Error('流式返回没有body')
    
    await streamResponse(response, messages.value.length - 1)
  } catch (error) {
    console.error('发送消息失败:', error)
    messages.value.pop() // 移除失败的AI消息
    ElMessage.error('发送消息失败，请重试')
  }
}

// 舌苔检测 - 上传图片
const sendCoatingImage = async (file) => {
  const token = localStorage.getItem('token')
  
  // 添加AI回复占位
  messages.value.push({
    text: '',
    isUser: false,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: true,
    isPicture: false,
    receivedContent: false
  })
  
  try {
    const formData = new FormData()
    formData.append('file_data', file)
    formData.append('user_input', '请分析这张舌象图片')
    formData.append('name', `舌诊-${new Date().toLocaleString()}`)
    
    const response = await fetch(`${settings.ServerUrl}/api/model/session`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    if (!response.body) throw new Error('流式返回没有body')
    
    // 流式响应处理，同时尝试从响应中获取session_id
    await streamResponseWithSessionId(response, messages.value.length - 1)
    
    // 如果流式响应结束后还没有session_id，尝试从API获取最新会话
    if (!currentSessionId.value) {
      await loadLatestSession()
    }
  } catch (error) {
    console.error('上传图片失败:', error)
    messages.value.pop()
    ElMessage.error('上传图片失败，请重试')
  }
}

// 加载最新会话
const loadLatestSession = async () => {
  const token = localStorage.getItem('token')
  if (!token) return
  
  try {
    const response = await axios.get('/model/session', {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (response.data.code === 0 && response.data.data && response.data.data.length > 0) {
      // 获取最新的会话
      const latestSession = response.data.data[0]
      currentSessionId.value = latestSession.session_id
    }
  } catch (error) {
    console.error('获取最新会话失败:', error)
  }
}

// 报告解读 - 文本
const sendReportMessage = async (content) => {
  const token = localStorage.getItem('token')
  
  // 添加AI回复占位
  messages.value.push({
    text: '',
    isUser: false,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: true,
    isPicture: false,
    receivedContent: false
  })
  
  try {
    const response = await fetch(`${settings.ServerUrl}/api/extra/report/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ text: content })
    })
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    if (!response.body) throw new Error('流式返回没有body')
    
    await streamResponse(response, messages.value.length - 1)
  } catch (error) {
    console.error('报告解读失败:', error)
    messages.value.pop()
    ElMessage.error('报告解读失败，请重试')
  }
}

// 报告解读 - 图片
const sendReportImage = async (file, question = '') => {
  const token = localStorage.getItem('token')
  
  // 添加AI回复占位
  messages.value.push({
    text: '',
    isUser: false,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: true,
    isPicture: false,
    receivedContent: false
  })
  
  try {
    const formData = new FormData()
    formData.append('file_data', file)
    formData.append('question', question)
    
    const response = await fetch(`${settings.ServerUrl}/api/extra/report/image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })
    
    if (!response.ok) {
      const msg = await readHttpErrorMessage(response)
      messages.value.pop()
      ElMessage.error(msg)
      return
    }
    if (!response.body) throw new Error('流式返回没有body')
    
    await streamResponse(response, messages.value.length - 1)
  } catch (error) {
    console.error('报告解读失败:', error)
    messages.value.pop()
    ElMessage.error('报告解读失败，请重试')
  }
}

// 药盒识别 - 文本
const sendDrugboxMessage = async (content) => {
  const token = localStorage.getItem('token')
  
  // 添加AI回复占位
  messages.value.push({
    text: '',
    isUser: false,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: true,
    isPicture: false,
    receivedContent: false
  })
  
  try {
    const response = await fetch(`${settings.ServerUrl}/api/extra/drugbox/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ 
        text: content,
        question: ''
      })
    })
    
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    if (!response.body) throw new Error('流式返回没有body')
    
    await streamResponse(response, messages.value.length - 1)
  } catch (error) {
    console.error('药盒识别失败:', error)
    messages.value.pop()
    ElMessage.error('药盒识别失败，请重试')
  }
}

// 药盒识别 - 图片
const sendDrugboxImage = async (file, question = '') => {
  const token = localStorage.getItem('token')
  
  // 添加AI回复占位
  messages.value.push({
    text: '',
    isUser: false,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: true,
    isPicture: false,
    receivedContent: false
  })
  
  try {
    const formData = new FormData()
    formData.append('file_data', file)
    formData.append('question', question)
    
    const response = await fetch(`${settings.ServerUrl}/api/extra/drugbox/image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })
    
    if (!response.ok) {
      const msg = await readHttpErrorMessage(response)
      messages.value.pop()
      ElMessage.error(msg)
      return
    }
    if (!response.body) throw new Error('流式返回没有body')
    
    await streamResponse(response, messages.value.length - 1)
  } catch (error) {
    console.error('药盒识别失败:', error)
    messages.value.pop()
    ElMessage.error('药盒识别失败，请重试')
  }
}

// 流式响应处理
const streamResponse = async (response, messageIndex) => {
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let done = false
  
  while (!done) {
    const { value, done: readerDone } = await reader.read()
    done = readerDone
    
    if (value) {
      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (!line.trim()) continue
        
        try {
          const parsed = JSON.parse(line)
          if (parsed?.token && parsed?.is_complete === false) {
            const currentMessage = messages.value[messageIndex]
            if (!currentMessage.receivedContent) {
              currentMessage.receivedContent = true
              currentMessage.loading = false
            }
            currentMessage.text += parsed.token
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  }
  
  // 流结束
  if (messages.value[messageIndex]) {
    messages.value[messageIndex].loading = false
  }
}

// 流式响应处理（带session_id提取）
const streamResponseWithSessionId = async (response, messageIndex) => {
  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let done = false
  
  while (!done) {
    const { value, done: readerDone } = await reader.read()
    done = readerDone
    
    if (value) {
      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (!line.trim()) continue
        
        try {
          const parsed = JSON.parse(line)
          
          // 尝试从响应中提取session_id（可能在流式响应的某个chunk中）
          if (parsed?.session_id && !currentSessionId.value) {
            currentSessionId.value = parsed.session_id
          }
          
          // 也检查其他可能的字段名
          if (parsed?.data?.session_id && !currentSessionId.value) {
            currentSessionId.value = parsed.data.session_id
          }
          
          // 处理token流
          if (parsed?.token && parsed?.is_complete === false) {
            const currentMessage = messages.value[messageIndex]
            if (!currentMessage.receivedContent) {
              currentMessage.receivedContent = true
              currentMessage.loading = false
            }
            currentMessage.text += parsed.token
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  }
  
  // 流结束
  if (messages.value[messageIndex]) {
    messages.value[messageIndex].loading = false
  }
}

// 消息更新处理
const handleMessageUpdated = (updatedMessages) => {
  messages.value = updatedMessages
}

onMounted(() => {
  // 组件挂载时的初始化
})
</script>

<style scoped>
.chat-home-container {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  background: linear-gradient(135deg, #f0f9ff 0%, #fdf2ff 100%);
  position: relative;
}

.chat-main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
  margin-left: 260px;
  overflow: hidden;
  height: 100vh;
}

.chat-main-content.sidebar-expanded {
  margin-left: 260px;
}

.chat-main-content:not(.sidebar-expanded) {
  margin-left: 60px;
}

.chat-messages-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(to bottom, 
    rgba(240, 249, 255, 0.3) 0%, 
    rgba(253, 242, 255, 0.2) 100%);
}

.chat-input-area {
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.95);
  border-top: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
  z-index: 10;
  position: relative;
  min-height: 200px;
  display: block;
  visibility: visible;
}

@media (max-width: 768px) {
  .chat-main-content {
    margin-left: 0;
  }
  
  .chat-main-content.sidebar-expanded {
    margin-left: 0;
  }
}
</style>

