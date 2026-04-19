<template>
  <div class="new-login-container">
    <!-- 左侧品牌展示区 -->
    <div class="brand-section">
      <div class="brand-content">
        <div class="brand-logo">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L15.09 8.26L22 9L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9L8.91 8.26L12 2Z"
                  fill="url(#logoGradient)" opacity="0.9"/>
            <defs>
              <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="brand-title">舌诊助手</h1>
        <p class="brand-subtitle">AI智能诊断平台</p>
        <div class="brand-features">
          <div class="feature-item">
            <el-icon class="feature-icon"><DocumentChecked /></el-icon>
            <span>智能舌象分析</span>
          </div>
          <div class="feature-item">
            <el-icon class="feature-icon"><Reading /></el-icon>
            <span>专业报告解读</span>
          </div>
          <div class="feature-item">
            <el-icon class="feature-icon"><Box /></el-icon>
            <span>药盒智能识别</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单区 -->
    <div class="form-section">
      <div class="form-wrapper">
        <div class="form-header">
          <h2 class="form-title">{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
          <p class="form-subtitle">{{ isLogin ? '登录您的账号以继续使用AI舌诊服务' : '注册新账号，开启AI舌诊之旅' }}</p>
        </div>

        <!-- 登录表单 -->
        <div v-if="isLogin" class="login-form">
          <el-form 
            ref="loginFormRef" 
            :model="loginForm" 
            :rules="loginRules"
            label-position="top"
            size="large"
          >
            <el-form-item label="邮箱地址" prop="email">
              <el-input
                v-model="loginForm.email"
                placeholder="请输入您的邮箱"
                clearable
              >
                <template #prefix>
                  <el-icon><Message /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入您的密码"
                show-password
                clearable
                @keyup.enter="handleLogin"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                :loading="loading"
                @click="handleLogin"
                class="submit-button"
              >
                {{ loading ? '登录中...' : '登录' }}
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 注册表单 -->
        <div v-else class="register-form">
          <el-form 
            ref="registerFormRef" 
            :model="registerForm" 
            :rules="registerRules"
            label-position="top"
            size="large"
          >
            <el-form-item label="邮箱地址" prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="请输入您的邮箱"
                clearable
              >
                <template #prefix>
                  <el-icon><Message /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码（6-20位字母或数字）"
                show-password
                clearable
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                show-password
                clearable
                @keyup.enter="handleRegister"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                :loading="loading"
                @click="handleRegister"
                class="submit-button"
              >
                {{ loading ? '注册中...' : '注册' }}
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 切换登录/注册 -->
        <div class="form-footer">
          <span class="switch-text">
            {{ isLogin ? '还没有账号？' : '已有账号？' }}
          </span>
          <el-button 
            type="primary" 
            link 
            @click="toggleMode"
            class="switch-button"
          >
            {{ isLogin ? '立即注册' : '立即登录' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DocumentChecked, Reading, Box, Message, Lock, User } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()

// 表单模式
const isLogin = ref(true)
const loading = ref(false)

// 表单引用
const loginFormRef = ref(null)
const registerFormRef = ref(null)

// 登录表单
const loginForm = reactive({
  email: '',
  password: ''
})

// 注册表单（后端只需要email和password）
const registerForm = reactive({
  email: '',
  password: '',
  confirmPassword: ''
})

// 登录验证规则
const loginRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度为6-20位', trigger: 'blur' }
  ]
}

// 注册验证规则
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validatePassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else if (value.length < 6) {
    callback(new Error('密码长度至少6位'))
  } else if (value.length > 20) {
    callback(new Error('密码长度不能超过20位'))
  } else if (!/^[a-zA-Z0-9]+$/.test(value)) {
    callback(new Error('密码只能包含字母和数字'))
  } else {
    callback()
  }
}

const registerRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, validator: validatePassword, trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 切换登录/注册模式
const toggleMode = () => {
  isLogin.value = !isLogin.value
  // 清空表单
  if (loginFormRef.value) loginFormRef.value.resetFields()
  if (registerFormRef.value) registerFormRef.value.resetFields()
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('email', loginForm.email)
      formData.append('password', loginForm.password)
      
      const response = await axios({
        method: 'put',
        url: '/user/login',
        data: formData,
        timeout: 20000
      })
      
      if (response.data.code === 0) {
        localStorage.setItem('token', response.data.data.token)
        ElMessage.success('登录成功')
        // 跳转到新的聊天界面
        router.push('/')
      } else {
        if (response.data.code === 101) {
          ElMessage.error('用户不存在')
        } else if (response.data.code === 102) {
          ElMessage.error('密码错误')
        } else {
          ElMessage.error('登录失败，请重试')
        }
      }
    } catch (error) {
      if (error.message === 'ECONNABORTED') {
        ElMessage.error('请求超时，请重试')
      } else {
        ElMessage.error('登录失败，请重试')
      }
      console.error('登录错误:', error)
    } finally {
      loading.value = false
    }
  })
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      // 后端API只接受 email 和 password，使用JSON格式（与旧组件保持一致）
      const response = await axios.post('/user/register', {
        email: registerForm.email,
        password: registerForm.password
      }, {
        timeout: 20000
      })
      
      if (response.data.code === 0) {
        ElMessage.success('注册成功，请登录')
        // 切换到登录模式
        isLogin.value = true
        loginForm.email = registerForm.email
        // 清空注册表单
        registerFormRef.value.resetFields()
      } else {
        if (response.data.code === 101) {
          ElMessage.error('该账号已被注册')
        } else {
          ElMessage.error('注册失败，请重试')
        }
      }
    } catch (error) {
      // 详细的错误处理和调试信息
      console.error('========== 注册错误详情 ==========')
      console.error('错误对象:', error)
      console.error('错误响应:', error.response?.data)
      console.error('错误状态码:', error.response?.status)
      console.error('请求URL:', error.config?.url)
      console.error('请求数据:', { email: registerForm.email, password: '***' })
      console.error('================================')
      
      if (error.response) {
        // 服务器返回了错误响应
        const errorData = error.response.data
        if (errorData && errorData.code === 101) {
          ElMessage.error('该账号已被注册')
        } else if (errorData && errorData.message) {
          ElMessage.error(`注册失败: ${errorData.message}`)
        } else if (error.response.status === 422) {
          ElMessage.error('数据格式错误，请检查输入')
        } else {
          ElMessage.error(`注册失败 (状态码: ${error.response.status})`)
        }
      } else if (error.code === 'ECONNABORTED' || error.message === 'ECONNABORTED') {
        ElMessage.error('请求超时，请重试')
      } else if (error.message) {
        ElMessage.error(`注册失败: ${error.message}`)
      } else {
        ElMessage.error('注册失败，请检查网络连接')
      }
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.new-login-container {
  display: flex;
  height: 100vh;
  width: 100%;
  background: linear-gradient(135deg, #f0f9ff 0%, #fdf2ff 100%);
}

.brand-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  position: relative;
  overflow: hidden;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
  animation: rotate 20s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.brand-content {
  position: relative;
  z-index: 1;
  text-align: center;
  max-width: 500px;
}

.brand-logo {
  margin-bottom: 32px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.brand-title {
  font-size: 3rem;
  font-weight: 700;
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 12px;
  line-height: 1.2;
}

.brand-subtitle {
  font-size: 1.25rem;
  color: #4b5563;
  margin-bottom: 48px;
  font-weight: 500;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.feature-item {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.2);
}

.feature-icon {
  font-size: 24px;
  color: #667eea;
}

.feature-item span {
  font-size: 1rem;
  color: #2c3e50;
  font-weight: 500;
}

.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.form-title {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 8px;
}

.form-subtitle {
  font-size: 0.95rem;
  color: #6b7280;
}

.login-form,
.register-form {
  margin-bottom: 24px;
}

:deep(.el-form-item__label) {
  color: #374151;
  font-weight: 500;
  margin-bottom: 8px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.2);
}

:deep(.el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.submit-button {
  width: 100%;
  height: 48px;
  font-size: 1rem;
  font-weight: 600;
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  transition: all 0.3s;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.form-footer {
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid rgba(226, 232, 240, 0.9);
}

.switch-text {
  color: #6b7280;
  font-size: 0.95rem;
  margin-right: 8px;
}

.switch-button {
  font-weight: 600;
  color: #667eea;
}

.switch-button:hover {
  color: #764ba2;
}

@media (max-width: 968px) {
  .new-login-container {
    flex-direction: column;
  }
  
  .brand-section {
    flex: 0 0 auto;
    padding: 40px 20px;
  }
  
  .brand-title {
    font-size: 2rem;
  }
  
  .brand-features {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .feature-item {
    flex: 1;
    min-width: 140px;
  }
  
  .form-section {
    flex: 1;
    padding: 20px;
  }
}
</style>

