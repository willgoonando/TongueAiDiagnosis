<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <div>
        <el-button @click="handleExport">导出 CSV</el-button>
        <el-button type="primary" @click="showCreate = true">+ 新增用户</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <div class="table-toolbar">
        <el-input v-model="keyword" placeholder="搜索邮箱" clearable style="width:260px" @clear="fetchUsers" @keyup.enter="fetchUsers" />
        <el-button type="primary" @click="fetchUsers">搜索</el-button>
      </div>

      <el-table :data="users" stripe border v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 1 ? 'danger' : 'info'" size="small">
              {{ row.role === 1 ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
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
          @current-change="fetchUsers"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showCreate" :title="editingUser ? '编辑用户' : '新增用户'" width="420px" @close="resetForm">
      <el-form :model="form" ref="formRef" label-width="70px">
        <el-form-item label="邮箱" prop="email" :rules="[{ required: true, message: '请输入邮箱' }]">
          <el-input v-model="form.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item label="密码" prop="password" :rules="editingUser ? [] : [{ required: true, message: '请输入密码' }]">
          <el-input v-model="form.password" type="password" placeholder="留空则不修改（编辑时）" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width:100%">
            <el-option :value="0" label="普通用户" />
            <el-option :value="1" label="管理员" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getUsers, createUser, updateUser, deleteUser, exportUsers, downloadBlob } from '@/api/index.js'

const users = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const showCreate = ref(false)
const editingUser = ref(null)
const saving = ref(false)
const formRef = ref(null)

const form = ref({ email: '', password: '', role: 0 })

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await getUsers(page.value, pageSize.value, keyword.value)
    if (res.code === 0) {
      users.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  }
  loading.value = false
}

const handleEdit = (user) => {
  editingUser.value = user
  form.value = { email: user.email, password: '', role: user.role }
  showCreate.value = true
}

const handleDelete = async (user) => {
  await ElMessageBox.confirm(`确定删除用户「${user.email}」？关联的舌诊记录和对话也会被删除。`, '警告', { type: 'warning' })
  const res = await deleteUser(user.id)
  if (res.code === 0) {
    ElMessage.success('删除成功')
    fetchUsers()
  } else {
    ElMessage.error(res.message || '删除失败')
  }
}

const handleSave = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingUser.value) {
      const res = await updateUser(editingUser.value.id, form.value)
      if (res.code === 0) {
        ElMessage.success('更新成功')
        showCreate.value = false
        fetchUsers()
      } else {
        ElMessage.error(res.message || '更新失败')
      }
    } else {
      const res = await createUser(form.value.email, form.value.password, form.value.role)
      if (res.code === 0) {
        ElMessage.success('创建成功')
        showCreate.value = false
        fetchUsers()
      } else {
        ElMessage.error(res.message || '创建失败')
      }
    }
  } catch (e) { ElMessage.error('操作失败') }
  saving.value = false
}

const resetForm = () => {
  editingUser.value = null
  form.value = { email: '', password: '', role: 0 }
  formRef.value?.resetFields()
}

const handleExport = async () => {
  try {
    const res = await exportUsers(page.value, pageSize.value, keyword.value);
    downloadBlob(res, 'users_page' + page.value + '.csv');
  } catch (e) {
    ElMessage.error('\u5bfc\u51fa\u5931\u8d25');
  }
};

onMounted(fetchUsers)
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
</style>
