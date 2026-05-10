<template>
  <div class="pipeline-page">
    <!-- 顶部导航栏 -->
    <header class="pipeline-header">
      <div class="header-left">
        <el-button @click="goBack" text>
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h1 class="page-title">🩺 舌诊 AI 流水线可视化</h1>
      </div>
      <div class="header-right">
        <el-tag type="success" effect="dark" size="large" v-if="recordId">流水线已执行</el-tag>
        <el-tag v-else type="info" effect="plain" size="large">答辩展示模式</el-tag>
      </div>
    </header>

    <div class="pipeline-content">
      <!-- 上传区域 -->
      <div class="upload-section" v-if="!recordId">
        <el-card class="upload-card" shadow="hover">
          <div class="upload-inner">
            <el-upload
              drag
              :auto-upload="false"
              :on-change="handleFileSelect"
              accept=".jpg,.jpeg,.png"
              :show-file-list="false"
            >
              <el-icon class="upload-icon" :size="60"><UploadFilled /></el-icon>
              <div class="upload-text">点击或拖拽舌象图片到此处</div>
              <div class="upload-hint">系统将依次展示 YOLOv5 → SAM → ResNet 完整处理流程</div>
            </el-upload>
            <div class="demo-note">
              <el-alert
                title="答辩提示：这不是简单的 API 调用，而是完整的深度学习流水线"
                type="warning"
                :closable="false"
                show-icon
              />
            </div>
          </div>
        </el-card>
      </div>

      <!-- 加载中（不等 LLM，只等推理完） -->
      <div class="loading-section" v-if="loading && !recordId">
        <el-card class="loading-card">
          <div class="loading-inner">
            <el-progress type="circle" :percentage="loadingPercent" :status="loadingPercent >= 100 ? 'success' : undefined" />
            <p class="loading-text">{{ loadingText }}</p>
            <p class="loading-subtext">YOLOv5 检测 → SAM 分割 → ResNet 分类（不等大模型回答）</p>
          </div>
        </el-card>
      </div>

      <!-- 流水线展示区域 -->
      <div class="pipeline-steps" v-if="recordId && steps.length > 0">
        <!-- 标题 -->
        <div class="pipeline-title">
          <h2>处理流水线实时展示</h2>
          <p class="pipeline-subtitle">上传图片完整经历了以下 5 个阶段，每个阶段都有独立模型处理</p>
        </div>

        <!-- 步骤时间线 -->
        <div class="timeline">
          <div
            v-for="(step, idx) in steps"
            :key="step.step_name"
            class="timeline-item"
            :class="{ active: activeStep === idx }"
          >
            <!-- 时间线连接线 -->
            <div class="timeline-connector">
              <div class="timeline-dot" :class="stepDotClass(idx)">
                <span v-if="idx < activeStep"><el-icon :size="18"><Check /></el-icon></span>
                <span v-else-if="idx === activeStep"><el-icon :size="16" class="loading-spinner"><Loading /></el-icon></span>
                <span v-else>{{ idx + 1 }}</span>
              </div>
              <div class="timeline-line" v-if="idx < steps.length - 1" :class="{ done: idx < activeStep }"></div>
            </div>

            <!-- 步骤内容 -->
            <div class="timeline-content">
              <el-card :class="['step-card', stepDotClass(idx)]" shadow="hover">
                <template #header>
                  <div class="step-header">
                    <div class="step-header-left">
                      <span class="step-title">{{ step.description }}</span>
                      <span class="step-model" v-if="step.tech?.model">{{ step.tech.model }}</span>
                    </div>
                    <el-tag v-if="idx < activeStep" size="small" type="success">已完成</el-tag>
                    <el-tag v-else-if="idx === activeStep" size="small" type="warning">处理中</el-tag>
                    <el-tag v-else size="small" type="info">等待中</el-tag>
                  </div>
                </template>

                <!-- 图片步骤 -->
                <div v-if="step.image_url" class="step-image-wrapper">
                  <div class="step-image-container">
                    <img 
                      :src="getImageUrl(step.image_url)" 
                      :alt="step.step_name"
                      class="step-image"
                      :class="{ 'blur-loading': idx > activeStep }"
                    />
                    <div class="image-badge" v-if="step.step_name === 'yolo'">
                      <span class="badge-dot green"></span> 检测框 + 置信度
                    </div>
                    <div class="image-badge" v-else-if="step.step_name === 'sam'">
                      <span class="badge-dot green"></span> 掩码分割 + 轮廓
                    </div>
                    <div class="image-badge" v-else-if="step.step_name === 'crop'">
                      <span class="badge-dot blue"></span> 裁剪后送入 ResNet
                    </div>
                  </div>
                </div>

                <!-- 技术细节卡片 -->
                <div v-if="step.tech" class="tech-details">
                  <div class="tech-grid">
                    <div v-for="(val, key) in step.tech.params" :key="key" class="tech-item">
                      <span class="tech-label">{{ key }}</span>
                      <span class="tech-value">{{ val }}</span>
                    </div>
                  </div>
                  <div class="tech-desc">
                    <el-icon><InfoFilled /></el-icon>
                    <span>{{ step.tech.desc }}</span>
                  </div>
                </div>

                <!-- 特征结果步骤 -->
                <div v-if="step.step_name === 'features' && features" class="features-section">
                  <div class="features-grid">
                    <div class="feature-card tongue-color">
                      <div class="feature-label">舌色</div>
                      <div class="feature-value">{{ tongueColorMap[features.tongue_color] || '未知' }}</div>
                      <el-progress :percentage="100" :stroke-width="10" color="#e74c3c" :show-text="false" />
                    </div>
                    <div class="feature-card coat-color">
                      <div class="feature-label">苔色</div>
                      <div class="feature-value">{{ coatingColorMap[features.tongue_coat_color] || '未知' }}</div>
                      <el-progress :percentage="100" :stroke-width="10" color="#f39c12" :show-text="false" />
                    </div>
                    <div class="feature-card thickness">
                      <div class="feature-label">舌体厚薄</div>
                      <div class="feature-value">{{ thicknessMap[features.thickness] || '未知' }}</div>
                      <el-progress :percentage="100" :stroke-width="10" color="#3498db" :show-text="false" />
                    </div>
                    <div class="feature-card rot">
                      <div class="feature-label">腐腻情况</div>
                      <div class="feature-value">{{ rotMap[features.rot_and_greasy] || '未知' }}</div>
                      <el-progress :percentage="100" :stroke-width="10" color="#2ecc71" :show-text="false" />
                    </div>
                  </div>
                  <div class="features-summary">
                    <el-alert
                      title="四维特征分类结果（4 个独立 ResNet50 + Attention）"
                      type="success"
                      :description="featureSummary"
                      :closable="false"
                      show-icon
                    />
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>

        <!-- 流水线总结 -->
        <el-card class="summary-card" v-if="allDone" shadow="hover">
          <template #header>
            <div class="summary-header">
              <el-icon :size="24"><Checked /></el-icon>
              <span>流水线处理完成</span>
            </div>
          </template>
          <div class="summary-body">
            <div class="summary-stat">
              <span class="stat-label">模型数量</span>
              <span class="stat-value">3 个独立模型</span>
            </div>
            <div class="summary-stat">
              <span class="stat-label">推理阶段</span>
              <span class="stat-value">5 个阶段</span>
            </div>
            <div class="summary-stat">
              <span class="stat-label">分类器数量</span>
              <span class="stat-value">4 个独立 ResNet50</span>
            </div>
            <div class="summary-stat">
              <span class="stat-label">注意力机制</span>
              <span class="stat-value">CBAM / SE / ECA 可选</span>
            </div>
          </div>
        </el-card>

        <!-- 重新上传 -->
        <div class="reset-section">
          <el-button @click="resetPipeline" type="primary" size="large" round>
            <el-icon><Refresh /></el-icon> 重新上传图片
          </el-button>
        </div>
      </div>

      <!-- 无数据 -->
      <div class="no-data" v-if="recordId && steps.length === 0 && !loading">
        <el-empty description="正在等待推理结果..." />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, ArrowLeft, Refresh, Check, Loading, InfoFilled, Checked } from '@element-plus/icons-vue'
