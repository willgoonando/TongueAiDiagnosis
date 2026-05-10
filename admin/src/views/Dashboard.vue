<template>
  <div class="dashboard">
    <h2 class="page-title">系统概览</h2>
    <div class="stat-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon icon-user">👥</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.user_count }}</div>
          <div class="stat-label">注册用户</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon icon-record">📋</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.analysis_count }}</div>
          <div class="stat-label">舌诊记录</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon icon-success">✅</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.success_analysis }}</div>
          <div class="stat-label">分析成功</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon icon-fail">❌</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.failed_analysis }}</div>
          <div class="stat-label">分析失败</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon icon-chat">💬</div>
        <div class="stat-body">
          <div class="stat-num">{{ stats.chat_count }}</div>
          <div class="stat-label">对话总数</div>
        </div>
      </el-card>
    </div>

    <el-card class="mt-20" shadow="never">
      <template #header>
        <span>快捷操作</span>
      </template>
      <div class="quick-actions">
        <el-button type="primary" @click="$router.push('/users')">用户管理</el-button>
        <el-button type="success" @click="$router.push('/records')">舌诊记录</el-button>
        <el-button type="warning" @click="$router.push('/analysis')">数据分析</el-button>
        <el-button @click="$router.push('/sessions')">对话管理</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats } from '@/api/index.js'

const stats = ref({
  user_count: 0,
  analysis_count: 0,
  session_count: 0,
  chat_count: 0,
  success_analysis: 0,
  failed_analysis: 0
})

onMounted(async () => {
  try {
    const res = await getStats()
    if (res.code === 0) stats.value = res.data
  } catch (e) { /* ignore */ }
})
</script>

<style scoped>
.dashboard { padding: 0; }
.page-title { margin: 0 0 20px; font-size: 20px; color: #303133; }
.stat-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; }
.stat-card { display: flex; align-items: center; }
.stat-card :deep(.el-card__body) { display: flex; align-items: center; width: 100%; padding: 20px; }
.stat-icon { font-size: 36px; margin-right: 16px; line-height: 1; }
.stat-body { flex: 1; }
.stat-num { font-size: 28px; font-weight: bold; color: #303133; line-height: 1.2; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.mt-20 { margin-top: 20px; }
.quick-actions { display: flex; gap: 12px; }
</style>
