<script setup>
import { RouterView, useRoute } from 'vue-router'
import { computed } from 'vue'
import Header from '@/components/Header.vue'

const route = useRoute()

// 在聊天页面不显示Header
const showHeader = computed(() => {
  return route.name !== 'chat'
})
</script>
<template>
  <div class="app-container">
    <Header v-if="showHeader"></Header>
    <main class="main-content" :class="{ 'no-header': !showHeader }">
      <router-view></router-view>
    </main>
  </div>
</template>

<style>
#app {
  padding: 0;
  margin: 0;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f8f9fa;
}

.main-content {
  padding-top: 72px;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.main-content.no-header {
  padding-top: 0;
}

.main-content > * {
  min-height: calc(100vh - 72px);
}

.main-content.no-header > * {
  min-height: 100vh;
  height: 100vh;
}
</style>