import axios from 'axios'
import settings from '@/config/config.js'

const router = useRouter()

// 特征值映射
const tongueColorMap = { 0: '淡白舌', 1: '淡红舌', 2: '红舌', 3: '绛舌', 4: '青紫舌' }
const coatingColorMap = { 0: '白苔', 1: '黄苔', 2: '灰黑苔' }
const thicknessMap = { 0: '薄', 1: '厚' }
const rotMap = { 0: '正常', 1: '腐腻' }

// 每个步骤的技术细节（硬编码展示，证明项目深度）
const stepTechDetails = {
  original: {
    model: '—',
    params: {
      '输入格式': 'JPG / PNG / BMP',
      '颜色空间': 'RGB',
      '处理方式': '直接读取文件流',
    },
    desc: '前端上传图片，后端通过 FastAPI 接收 UploadFile，不经过任何预处理直接送入流水线'
  },
  yolo: {
    model: 'YOLOv5',
    params: {
      '模型类型': '目标检测 (Object Detection)',
      'Backbone': 'CSPDarknet53',
      '输入尺寸': '640 × 640',
      '置信度阈值': '0.5（过滤低质量检测）',
      '多目标策略': '取置信度最高的检测框',
    },
    desc: 'YOLOv5 定位舌头区域，返回 bounding box [x1,y1,x2,y2] 和置信度分数。这是自行训练的检测模型，非第三方 API。'
  },
  sam: {
    model: 'SAM (ViT-B)',
    params: {
      '模型架构': 'Segment Anything (ViT-B)',
      '参数量': '~91M',
      '分割方式': 'Box Prompt + 掩码预测',
      '多掩码策略': '取置信度最高的掩码',
      '掩码应用': '非掩码区域设为黑色背景',
    },
    desc: 'SAM 对 YOLO 检测到的舌头区域做像素级分割，得到精确的舌头掩码。相比 YOLO 的矩形边框，SAM 能精确贴合舌头轮廓'
  },
  crop: {
    model: '—',
    params: {
      '裁剪依据': 'SAM 掩码的精确边界框',
      '与 YOLO 对比': 'YOLO 矩形框 → SAM 精确轮廓',
      '背景去除': '非掩码区域置黑',
      '输出尺寸': '自适应（根据掩码范围）',
    },
    desc: '使用 SAM 生成的掩码轮廓计算最小外接矩形，裁剪出只包含舌头的区域。相比直接用 YOLO 边框裁剪，去除了更多背景噪声'
  },
  features: {
    model: 'ResNet50 × 4',
    params: {
      '分类器1': '舌色 (5 类：淡白/淡红/红/绛/青紫)',
      '分类器2': '苔色 (3 类：白/黄/灰黑)',
      '分类器3': '厚薄 (2 类：薄/厚)',
      '分类器4': '腐腻 (2 类：正常/腐腻)',
      '注意力机制': 'CBAM / SE / ECA 可选',
    },
    desc: '四个独立的 ResNet50 分类器并行处理，每个负责一个舌象维度的分类。支持 CBAM/SE/ECA 三种注意力机制可选，通过训练对比实验验证效果。'
  }
}

