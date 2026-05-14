<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <!-- Logo区域 + 收起按钮 -->
    <div class="sidebar-logo">
      <div class="logo-content">
        <h1>ASMR</h1>
        <p>自简宏枢</p>
      </div>
      <button class="collapse-btn" @click="toggleCollapse">
        <ChevronLeft v-if="!isCollapsed" :size="20" />
        <ChevronRight v-else :size="20" />
      </button>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar-nav">
      <router-link 
        v-for="item in navItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <component :is="item.icon" :size="20" />
        <span class="nav-text">{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { 
  ChevronLeft, 
  ChevronRight, 
  Home, 
  ListTodo, 
  Image, 
  PlayCircle, 
  BookOpen,
  Cat,
  Settings
} from 'lucide-vue-next'

const route = useRoute()
const isCollapsed = ref(false)

// 导航项配置
const navItems = [
  { path: '/', label: '主页', icon: Home },
  { path: '/todo', label: '待办事项', icon: ListTodo },
  { path: '/image', label: '图片搜索', icon: Image },
  { path: '/bili', label: 'B站监控', icon: PlayCircle },
  { path: '/jm', label: '禁漫下载', icon: BookOpen },
  { path: '/miao', label: '喵喵喵', icon: Cat },
  { path: '/setting', label: '设置', icon: Settings }
]

// 切换收起状态
function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}

// 判断是否激活
function isActive(path) {
  return route.path === path || (path === '/' && route.path === '/')
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  background: linear-gradient(180deg, var(--bg-card) 0%, var(--bg-surface) 100%);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 999;
  transition: width 0.3s ease;
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.3);
}

.sidebar.collapsed {
  width: 60px;
}

/* Logo区域 */
.sidebar-logo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 15px;
  border-bottom: 1px solid var(--border);
  transition: all 0.3s ease;
}

.sidebar.collapsed .sidebar-logo {
  justify-content: center;
}

.logo-content {
  display: flex;
  flex-direction: column;
}

.logo-content h1 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.logo-content p {
  font-size: 11px;
  color: var(--text-secondary);
  margin: 2px 0 0 0;
}

.sidebar.collapsed .logo-content {
  display: none;
}

/* 收起按钮 */
.collapse-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  padding: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: var(--text-primary);
}

.sidebar.collapsed .collapse-btn {
  position: relative;
}

/* 导航菜单 */
.sidebar-nav {
  flex: 1;
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(251, 146, 60, 0.15);
  color: var(--text-primary);
  border-left-color: var(--primary);
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.sidebar.collapsed .nav-text {
  display: none;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 12px 0;
}
</style>
