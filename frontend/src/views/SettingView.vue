<template>
  <div class="setting-page">
    <!-- Toast 组件 -->
    <Toast ref="toastRef" />

    <!-- 顶部导航栏 -->
    <header class="setting-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <span class="back-icon">←</span>
          <span>返回</span>
        </button>
        <h1 class="page-title">设置</h1>
      </div>
    </header>

    <!-- 设置主体内容 -->
    <div class="setting-body">
      <!-- 左侧导航 -->
      <nav class="setting-sidebar">
        <div
          v-for="item in settingNavItems"
          :key="item.id"
          class="nav-item"
          :class="{ active: activeNav === item.id }"
          @click="activeNav = item.id"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </div>
      </nav>

      <!-- 右侧内容 -->
      <main class="setting-content">
        <!-- 通用设置 -->
        <div v-if="activeNav === 'general'" class="setting-section">
          <h2 class="section-title">通用设置</h2>

          <!-- 操作提醒开关 -->
          <div class="setting-item">
            <div class="setting-info">
              <h3 class="setting-label">操作提醒</h3>
              <p class="setting-desc">删除、恢复等操作前显示确认弹窗</p>
            </div>
            <label class="toggle-switch">
              <input
                type="checkbox"
                :checked="settings.showActionConfirm"
                @change="toggleActionConfirm"
              />
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- 图片搜索设置 -->
        <div v-if="activeNav === 'image'" class="setting-section">
          <h2 class="section-title">图片搜索设置</h2>
          <p class="section-hint">提示：修改配置后需要点击「保存配置」按钮才会生效</p>

          <!-- 百度图片（接口盒子） -->
          <div class="api-card">
            <div class="api-header">
              <span class="api-name">百度图片（接口盒子）</span>
              <span
                class="api-status"
                :class="{ configured: configStatus?.baidu?.configured }"
              >
                {{ configStatus?.baidu?.configured ? '✓ 已配置' : '✗ 未配置' }}
              </span>
            </div>
            <p class="api-desc">需要配置 API Key 和 User ID</p>
            <div class="api-fields">
              <div class="field-item">
                <label>API Key</label>
                <input
                  type="text"
                  v-model="apiConfigs.baidu.api_key"
                  :placeholder="configStatus?.baidu?.has_saved_key ? '················· (已配置，如需修改请重新输入)' : '请输入百度图片 API Key'"
                  class="api-input"
                />
              </div>
              <div class="field-item">
                <label>User ID</label>
                <input
                  type="text"
                  v-model="apiConfigs.baidu.user_id"
                  :placeholder="configStatus?.baidu?.has_saved_key ? '················· (已配置，如需修改请重新输入)' : '请输入用户 ID'"
                  class="api-input"
                />
              </div>
            </div>
            <button class="save-btn" @click="saveApiConfig('baidu')">保存配置</button>
          </div>

          <!-- Pexels -->
          <div class="api-card">
            <div class="api-header">
              <span class="api-name">Pexels</span>
              <span
                class="api-status"
                :class="{ configured: configStatus?.pexels?.configured }"
              >
                {{ configStatus?.pexels?.configured ? '✓ 已配置' : '✗ 未配置' }}
              </span>
            </div>
            <p class="api-desc">需要配置 API Key，URL 已预设</p>
            <div class="api-fields">
              <div class="field-item">
                <label>API Key</label>
                <input
                  type="text"
                  v-model="apiConfigs.pexels.api_key"
                  :placeholder="configStatus?.pexels?.has_saved_key ? '················· (已配置，如需修改请重新输入)' : '请输入 Pexels API Key'"
                  class="api-input"
                />
              </div>
            </div>
            <button class="save-btn" @click="saveApiConfig('pexels')">保存配置</button>
          </div>

          <!-- 随机猫图 -->
          <div class="api-card">
            <div class="api-header">
              <span class="api-name">随机猫图</span>
              <span
                class="api-status"
                :class="{ configured: configStatus?.cat?.configured }"
              >
                {{ configStatus?.cat?.configured ? '✓ 已配置' : '○ 可选配置' }}
              </span>
            </div>
            <p class="api-desc">公共 API，可选配密钥以提升限制（无密钥时使用演示模式）</p>
            <div class="api-fields">
              <div class="field-item">
                <label>API Key <span class="optional-tag">(可选)</span></label>
                <input
                  type="text"
                  v-model="apiConfigs.cat.api_key"
                  :placeholder="configStatus?.cat?.has_saved_key ? '················· (已配置，如需修改请重新输入)' : '可选，不填则使用演示模式'"
                  class="api-input"
                />
              </div>
            </div>
            <div class="api-info">
              <span>API URL: {{ configStatus?.cat?.api_url }}</span>
            </div>
            <button class="save-btn" @click="saveApiConfig('cat')">保存配置</button>
          </div>

          <!-- Lolicon -->
          <div class="api-card">
            <div class="api-header">
              <span class="api-name">Lolicon</span>
              <span class="api-status configured">✓ 无需配置</span>
            </div>
            <p class="api-desc">二次元图片 API，URL 已预设，直接使用</p>
            <div class="api-info">
              <span>API URL: {{ configStatus?.lolicon?.api_url }}</span>
            </div>
          </div>
        </div>

        <!-- 主题设置 -->
        <div v-if="activeNav === 'theme'" class="setting-section">
          <h2 class="section-title">主题设置</h2>

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

        <!-- 关于 -->
        <div v-if="activeNav === 'about'" class="setting-section">
          <h2 class="section-title">关于</h2>

          <div class="about-card">
            <div class="app-info">
              <div class="app-icon">🎧</div>
              <div class="app-details">
                <h3 class="app-name">ASMR</h3>
                <p class="app-version">版本 1.0.0</p>
              </div>
            </div>
            <p class="app-desc">一个集多种功能于一体的 Web 应用，包括待办事项、图片搜索、B站监控等。</p>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { useSettings } from '../composables/useSettings'