const loading = ref(false)
const loadingPercent = ref(0)
const loadingText = ref('正在处理图片...')
const recordId = ref(null)
const steps = ref([])
const features = ref(null)
const activeStep = ref(0)
const selectedFile = ref(null)
const allDone = ref(false)

let pollTimer = null
let progressTimer = null
let fetchAbortController = null

const featureSummary = computed(() => {
  if (!features.value) return ''
  const parts = []
  if (features.value.tongue_color !== undefined) parts.push(`舌色：${tongueColorMap[features.value.tongue_color] || '未知'}`)
  if (features.value.tongue_coat_color !== undefined) parts.push(`苔色：${coatingColorMap[features.value.tongue_coat_color] || '未知'}`)
  if (features.value.thickness !== undefined) parts.push(`厚薄：${thicknessMap[features.value.thickness] || '未知'}`)
  if (features.value.rot_and_greasy !== undefined) parts.push(`腐腻：${rotMap[features.value.rot_and_greasy] || '未知'}`)
  return parts.join(' | ')
})

const goBack = () => router.push('/')

const getImageUrl = (url) => {
  if (!url) return ''
  // pipeline 图片通过 FastAPI StaticFiles 在 5000 端口提供
  return `${settings.ServerUrl}${url}`
}

const stepDotClass = (idx) => {
  if (idx < activeStep.value) return 'completed'
  if (idx === activeStep.value) return 'active'
  return 'pending'
}

