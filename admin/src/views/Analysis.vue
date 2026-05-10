<template>
  <div>
    <div class="page-header">
      <h2 class="page-title">数据分析</h2>
      <span class="total-badge">共 {{ total }} 条成功记录</span>
    </div>

    <div class="stat-grid">
      <!-- 舌色分布 -->
      <el-card shadow="never" class="stat-card">
        <template #header><span>👅 舌色分布</span></template>
        <div v-for="(label, key) in colorLabels" :key="'tc-' + key" class="stat-row">
          <span class="stat-label">{{ label }}</span>
          <el-progress
            :percentage="calcPct(tongueColor[key])"
            :color="colorColors[key]"
            :stroke-width="20"
            :text-inside="true"
          >
            {{ tongueColor[key] || 0 }} 人
          </el-progress>
        </div>
      </el-card>

      <!-- 苔色分布 -->
      <el-card shadow="never" class="stat-card">
        <template #header><span>🌫️ 苔色分布</span></template>
        <div v-for="(label, key) in coatingLabels" :key="'cc-' + key" class="stat-row">
          <span class="stat-label">{{ label }}</span>
          <el-progress
            :percentage="calcPct(coatingColor[key])"
            :color="coatingColors[key]"
            :stroke-width="20"
            :text-inside="true"
          >
            {{ coatingColor[key] || 0 }} 人
          </el-progress>
        </div>
      </el-card>

      <!-- 舌体厚薄 -->
      <el-card shadow="never" class="stat-card">
        <template #header><span>📏 舌体厚薄</span></template>
        <div class="stat-row">
          <span class="stat-label">薄</span>
          <el-progress
            :percentage="calcPct(thickness[0])"
            color="#67c23a"
            :stroke-width="20"
            :text-inside="true"
          >
            {{ thickness[0] || 0 }} 人
          </el-progress>
        </div>
        <div class="stat-row">
          <span class="stat-label">厚</span>
          <el-progress
            :percentage="calcPct(thickness[1])"
            color="#e6a23c"
            :stroke-width="20"
            :text-inside="true"
          >
            {{ thickness[1] || 0 }} 人
          </el-progress>
        </div>
      </el-card>

      <!-- 腐腻情况 -->
      <el-card shadow="never" class="stat-card">
        <template #header><span>🫧 腐腻情况</span></template>
        <div class="stat-row">
          <span class="stat-label">正常</span>
          <el-progress
            :percentage="calcPct(rotGreasy[0])"
            color="#67c23a"
            :stroke-width="20"
            :text-inside="true"
          >
            {{ rotGreasy[0] || 0 }} 人
          </el-progress>
        </div>
        <div class="stat-row">
          <span class="stat-label">腐腻</span>
          <el-progress
            :percentage="calcPct(rotGreasy[1])"
            color="#f56c6c"
            :stroke-width="20"
            :text-inside="true"
          >
            {{ rotGreasy[1] || 0 }} 人
          </el-progress>
        </div>
      </el-card>
    </div>

    <!-- ECharts 图表：舌色分布 + 苔色分布 -->
    <div class="chart-row">
      <el-card shadow="never" class="chart-card">
        <template #header><span>📊 舌色分布（柱状图）</span></template>
        <div ref="barChartRef" class="chart-box"></div>
      </el-card>
      <el-card shadow="never" class="chart-card">
        <template #header><span>🥧 苔色分布（饼图）</span></template>
        <div ref="pieChartRef" class="chart-box"></div>
      </el-card>
    </div>

    <!-- 用户对话活跃度 -->
    <el-card shadow="never" class="mt-20">
      <template #header><span>💬 用户对话活跃度</span></template>
      <div ref="userChatRef" class="chart-box chart-box-slim"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { getAnalysisStats, getUserChatStats } from '@/api/index.js'
import * as echarts from 'echarts'

const total = ref(0)
const tongueColor = ref({})
const coatingColor = ref({})
const thickness = ref({})
const rotGreasy = ref({})

