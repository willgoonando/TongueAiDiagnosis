<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">对话管理</h2>
    </div>

    <el-card shadow="never">
      <div class="table-toolbar">
        <el-select v-model="userId" placeholder="筛选用户" clearable style="width:180px" @change="handleUserFilter">
          <el-option
            v-for="u in userList"
            :key="u.id"
            :label="`${u.email} (ID:${u.id})`"
            :value="u.id"
          />
        </el-select>
        <el-input v-model="keyword" placeholder="搜索邮箱或会话标题" clearable style="width:280px" @clear="fetchSessions" @keyup.enter="fetchSessions" />
        <el-button type="primary" @click="fetchSessions">搜索</el-button>
        <el-button @click="handleExport">导出 CSV</el-button>
      </div>

      <el-table :data="sessions" stripe border v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="email" label="用户" min-width="140" />
        <el-table-column prop="title" label="会话标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="handleView(row)">查看详情</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchSessions"
        />
      </div>
    </el-card>

    <!-- 对话详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="50%" direction="rtl">
      <div v-if="loadingDetail" style="text-align:center; padding:40px">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <p style="color:#909399; margin-top:12px">加载中...</p>
      </div>
      <div v-else class="chat-log">
        <div
          v-for="(msg, i) in detailRecords"
          :key="msg.id"
          class="chat-msg"
          :class="msg.role"
        >
          <div class="msg-bubble">
            <div class="msg-meta">
              <el-tag :type="msg.role === 'user' ? '' : 'success'" size="small" round>
                {{ msg.role === 'user' ? '用户' : 'AI' }}
              </el-tag>
              <span class="msg-time">{{ formatTime(msg.time) }}</span>
            </div>
            <div class="msg-text">{{ msg.content || '(空)' }}</div>
          </div>
        </div>
        <div v-if="!detailRecords.length" style="text-align:center;color:#909399;padding:40px">
          暂无对话记录
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { getChatSessions, getChatSessionDetail, deleteChatSession, getUsers, exportChatSessions, downloadBlob } from '@/api/index.js'

const sessions = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const userId = ref(null)
const userList = ref([])

const drawerVisible = ref(false)
const drawerTitle = ref('')
const loadingDetail = ref(false)
const detailRecords = ref([])

const fetchUsers = async () => {
  try {
    const res = await getUsers(1, 200, '')
    if (res.code === 0) {
      userList.value = res.data.list
    }
  } catch (e) { /* ignore */ }
}

// 切换用户筛选时重置到第一页并清除关键词
const handleUserFilter = (val) => {
  page.value = 1
  keyword.value = ''
  if (val === '' || val === undefined || val === null) {
    userId.value = null
  } else {
    userId.value = Number(val)
  }
  fetchSessions()
}

const fetchSessions = async () => {
  loading.value = true
  try {
    const res = await getChatSessions(page.value, pageSize.value, keyword.value, userId.value)
    if (res.code === 0) {
      sessions.value = [...(res.data.list || [])]
      total.value = res.data.total
    }
  } catch (e) { ElMessage.error('获取会话列表失败') }
  loading.value = false
}

const handleView = async (row) => {
  drawerTitle.value = `对话详情 - ${row.title || `#${row.id}`}`
  drawerVisible.value = true
  loadingDetail.value = true
  detailRecords.value = []
  try {
    const res = await getChatSessionDetail(row.id)
    if (res.code === 0) {
      detailRecords.value = res.data.records || []
    }
  } catch (e) { ElMessage.error('获取对话详情失败') }
  loadingDetail.value = false
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除会话「${row.title || '#'+row.id}」？对话内容也会一并删除。`, '警告', { type: 'warning' })
  const res = await deleteChatSession(row.id)
  if (res.code === 0) {
    ElMessage.success('删除成功')
    fetchSessions()
  } else {
    ElMessage.error(res.message || '删除失败')
  }
}

const formatTime = (ts) => {
  if (!ts) return '-'
  const d = new Date(ts)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
}

const handleExport = async () => {
  try {
    const res = await exportChatSessions(page.value, pageSize.value, keyword.value, userId.value);
    downloadBlob(res, 'sessions_page' + page.value + '.csv');
  } catch (e) {
    ElMessage.error('导出失败');
  }
};

onMounted(() => {
  fetchSessions()
  fetchUsers()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-title { margin: 0; font-size: 20px; color: #303133; }
.table-toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}
.table-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.chat-log { padding: 0 8px; }
.chat-msg {
  margin-bottom: 16px;
  display: flex;
}
.chat-msg.user { justify-content: flex-start; }
.chat-msg.assistant { justify-content: flex-start; }
.msg-bubble {
  max-width: 90%;
  padding: 12px 16px;
  border-radius: 8px;
  background: #f5f7fa;
}
.chat-msg.assistant .msg-bubble {
  background: #ecf5ff;
}
.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.msg-time {
  font-size: 12px;
  color: #c0c4cc;
}
.msg-text {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
