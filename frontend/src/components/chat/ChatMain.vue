<template>
  <div class="chat-main-container" ref="chatContainer">
    <div class="messages-list">
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message-item', message.isUser ? 'user-message' : 'ai-message']"
      >
        <div class="message-avatar">
          <img 
            v-if="message.isUser" 
            :src="userAvatar" 
            alt="用户头像"
          />
          <img 
            v-else 
            :src="aiAvatar" 
            alt="AI头像"
          />
        </div>
        <div class="message-content">
          <!-- 用户消息中的图片 -->
          <div v-if="message.isPicture && message.imageFile" class="message-image-wrapper">
            <div class="image-container">
              <img :src="getImageUrl(message.imageFile)" alt="上传的图片" class="uploaded-image" />
              <div class="image-overlay">
                <span class="image-label">{{ imageLabel }}</span>
              </div>
            </div>
          </div>
          <!-- 用户消息中的文本 -->
          <div v-if="message.isUser && !message.isPicture && message.text" class="message-text user-text">
            {{ message.text }}
          </div>
          <!-- AI思考中 -->
          <div 
            v-if="!message.isUser && message.loading && !message.receivedContent" 
            class="thinking-indicator"
          >
            <span></span>
            <span></span>
            <span></span>
            <span class="thinking-text">AI正在思考...</span>
          </div>
          <!-- AI回复 -->
          <div 
            v-if="!message.isUser && (!message.loading || message.receivedContent)" 
            class="message-text ai-text"
            v-html="renderMarkdown(message.text)"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import 'github-markdown-css'
import { useStateStore } from '@/stores/stateStore'

const props = defineProps({
  category: {
    type: String,
    default: 'coating'
  },
  sessionId: {
    type: [String, Number],
    default: null
  },
  messages: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['message-updated'])

const stateStore = useStateStore()
const chatContainer = ref(null)
const userAvatar = ref('./static/userDefault.jpg')
const aiAvatar = ref('./static/aiDefault.jpg')

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

const imageLabel = computed(() => {
  const labels = {
    coating: '📷 舌象图片',
    report: '📄 报告/化验单图片',
    drugbox: '💊 药盒/说明书图片'
  }
  return labels[props.category] || '📷 上传图片'
})

// 渲染Markdown
const renderMarkdown = (text) => {
  if (!text) return ''
  return md.render(text)
}

// 获取图片URL
const getImageUrl = (file) => {
  if (typeof file === 'string') return file
  if (file instanceof File) {
    return URL.createObjectURL(file)
  }
  return ''
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

// 监听消息变化，自动滚动
watch(() => props.messages, () => {
  scrollToBottom()
}, { deep: true })

onMounted(() => {
  // 设置头像
  userAvatar.value = stateStore.userImagePath || './static/userDefault.jpg'
  aiAvatar.value = stateStore.aiImagePath || './static/aiDefault.jpg'
  
  scrollToBottom()
})
</script>

<style scoped>
.chat-main-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  background: transparent;
  scroll-behavior: smooth;
}

.messages-list {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding-bottom: 20px;
}

.message-item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  border: 2px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease;
}

.message-avatar:hover {
  transform: scale(1.05);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px 20px 6px 20px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.ai-message .message-content {
  background: white;
  color: #2c3e50;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 20px 20px 20px 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.user-text {
  color: white;
  line-height: 1.6;
  word-wrap: break-word;
}

.ai-text {
  color: #2c3e50;
  line-height: 1.8;
  word-wrap: break-word;
}

.message-content {
  max-width: 70%;
  padding: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.user-message .message-content {
  padding: 12px 16px;
}

.ai-message .message-content {
  padding: 16px 20px;
}

/* 图片显示美化 */
.message-image-wrapper {
  margin: 0;
  padding: 0;
}

.image-container {
  position: relative;
  display: inline-block;
  max-width: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.image-container:hover {
  transform: scale(1.02);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
}

.uploaded-image {
  display: block;
  max-width: 100%;
  max-height: 400px;
  width: auto;
  height: auto;
  object-fit: contain;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.6), transparent);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-label {
  color: white;
  font-size: 0.875rem;
  font-weight: 500;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.message-text {
  line-height: 1.8;
  word-wrap: break-word;
}

.message-text :deep(.markdown-body) {
  font-size: 0.95rem;
  color: inherit;
}

.message-text :deep(.markdown-body h1),
.message-text :deep(.markdown-body h2),
.message-text :deep(.markdown-body h3) {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
}

.message-text :deep(.markdown-body p) {
  margin-bottom: 8px;
}

.message-text :deep(.markdown-body code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.message-text :deep(.markdown-body pre) {
  background: rgba(0, 0, 0, 0.05);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(.markdown-body pre code) {
  background: transparent;
  padding: 0;
}

.thinking-indicator {
  display: flex;
  gap: 6px;
  align-items: center;
  padding: 12px 0;
}

.thinking-text {
  margin-left: 8px;
  color: #6b7280;
  font-size: 0.9rem;
  font-style: italic;
}

.thinking-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: thinking 1.4s ease-in-out infinite;
}

.thinking-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  30% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
  
  .chat-main-container {
    padding: 16px;
  }
}
</style>