const handleFileSelect = async (uploadFile) => {
  selectedFile.value = uploadFile.raw
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.warning('请先登录后再使用流水线展示功能')
    router.push('/login')
    return
  }
  await startPipeline()
}

const startPipeline = async () => {
  if (!selectedFile.value) return

  // 重置状态
  loading.value = true
  loadingPercent.value = 0
  loadingText.value = '正在处理图片...'
  steps.value = []
  features.value = null
  activeStep.value = 0
  recordId.value = null
  allDone.value = false

  // 进度动画（最高到 90%，留 10% 给最后的步骤）
  progressTimer = setInterval(() => {
    if (loadingPercent.value < 85) {
      loadingPercent.value += 2.5 + Math.random() * 4
      if (loadingPercent.value > 85) loadingPercent.value = 85
    }
  }, 800)

  const token = localStorage.getItem('token')
  const formData = new FormData()
  formData.append('file_data', selectedFile.value)
  formData.append('user_input', '请分析这张舌象图片')
  formData.append('name', `流水线展示 ${new Date().toLocaleString()}`)

  try {
    // 用 fetch 发请求，但不等流读完——读到 record_id/session_id 就立刻开始轮询 pipeline
    fetchAbortController = new AbortController()
    
    const response = await fetch(`${settings.ServerUrl}/api/model/session`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
      signal: fetchAbortController.signal
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    // 只读前几帧就丢，不等流结束
    // 同时立即开始轮询 pipeline
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    
    // 异步读流但不阻塞 pipeline 轮询
    const readStream = async () => {
      try {
        let done = false
        while (!done) {
          const { value, done: readerDone } = await reader.read()
          done = readerDone
        }
      } catch (e) {
        if (e.name === 'AbortError') return
      }
    }
    readStream()  // 不 await，后台跑

    // 短暂等待后开始轮询 pipeline
    await new Promise(resolve => setTimeout(resolve, 1500))

    // 获取最新 record_id
    loadingText.value = '等待流水线结果...'
    await fetchRecordId(token)

    if (!recordId.value) {
      // 重试一次
      await new Promise(resolve => setTimeout(resolve, 2000))
      await fetchRecordId(token)
    }

    if (!recordId.value) {
      ElMessage.error('无法获取分析记录，请确认已登录')
      loading.value = false
      clearInterval(progressTimer)
      return
    }

    clearInterval(progressTimer)
    loadingPercent.value = 95
    await new Promise(resolve => setTimeout(resolve, 300))
    loading.value = false

    // 开始轮询 pipeline 结果
    await pollPipeline()
  } catch (error) {
    console.error('Pipeline 上传失败:', error)
    ElMessage.error('上传失败，请重试')
    loading.value = false
    clearInterval(progressTimer)
  }
}

const fetchRecordId = async (token) => {
  try {
    const res = await axios.get('/user/record', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const records = res.data?.data || []
    if (records.length > 0) {
      const latest = records[records.length - 1]
      recordId.value = latest.ID || latest.id
    }
  } catch (e) {
    console.error('获取记录列表失败', e)
  }
}

const pollPipeline = async () => {
  return new Promise((resolve) => {
    let noDataCount = 0
    const token = localStorage.getItem('token')

    pollTimer = setInterval(async () => {
      try {
        const res = await axios.get(`/pipeline/${recordId.value}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        const data = res.data

        if (data.steps && data.steps.length > 0) {
          // 给每个步骤附加技术细节
          steps.value = data.steps.map(s => ({
            ...s,
            tech: stepTechDetails[s.step_name] || null
          }))
          
          if (data.features) {
            features.value = data.features
          }

          // 计算当前激活的步骤
          const stepOrder = ['original', 'yolo', 'sam', 'crop', 'features']
          let lastDoneIdx = -1
          for (const step of data.steps) {
            const idx = stepOrder.indexOf(step.step_name)
            if (idx > lastDoneIdx) lastDoneIdx = idx
          }
          activeStep.value = lastDoneIdx + 1

          // 所有步骤完成
          if (data.steps.length >= 5 && data.features) {
            allDone.value = true
            clearInterval(pollTimer)
            resolve()
          }
        } else {
          noDataCount++
          if (noDataCount > 60) {
            clearInterval(pollTimer)
            resolve()
          }
        }
      } catch (e) {
        noDataCount++
        if (noDataCount > 60) {
          clearInterval(pollTimer)
          resolve()
        }
      }
    }, 1000)
  })
}

const resetPipeline = () => {
  clearInterval(pollTimer)
  clearInterval(progressTimer)
  if (fetchAbortController) {
    try { fetchAbortController.abort() } catch (e) {}
  }
  recordId.value = null
  steps.value = []
  features.value = null
  activeStep.value = 0
  selectedFile.value = null
  loading.value = false
  loadingPercent.value = 0
  allDone.value = false
}

onUnmounted(() => {
  clearInterval(pollTimer)
  clearInterval(progressTimer)
  if (fetchAbortController) {
    try { fetchAbortController.abort() } catch (e) {}
  }
})
</script>

<style scoped>
.pipeline-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.pipeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.pipeline-content {
  max-width: 920px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* 上传区域 */
.upload-section {
  display: flex;
  justify-content: center;
  padding-top: 80px;
}

.upload-card {
  width: 620px;
  border-radius: 16px;
}

.upload-inner {
  padding: 30px 20px;
  text-align: center;
}

.upload-icon {
  margin-bottom: 12px;
  color: #409eff;
}

.upload-text {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 14px;
  color: #999;
  margin-bottom: 16px;
}

.demo-note {
  margin-top: 20px;
}

/* 加载 */
.loading-section {
  display: flex;
  justify-content: center;
  padding-top: 100px;
}

.loading-card {
  width: 420px;
  border-radius: 16px;
}

.loading-inner {
  text-align: center;
  padding: 30px;
}

.loading-text {
  font-size: 18px;
  font-weight: bold;
  margin-top: 20px;
  color: #333;
}

.loading-subtext {
  font-size: 13px;
  color: #999;
  margin-top: 8px;
}

/* 流水线标题 */
.pipeline-title {
  text-align: center;
  margin-bottom: 40px;
  color: white;
}

.pipeline-title h2 {
  font-size: 28px;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.pipeline-subtitle {
  font-size: 15px;
  opacity: 0.8;
  margin-top: 8px;
}

/* 时间线 */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-item {
  display: flex;
  align-items: stretch;
  gap: 20px;
}

.timeline-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 40px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  color: white;
  z-index: 2;
  transition: all 0.3s;
}

.timeline-dot.completed { background: #67c23a; }

.timeline-dot.active {
  background: #e6a23c;
  box-shadow: 0 0 0 4px rgba(230, 162, 60, 0.3);
  animation: pulse 1.5s infinite;
}

.timeline-dot.pending { background: #c0c4cc; }

.loading-spinner { animation: spin 1s linear infinite; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(230, 162, 60, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(230, 162, 60, 0); }
  100% { box-shadow: 0 0 0 0 rgba(230, 162, 60, 0); }
}

.timeline-line {
  width: 3px;
  flex: 1;
  background: #c0c4cc;
  min-height: 30px;
  transition: background 0.3s;
}

.timeline-line.done { background: #67c23a; }

/* 步骤卡片 */
.timeline-content {
  flex: 1;
  margin-bottom: 20px;
}

.step-card {
  border-radius: 12px;
  transition: all 0.3s;
}

.step-card.completed { border-left: 4px solid #67c23a; }

.step-card.active {
  border-left: 4px solid #e6a23c;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.step-card.pending { opacity: 0.5; }

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.step-title {
  font-weight: 600;
  font-size: 15px;
}

.step-model {
  font-size: 12px;
  background: #f0f2f5;
  color: #666;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
}

/* 图片 */
.step-image-wrapper {
  padding: 10px;
}

.step-image-container {
  position: relative;
  display: inline-block;
  width: 100%;
}

.step-image {
  width: 100%;
  max-height: 340px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.5s;
  background: #f5f5f5;
}

.blur-loading {
  filter: blur(8px);
  opacity: 0.3;
}

.image-badge {
  position: absolute;
  bottom: 12px;
  left: 12px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.badge-dot.green { background: #2ecc71; }
.badge-dot.blue { background: #3498db; }

/* 技术细节 */
.tech-details {
  padding: 0 16px 16px;
  border-top: 1px solid #eee;
  margin-top: 4px;
}

.tech-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  padding: 12px 0;
}

.tech-item {
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  padding: 8px 12px;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.tech-label {
  font-size: 11px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tech-value {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-top: 2px;
}

.tech-desc {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  padding: 8px 0;
  background: #f0f7ff;
  border-radius: 8px;
  padding: 10px 12px;
}

.tech-desc .el-icon {
  margin-top: 3px;
  flex-shrink: 0;
  color: #409eff;
}

/* 特征结果 */
.features-section {
  padding: 10px;
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.feature-card {
  padding: 16px;
  border-radius: 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
}

.feature-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
  font-weight: 500;
}

.feature-value {
  font-size: 22px;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
}

.feature-card.tongue-color { border-left: 4px solid #e74c3c; }
.feature-card.coat-color { border-left: 4px solid #f39c12; }
.feature-card.thickness { border-left: 4px solid #3498db; }
.feature-card.rot { border-left: 4px solid #2ecc71; }

.features-summary {
  margin-top: 8px;
}

/* 总结卡片 */
.summary-card {
  margin-top: 20px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.summary-card :deep(.el-card__header) {
  border-bottom: 1px solid rgba(255,255,255,0.2);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.summary-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  background: rgba(255,255,255,0.15);
  padding: 14px 18px;
  border-radius: 10px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.7;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  margin-top: 4px;
}

/* 重传按钮 */
.reset-section {
  text-align: center;
  margin-top: 30px;
  padding-bottom: 60px;
}

.no-data {
  padding-top: 100px;
}

/* 响应式 */
@media (max-width: 768px) {
  .upload-card { width: 100%; }
  .features-grid { grid-template-columns: 1fr; }
  .tech-grid { grid-template-columns: 1fr; }
  .summary-body { grid-template-columns: 1fr; }
  .pipeline-header { flex-direction: column; gap: 12px; text-align: center; }
  .header-left { flex-direction: column; gap: 10px; }
}
</style>
