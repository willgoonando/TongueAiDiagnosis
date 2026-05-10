<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">舌诊记录管理</h2>
    </div>

    <el-card shadow="never">
      <div class="table-toolbar">
        <el-select v-model="stateFilter" placeholder="状态筛选" clearable style="width:140px" @change="fetchRecords">
          <el-option label="全部" :value="null" />
          <el-option label="分析成功" :value="1" />
          <el-option label="处理中" :value="0" />
          <el-option label="失败" :value="200" />
        </el-select>
        <el-button @click="handleExport">导出 CSV</el-button>
        <el-button type="primary" @click="fetchRecords">刷新</el-button>
      </div>

      <el-table :data="records" stripe border v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="user_id" label="用户ID" width="80" />
        <el-table-column prop="email" label="用户邮箱" min-width="160" />
        <el-table-column prop="img_src" label="图片路径" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.state === 1" type="success" size="small">成功</el-tag>
            <el-tag v-else-if="row.state === 0" type="warning" size="small">处理中</el-tag>
            <el-tag v-else type="danger" size="small">失败({{ row.state }})</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="舌色" width="100">
          <template #default="{ row }">
            {{ row.tongue_color != null ? colorLabels[row.tongue_color] : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="苔色" width="100">
          <template #default="{ row }">
            {{ row.coating_color != null ? coatingLabels[row.coating_color] : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="厚薄" width="80">
          <template #default="{ row }">
            {{ row.tongue_thickness != null ? (row.tongue_thickness === 1 ? '厚' : '薄') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="腐腻" width="80">
          <template #default="{ row }">
            {{ row.rot_greasy != null ? (row.rot_greasy === 1 ? '腐腻' : '正常') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
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
          @current-change="fetchRecords"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRecords, deleteRecord, exportRecords, downloadBlob } from '@/api/index.js'

const records = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const stateFilter = ref(null)

const colorLabels = ['淡白', '淡红', '红', '绛', '青紫']
const coatingLabels = ['白苔', '黄苔', '灰黑苔']

const fetchRecords = async () => {
  loading.value = true
  try {
    const res = await getRecords(page.value, pageSize.value, null, stateFilter.value)
    if (res.code === 0) {
      records.value = res.data.list
      total.value = res.data.total
    }
  } catch (e) {
    ElMessage.error('获取记录失败')
  }
  loading.value = false
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除记录 #${row.id}？`, '警告', { type: 'warning' })
  const res = await deleteRecord(row.id)
  if (res.code === 0) {
    ElMessage.success('删除成功')
    fetchRecords()
  } else {
    ElMessage.error(res.message || '删除失败')
  }
}

const handleExport = async () => {
  try {
    const res = await exportRecords(page.value, pageSize.value, null, stateFilter.value);
    downloadBlob(res, 'records_page' + page.value + '.csv');
  } catch (e) {
    ElMessage.error('导出失败');
  }
};

onMounted(fetchRecords)
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