import Toast from '../components/Toast.vue'

const router = useRouter()
const { theme, setTheme } = useTheme()
const { settings, setSetting } = useSettings()

// 当前激活的导航项
const activeNav = ref('general')

// 设置导航项
const settingNavItems = [
  { id: 'general', icon: '⚙️', label: '通用设置' },
  { id: 'image', icon: '🖼️', label: '图片搜索' },
  { id: 'theme', icon: '🎨', label: '主题设置' },
  { id: 'about', icon: 'ℹ️', label: '关于' }
]

// API 配置表单数据
const apiConfigs = ref({
  baidu: { api_key: '', user_id: '' },
  pexels: { api_key: '' },
  cat: { api_key: '' }
})

// API 配置状态
const configStatus = ref({})

// Toast 提示引用
const toastRef = ref(null)

// Toast 辅助函数
function showToast(message, type = 'info') {
  if (toastRef.value) {
    toastRef.value.showToast(message, { type, duration: 3000 })
  }
}

// 获取 API 配置状态
async function fetchConfigStatus() {
  try {
    const response = await fetch('/api/images/config/status')
    configStatus.value = await response.json()
  } catch (error) {
    console.error('获取配置状态失败:', error)
  }
}

// 保存 API 配置
async function saveApiConfig(source) {
  const config = apiConfigs.value[source]

  // 检查是否有输入
  const hasInput = config.api_key || config.user_id

  // 如果有已保存的密钥但用户没有输入新密钥，不发送请求
  if (!hasInput && configStatus.value[source]?.has_saved_key) {
    showToast('未修改配置，无需保存', 'info')
    return
  }

  // 如果什么都没有输入且没有已保存的密钥
  if (!hasInput && source !== 'lolicon') {
    showToast('请输入配置信息', 'warning')
    return
  }

  try {
    const params = new URLSearchParams()
    params.append('source', source)
    if (config.api_key) {
      params.append('api_key', config.api_key)
    }
    if (config.user_id) {
      params.append('user_id', config.user_id)
    }

    const response = await fetch('/api/images/config/set', {
      method: 'POST',
      body: params
    })
    const result = await response.json()

    if (result.success) {
      // 清空输入框
      config.api_key = ''
      config.user_id = ''
      // 刷新配置状态
      await fetchConfigStatus()
      showToast('配置已保存', 'success')
    } else {
      showToast(result.message, 'error')
    }
  } catch (error) {
    showToast('保存失败', 'error')
  }
}

