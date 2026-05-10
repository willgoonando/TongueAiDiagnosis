<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>🩺 舌诊系统管理</h1>
        <p>请使用管理员账号登录</p>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="0" size="large" @keyup.enter="handleLogin">
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width:100%" @click="handleLogin">
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div v-if="error" class="login-error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/index.js'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const error = ref('')

const form = reactive({
  email: '',
  password: ''
})

const rules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  error.value = ''
  try {
    const res = await login(form.email, form.password)
    if (res.code === 0) {
      // 校验是否是管理员
      const token = res.data?.token
      if (!token) {
        error.value = '登录返回异常，请重试'
        loading.value = false
        return
      }
      const userInfoRes = await fetch('/api/user/info', {
        headers: { Authorization: `Bearer ${token}` }
      }).then(r => r.json())

      if (userInfoRes.code === 0) {
        const user = userInfoRes.data || {}
        // 从 token 里解析 role 或直接获取
        const role = user.role
        if (role !== 1) {
          error.value = '该账号不是管理员，无法登录后台'
          loading.value = false
          return
        }
      }

      localStorage.setItem('admin_token', token)
      localStorage.setItem('admin_user', JSON.stringify({ email: form.email }))
      ElMessage.success('登录成功')
      router.push('/dashboard')
    } else {
      error.value = res.message || res.msg || '登录失败'
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '网络错误'
  }
  loading.value = false
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
.login-header {
  text-align: center;
  margin-bottom: 30px;
}
.login-header h1 {
  margin: 0 0 8px;
  font-size: 22px;
  color: #303133;
}
.login-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}
.login-error {
  color: #f56c6c;
  text-align: center;
  font-size: 14px;
}
</style>