const colorLabels = { 0: '淡白舌', 1: '淡红舌', 2: '红舌', 3: '绛舌', 4: '青紫舌' }
const colorColors = { 0: '#909399', 1: '#f0c0a0', 2: '#e6655a', 3: '#b03030', 4: '#6b3fa0' }
const coatingLabels = { 0: '白苔', 1: '黄苔', 2: '灰黑苔' }
const coatingColors = { 0: '#e8e0d0', 1: '#d4a833', 2: '#4a4a4a' }

const calcPct = (val) => (val && total.value ? Math.round((val / total.value) * 100) : 0)

// ECharts
const barChartRef = ref(null)
const pieChartRef = ref(null)
const userChatRef = ref(null)
let barChart = null
let pieChart = null
let userChatChart = null

function initCharts(data) {
  if (!barChartRef.value || !pieChartRef.value) return
  const tc = data.tongue_color || {}
  const barNames = [0, 1, 2, 3, 4].map(k => colorLabels[k])
  const barValues = [0, 1, 2, 3, 4].map(k => tc[k] || 0)
  const cc = data.coating_color || {}
  const pieNames = [0, 1, 2].map(k => coatingLabels[k])
  const pieValues = [0, 1, 2].map(k => cc[k] || 0)

  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: 'category', data: barNames, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: barValues.map((v, i) => ({ value: v, itemStyle: { color: colorColors[i] } })), barWidth: '50%' }]
  })

  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie', radius: ['30%', '60%'],
      data: pieValues.map((v, i) => ({ value: v, name: pieNames[i], itemStyle: { color: coatingColors[i] } })),
      label: { fontSize: 11 }
    }]
  })
}

function initUserChatChart(userChatData) {
  if (!userChatRef.value) return
  userChatChart = echarts.init(userChatRef.value)
  const emails = userChatData.map(d => d.email)
  const counts = userChatData.map(d => d.count)
  const maxCount = Math.max(...counts, 1)
  userChatChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 180, right: 40, top: 10, bottom: 20 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: emails.reverse(), axisLabel: { fontSize: 12 } },
    series: [{
      type: 'bar',
      data: counts.map(v => ({
        value: v,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#a0cfff' },
            { offset: 1, color: v / maxCount > 0.7 ? '#e6a23c' : '#409eff' }
          ]),
          borderRadius: [0, 4, 4, 0]
        }
      })),
      barWidth: '60%',
      label: { show: true, position: 'right', fontSize: 11 }
    }]
  })
}

function handleResize() {
  barChart?.resize()
  pieChart?.resize()
  userChatChart?.resize()
}

onMounted(async () => {
  try {
    const res = await getAnalysisStats()
    if (res.code === 0) {
      total.value = res.data.total
      tongueColor.value = res.data.tongue_color || {}
      coatingColor.value = res.data.coating_color || {}
      thickness.value = res.data.thickness || {}
      rotGreasy.value = res.data.rot_greasy || {}
      nextTick(() => initCharts(res.data))
    }
  } catch (e) {
    ElMessage.error('获取统计失败')
  }
  try {
    const uc = await getUserChatStats()
    if (uc.code === 0 && uc.data) {
      nextTick(() => initUserChatChart(uc.data))
    }
  } catch (e) { /* ignore */ }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  barChart?.dispose()
  pieChart?.dispose()
  userChatChart?.dispose()
  window.removeEventListener('resize', handleResize)
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
.total-badge {
  font-size: 14px;
  color: #909399;
  background: #f0f2f5;
  padding: 4px 12px;
  border-radius: 12px;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}
.stat-card :deep(.el-card__body) {
  padding: 16px 20px;
}
.stat-row {
  display: flex;
  align-items: center;
  margin-bottom: 14px;
  gap: 12px;
}
.stat-row:last-child {
  margin-bottom: 0;
}
.stat-label {
  width: 60px;
  font-size: 14px;
  color: #606266;
  flex-shrink: 0;
}
.stat-row :deep(.el-progress) {
  flex: 1;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}
.chart-card { min-width: 0; }
.chart-box { width: 100%; height: 280px; }
.chart-box-slim { height: 300px; }
.mt-20 { margin-top: 20px; }
</style>
