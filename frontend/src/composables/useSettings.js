import { ref, watch } from 'vue'

const settings = ref({
  showActionConfirm: true // 是否显示操作确认弹窗
})

// 从 localStorage 加载设置
const savedSettings = localStorage.getItem('appSettings')
if (savedSettings) {
  try {
    settings.value = { ...settings.value, ...JSON.parse(savedSettings) }
  } catch (e) {
    console.error('Failed to load settings:', e)
  }
}

// 监听设置变化并保存
watch(settings, (newSettings) => {
  localStorage.setItem('appSettings', JSON.stringify(newSettings))
}, { deep: true })

export function useSettings() {
  function setSetting(key, value) {
    settings.value[key] = value
  }

  function getSetting(key, defaultValue = null) {
    return settings.value[key] ?? defaultValue
  }

  return {
    settings,
    setSetting,
    getSetting
  }
}
