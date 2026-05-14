<template>
  <div class="setting-page">
    <!-- 设置内容 -->
    <div class="setting-container">
      <!-- 标题 -->
      <h1 class="page-title">设置</h1>

      <!-- 主题设置卡片 -->
      <div class="theme-card">
        <h2 class="card-title">主题设置</h2>
        
        <div class="theme-options">
          <button 
            class="theme-btn" 
            :class="{ active: theme === 'system' }"
            @click="setTheme('system')"
          >
            <span class="theme-icon">📱</span>
            <span class="theme-name">跟随系统</span>
          </button>

          <button 
            class="theme-btn" 
            :class="{ active: theme === 'light' }"
            @click="setTheme('light')"
          >
            <span class="theme-icon">☀️</span>
            <span class="theme-name">亮色模式</span>
          </button>

          <button 
            class="theme-btn" 
            :class="{ active: theme === 'dark' }"
            @click="setTheme('dark')"
          >
            <span class="theme-icon">🌙</span>
            <span class="theme-name">暗色模式</span>
          </button>
        </div>

        <!-- 当前状态 -->
        <div class="current-status">
          <span>当前：{{ themeStatusText }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useTheme } from '../composables/useTheme'

const { theme, setTheme } = useTheme()

// 主题状态文字
const themeStatusText = computed(() => {
  const texts = {
    system: '跟随系统',
    light: '亮色模式',
    dark: '暗色模式'
  }
  return texts[theme.value]
})

// 监听系统主题变化
function handleSystemThemeChange(e) {
  if (theme.value === 'system') {
    // 主题会自动响应，不需要额外操作
  }
}

onMounted(() => {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', handleSystemThemeChange)
})

onUnmounted(() => {
  window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', handleSystemThemeChange)
})
</script>

<style scoped>
.setting-page {
  min-height: 100vh;
  background: var(--bg-page);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

/* 设置容器 */
.setting-container {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 页面标题 */
.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 30px 0;
}

/* 主题卡片 */
.theme-card {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
}

/* 主题选项 */
.theme-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.theme-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  border: 2px solid var(--border);
  border-radius: 12px;
  background: var(--bg-surface);
  cursor: pointer;
  transition: all 0.3s ease;
}

.theme-btn:hover {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.05);
}

.theme-btn.active {
  border-color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
}

.theme-icon {
  font-size: 24px;
}

.theme-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

/* 当前状态 */
.current-status {
  text-align: center;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
}

.current-status span {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>