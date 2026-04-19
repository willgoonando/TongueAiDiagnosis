<template>
  <div class="welcome-container">
    <div class="welcome-content">
      <div class="welcome-icon">
        <svg width="120" height="120" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L15.09 8.26L22 9L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9L8.91 8.26L12 2Z"
                fill="url(#gradient)" opacity="0.8"/>
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      <h1 class="welcome-title">我是小超</h1>
      <p class="welcome-subtitle">你的AI医生朋友</p>
      <p class="welcome-description">
        医学问题 · 解读报告 · 检索文献<br>
        都来问我吧~
      </p>
    </div>
  </div>
</template>

<script setup>
// 纯展示组件，无需逻辑
</script>

<style scoped>
.welcome-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  min-height: 0;
  max-height: 100%;
  overflow: auto;
}

.welcome-content {
  text-align: center;
  max-width: 600px;
}

.welcome-icon {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

.welcome-title {
  font-size: 3rem;
  font-weight: 700;
  background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 12px;
  line-height: 1.2;
}

.welcome-subtitle {
  font-size: 1.5rem;
  color: #4b5563;
  margin-bottom: 24px;
  font-weight: 500;
}

.welcome-description {
  font-size: 1.125rem;
  color: #6b7280;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .welcome-title {
    font-size: 2rem;
  }
  
  .welcome-subtitle {
    font-size: 1.25rem;
  }
  
  .welcome-description {
    font-size: 1rem;
  }
}
</style>

