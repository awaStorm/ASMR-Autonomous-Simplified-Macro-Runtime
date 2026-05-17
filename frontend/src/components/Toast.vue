<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="[toast.type]"
      >
        <div class="toast-content">
          <span class="toast-icon">{{ getIcon(toast.type) }}</span>
          <span class="toast-message">{{ toast.message }}</span>
          <div class="toast-progress" :style="{ animationDuration: toast.duration + 'ms' }"></div>
        </div>
        <div v-if="toast.showActions" class="toast-actions">
          <button @click="handleAction(toast.id, 'cancel')" class="btn-cancel">取消</button>
          <button @click="handleAction(toast.id, 'confirm')" class="btn-confirm">确定</button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useSettings } from '../composables/useSettings'

const { getSetting } = useSettings()
const toasts = ref([])
let toastId = 0

function getIcon(type) {
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  }
  return icons[type] || 'ℹ'
}

function showToast(message, options = {}) {
  const id = ++toastId
  const duration = options.duration || 5000 // 默认 5 秒
  const toast = {
    id,
    message,
    type: options.type || 'info',
    duration,
    showActions: options.showActions || false,
    onConfirm: options.onConfirm || null,
    onCancel: options.onCancel || null
  }
  
  toasts.value.push(toast)
  
  // 无论是否有操作按钮，都设置超时自动关闭
  setTimeout(() => {
    removeToast(id)
  }, duration)
  
  return id
}

function removeToast(id) {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

function handleAction(id, action) {
  const toast = toasts.value.find(t => t.id === id)
  if (toast) {
    if (action === 'confirm' && toast.onConfirm) {
      toast.onConfirm()
    } else if (action === 'cancel' && toast.onCancel) {
      toast.onCancel()
    }
    removeToast(id)
  }
}

function confirm(message, options = {}) {
  // 检查全局设置是否关闭操作确认
  const showActionConfirm = getSetting('showActionConfirm', true)
  if (!showActionConfirm) {
    // 如果关闭了确认弹窗，直接返回 true（确认操作）
    return Promise.resolve(true)
  }
  
  // 添加提示信息
  const messageWithTip = message + ' （可在设置中关掉提示）'
  
  return new Promise((resolve) => {
    showToast(messageWithTip, {
      type: options.type || 'warning',
      duration: options.duration || 5000, // 确认弹窗也使用 5 秒
      showActions: true,
      onConfirm: () => resolve(true),
      onCancel: () => resolve(false)
    })
    
    // 超时后默认返回 false（不做任何操作）
    setTimeout(() => {
      resolve(false)
    }, options.duration || 5000)
  })
}

defineExpose({
  showToast,
  confirm,
  removeToast
})
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
  border-radius: 8px;
  padding: 12px 16px;
  min-width: 280px;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  position: relative;
}

.toast.success {
  border-left: 4px solid #48bb78;
}

.toast.error {
  border-left: 4px solid #fc8181;
}

.toast.warning {
  border-left: 4px solid #f6ad55;
}

.toast.info {
  border-left: 4px solid #63b3ed;
}

.toast-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toast-icon {
  font-size: 18px;
  font-weight: bold;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.toast.success .toast-icon {
  background: rgba(72, 187, 120, 0.2);
  color: #48bb78;
}

.toast.error .toast-icon {
  background: rgba(252, 129, 129, 0.2);
  color: #fc8181;
}

.toast.warning .toast-icon {
  background: rgba(246, 173, 85, 0.2);
  color: #f6ad55;
}

.toast.info .toast-icon {
  background: rgba(99, 179, 237, 0.2);
  color: #63b3ed;
}

.toast-message {
  flex: 1;
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.4;
}

.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #48bb78, #38a169);
  animation: progress linear forwards;
}

.toast.warning .toast-progress {
  background: linear-gradient(90deg, #f6ad55, #ed8936);
}

.toast.error .toast-progress {
  background: linear-gradient(90deg, #fc8181, #f56565);
}

.toast.info .toast-progress {
  background: linear-gradient(90deg, #63b3ed, #4299e1);
}

@keyframes progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

.toast-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-cancel,
.btn-confirm {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.1);
  color: #a0aec0;
  border: none;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-confirm {
  background: #48bb78;
  color: white;
  border: none;
}

.btn-confirm:hover {
  background: #38a169;
}

/* 过渡动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