// 检查配置并显示错误提示
function checkAndShowError(source) {
  const status = configStatus.value[source]
  if (status && !status.configured && status.errors.length > 0) {
    // 优先显示 URL 错误，然后是密钥错误
    const urlError = status.errors.find(e => e.includes('URL'))
    const keyError = status.errors.find(e => e.includes('Key'))
    const idError = status.errors.find(e => e.includes('ID'))

    if (urlError) {
      showToast(urlError, 'warning')
    } else if (keyError) {
      showToast(keyError, 'warning')
    } else if (idError) {
      showToast(idError, 'warning')
    } else {
      showToast(status.errors[0], 'warning')
    }
    return false
  }
  return true
}

onMounted(() => {
  fetchConfigStatus()
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', handleSystemThemeChange)
})

// 主题状态文字
const themeStatusText = computed(() => {
  const texts = {
    system: '跟随系统',
    light: '亮色模式',
    dark: '暗色模式'
  }
  return texts[theme.value]
})

// 返回按钮
function goBack() {
  router.back()
}

// 切换操作提醒
function toggleActionConfirm(event) {
  setSetting('showActionConfirm', event.target.checked)
}

// 监听系统主题变化
function handleSystemThemeChange(e) {
  if (theme.value === 'system') {
    // 主题会自动响应，不需要额外操作
  }
}

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
}

/* 顶部导航栏 */
.setting-header {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-primary);
  font-size: 14px;
  transition: all 0.2s ease;
  line-height: 1;
}

.back-btn:hover {
  background: var(--bg-hover);
  border-color: var(--primary);
}

.back-icon {
  font-size: 16px;
  line-height: 1;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

/* 设置主体内容 */
.setting-body {
  flex: 1;
  display: flex;
}

/* 左侧导航 */
.setting-sidebar {
  width: 200px;
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary);
  border-left: 3px solid var(--primary);
}

.nav-icon {
  font-size: 18px;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

/* 右侧内容 */
.setting-content {
  flex: 1;
  padding: 30px 40px;
  overflow-y: auto;
}

.setting-section {
  max-width: 600px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 10px 0;
}

.section-hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 20px 0;
}

/* 设置项 */
.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background: var(--bg-card);
  border-radius: 12px;
  margin-bottom: 12px;
}

.setting-info {
  flex: 1;
}

.setting-label {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.setting-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

/* 开关切换 */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 26px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--border);
  transition: 0.3s;
  border-radius: 26px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

input:checked + .slider {
  background-color: var(--primary);
}

input:checked + .slider:before {
  transform: translateX(22px);
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
  width: 100%;
  max-width: 300px;
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
  text-align: left;
}

/* 当前状态 */
.current-status {
  text-align: left;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid var(--border);
  max-width: 300px;
}

.current-status span {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 关于卡片 */
.about-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 24px;
}

.app-info {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.app-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--primary), rgba(99, 102, 241, 0.6));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.app-details {
  display: flex;
  flex-direction: column;
}

.app-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px 0;
}

.app-version {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

.app-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

/* API 配置卡片 */
.api-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid var(--border);
}

.api-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.api-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.api-status {
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.api-status.configured {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.api-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 16px 0;
}

.api-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.field-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-item label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.optional-tag {
  font-size: 11px;
  color: var(--primary);
  font-weight: normal;
}

.api-input {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.2s ease;
}

.api-input:focus {
  outline: none;
  border-color: var(--primary);
}

.api-input::placeholder {
  color: var(--text-muted);
}

.save-btn {
  padding: 10px 20px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.save-btn:hover {
  background: rgba(99, 102, 241, 0.8);
}

.api-info {
  padding-top: 12px;
  margin-bottom: 16px;
  border-top: 1px solid var(--border);
}

.api-info span {
  font-size: 12px;
  color: var(--text-muted);
  font-family: monospace;
}
</style>
