<template>
  <div id="app">
    <!-- 设置页面特殊布局 -->
    <div v-if="isSettingPage" class="setting-layout">
      <router-view />
    </div>
    
    <!-- 普通页面布局 -->
    <div v-else class="app-layout">
      <!-- 侧边栏 -->
      <Sidebar />
      
      <!-- 主内容区 -->
      <main class="main-content">
        <!-- 路由视图 -->
        <div class="content-wrapper">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import { useTheme } from './composables/useTheme'

useTheme()

const route = useRoute()

const isSettingPage = computed(() => route.path === '/setting')
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

/* 主内容区 */
.main-content {
  flex: 1;
  min-height: 100vh;
  background-color: var(--bg-page);
  margin-left: 220px;
  transition: margin-left 0.3s ease;
}

/* 侧边栏收起时调整边距 */
:deep(.sidebar.collapsed) + .main-content {
  margin-left: 60px;
}

/* 内容容器 */
.content-wrapper {
  padding: 30px 40px;
}

/* 设置页面布局 */
.setting-layout {
  min-height: 100vh;
  background-color: var(--bg-page);
}
</style>