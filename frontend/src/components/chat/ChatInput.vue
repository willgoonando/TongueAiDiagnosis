<template>
  <div class="chat-input-container">
    <!-- 类目选择 -->
    <div class="category-section">
      <el-radio-group 
        v-model="selectedCategory" 
        size="small"
        @change="handleCategoryChange"
        class="category-tabs"
      >
        <el-radio-button label="coating">舌苔检测</el-radio-button>
        <el-radio-button label="report">报告解读</el-radio-button>
        <el-radio-button label="drugbox">药盒识别</el-radio-button>
      </el-radio-group>
      <div class="category-hint">
        聚焦临床决策,专业文献循证~
      </div>
    </div>

    <!-- 输入框区域 -->
    <div class="input-wrapper">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="4"
        :placeholder="getPlaceholder()"
        @keydown.ctrl.enter="handleSend"
        class="message-input"
        resize="none"
      />
      <div class="input-actions">
        <el-upload
          :show-file-list="false"
          :on-change="handleFileChange"
          :before-upload="() => false"
          accept=".jpg,.jpeg,.png,.bmp,.webp"
        >
          <el-button :icon="Picture" circle />
        </el-upload>
        <el-upload
          :show-file-list="false"
          :on-change="handleFileChange"
          :before-upload="() => false"
        >
          <el-button :icon="Document" circle />
        </el-upload>
        <el-button 
          type="primary" 
          :icon="Promotion" 
          circle
          @click="handleSend"
          :loading="sending"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Picture, Document, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  category: {
    type: String,
    default: 'coating'
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['category-change', 'send-message', 'send-image'])

const selectedCategory = ref(props.category)
const inputText = ref('')
const sending = ref(false)
const selectedFile = ref(null)

// 监听外部category变化
watch(() => props.category, (newVal) => {
  selectedCategory.value = newVal
})

// 切换类目
const handleCategoryChange = (category) => {
  selectedCategory.value = category
  inputText.value = ''
  selectedFile.value = null
  emit('category-change', category)
}

// 获取占位符文本
const getPlaceholder = () => {
  const placeholders = {
    coating: '输入您的问题，或上传舌象图片...',
    report: '粘贴报告文字或上传报告图片...',
    drugbox: '粘贴药盒/说明书文字或上传图片...'
  }
  return placeholders[selectedCategory.value] || '输入消息...'
}

// 文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
  // 如果是图片，可以预览
  if (file.raw.type.startsWith('image/')) {
    // 直接发送图片
    handleSendImage(file.raw)
  } else {
    ElMessage.info('文件已选择，请在输入框中输入问题后发送')
  }
}

// 发送消息
const handleSend = () => {
  if (sending.value) return
  
  const text = inputText.value.trim()
  if (!text && !selectedFile.value) {
    ElMessage.warning('请输入消息或上传文件')
    return
  }
  
  sending.value = true
  
  if (selectedFile.value) {
    // 发送图片
    emit('send-image', selectedFile.value, text)
    selectedFile.value = null
  } else {
    // 发送文本
    emit('send-message', text)
  }
  
  inputText.value = ''
  sending.value = false
}

// 发送图片
const handleSendImage = (file) => {
  emit('send-image', file, inputText.value.trim())
  inputText.value = ''
  selectedFile.value = null
}
</script>

<style scoped>
.chat-input-container {
  padding: 24px 20px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  display: block;
  visibility: visible;
  min-height: 150px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
}

.category-section {
  margin-bottom: 16px;
}

.category-tabs {
  width: 100%;
  display: flex;
  gap: 8px;
}

.category-tabs :deep(.el-radio-button) {
  flex: 1;
}

.category-tabs :deep(.el-radio-button__inner) {
  width: 100%;
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.category-tabs :deep(.el-radio-button__original:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.category-hint {
  margin-top: 8px;
  font-size: 0.875rem;
  color: #6b7280;
  text-align: center;
}

.input-wrapper {
  position: relative;
}

.message-input {
  margin-bottom: 12px;
}

.message-input :deep(.el-textarea__inner) {
  border-radius: 16px;
  border: 2px solid rgba(226, 232, 240, 0.8);
  padding: 16px 20px;
  font-size: 0.95rem;
  line-height: 1.7;
  resize: none;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.95);
}

.message-input :deep(.el-textarea__inner):hover {
  border-color: rgba(102, 126, 234, 0.5);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.message-input :deep(.el-textarea__inner):focus {
  border-color: #667eea;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
  background: white;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
}

.input-actions .el-button {
  width: 44px;
  height: 44px;
  transition: all 0.3s ease;
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.input-actions .el-button:not(.el-button--primary):hover {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.input-actions .el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.input-actions .el-button--primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.input-actions .el-button--primary:active {
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .chat-input-container {
    padding: 16px;
  }
  
  .category-hint {
    font-size: 0.8rem;
  }
}
</style>

