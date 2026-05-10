<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="admin-sidebar">
      <div class="sidebar-logo">
        <span>🩺 舌诊后台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>系统概览</span>
        </el-menu-item>
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/records">
          <el-icon><Document /></el-icon>
          <span>舌诊记录</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据分析</span>
        </el-menu-item>
        <el-menu-item index="/sessions">
          <el-icon><ChatDotSquare /></el-icon>
          <span>对话管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主区域 -->
    <el-container>
      <el-header class="admin-header">
        <span class="header-title">后台管理系统</span>
        <div class="header-right">
          <span class="header-user">{{ adminEmail }}</span>
          <el-button type="danger" size="small" plain @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { DataAnalysis, User, Document, ChatDotSquare } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const activeMenu = computed(() => route.path)
const adminEmail = computed(() => {
  const info = localStorage.getItem('admin_user')
  if (info) {
    try {
      return JSON.parse(info).email
    } catch {
      return '管理员'
    }
  }
  return '管理员'
})

const handleLogout = async () => {
  await ElMessageBox.confirm('确定退出登录？', '提示')
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_user')
  router.push('/login')
}
</script>

<style scoped>
.admin-sidebar {
  background-color: #304156;
  overflow-y: auto;
}
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}
.header-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-user {
  color: #606266;
  font-size: 14px;
}
.admin-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
