<template>
  <div class="jm-view">
    <Toast ref="toastRef" />

    <!-- 封面预览模态框 -->
    <div
      v-if="previewImage"
      class="fixed inset-0 z-50 flex items-center justify-center"
    >
      <!-- 遮罩层：点击关闭 -->
      <div class="absolute inset-0 bg-black/70 backdrop-blur-sm cursor-pointer" @click="closePreview"></div>
      <button
        @click="closePreview"
        class="absolute top-4 right-4 z-10 w-10 h-10 bg-[var(--bg-card)]/90 backdrop-blur-md rounded-full shadow-lg flex items-center justify-center hover:bg-[var(--bg-card)] transition-colors"
      >
        <svg class="w-6 h-6 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
      <!-- 内容区：阻止冒泡 -->
      <div class="relative flex flex-col items-center justify-center max-w-4xl max-h-[90vh] p-4" @click.stop>
        <img
          :src="previewImage"
          :alt="previewTitle"
          class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
        />
        <p v-if="previewTitle" class="text-center text-white mt-4 text-lg font-medium">{{ previewTitle }}</p>
      </div>
    </div>

    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-[var(--text-primary)]">禁漫下载</h2>
    </div>

    <!-- 输入框 -->
    <div class="bg-[var(--bg-card)] p-4 rounded-lg shadow mb-6">
      <div class="flex flex-wrap gap-4 items-end">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium mb-1 text-[var(--text-primary)]">车牌号</label>
          <input
            v-model="albumId"
            type="text"
            placeholder="请输入车牌号"
            class="w-full border border-[var(--border)] rounded px-3 py-2 bg-[var(--bg-surface)] text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            @keyup.enter="startDownload"
          />
        </div>
        <div>
          <button
            @click="startDownload"
            :disabled="downloading"
            class="px-6 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="downloading">下载中...</span>
            <span v-else>下载</span>
          </button>
        </div>
      </div>

      <!-- 进度条 -->
      <div v-if="downloading || showTransition" class="mt-4 transition-all duration-300" :class="{ 'opacity-0': isFadingOut }">
        <div v-if="currentTitle" class="text-sm text-[var(--text-primary)] font-medium mb-1">
          {{ currentTitle }}
        </div>
        <div class="flex justify-between text-sm text-[var(--text-secondary)] mb-1">
          <span>{{ statusText }}</span>
          <span>{{ progress }}%</span>
        </div>
        <div class="w-full bg-[var(--bg-surface)] rounded-full h-2.5 overflow-hidden">
          <div
            class="h-2.5 rounded-full transition-all duration-300"
            :class="currentStatus === 'completed' ? 'bg-green-500' : 'bg-[var(--primary)]'"
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
      </div>
    </div>

    <!-- 最近下载的本子 -->
    <div v-if="recentItems.length > 0 || newAddedId" class="mb-8">
      <h3 class="text-lg font-bold text-[var(--text-primary)] mb-4">最近下载的本子</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div
          v-for="item in recentItems"
          :key="item.album_id"
          class="bg-[var(--bg-card)] rounded-xl shadow-lg overflow-hidden group relative cursor-pointer transition-all duration-500"
          :class="{ 'ring-2 ring-[var(--primary)] ring-offset-2 ring-offset-[var(--bg-page)]': newAddedId === item.album_id }"
          @click="openPreview(getCoverUrl(item.album_id), item.title)"
        >
          <div class="relative overflow-hidden" style="aspect-ratio: 3/4;">
            <img
              :src="getCoverUrl(item.album_id)"
              :alt="item.title"
              class="w-full h-full object-cover"
              @error="handleCoverError"
            />
            <!-- 悬浮遮罩 - 下载按钮 -->
            <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-300 flex items-center justify-center">
              <button
                @click.stop="downloadPdf(item.album_id)"
                class="opacity-0 group-hover:opacity-100 backdrop-blur-md bg-white/30 border border-white/50 px-6 py-3 rounded-lg text-white text-sm font-medium shadow-lg transition-all duration-300 hover:bg-white/50 hover:scale-105"
              >
                <span class="flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                  下载
                </span>
              </button>
            </div>
          </div>
          <div class="p-3">
            <p class="text-sm font-medium text-[var(--text-primary)] truncate" :title="item.title">{{ item.title }}</p>
            <p class="text-xs text-[var(--text-secondary)] mt-1">车牌号: {{ item.album_id }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录 -->
    <div v-if="historyItems.length > 0">
      <h3 class="text-lg font-bold text-[var(--text-primary)] mb-4">历史记录</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <div
          v-for="item in historyItems"
          :key="item.album_id"
          class="bg-[var(--bg-card)] rounded-xl shadow-lg overflow-hidden opacity-80 group"
        >
          <div class="relative overflow-hidden" style="aspect-ratio: 3/4;">
            <img
              :src="getCoverUrl(item.album_id)"
              :alt="item.title"
              class="w-full h-full object-cover"
              @error="handleCoverError"
            />
            <!-- 删除按钮 -->
            <button
              @click="deleteItem(item.album_id)"
              class="absolute top-2 right-2 w-6 h-6 bg-black/50 backdrop-blur-sm rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 hover:bg-red-500 hover:bg-opacity-80 transition-all duration-200"
              title="删除"
            >
              <svg class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="p-3">
            <p class="text-sm font-medium text-[var(--text-primary)] truncate" :title="item.title">{{ item.title }}</p>
            <p class="text-xs text-[var(--text-secondary)] mt-1">车牌号: {{ item.album_id }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="recentItems.length === 0 && historyItems.length === 0 && !downloading" class="text-center py-16">
      <div class="text-[var(--text-secondary)] text-6xl mb-4">📚</div>
      <div class="text-[var(--text-secondary)] text-lg">输入车牌号开始下载</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { jmApi } from '../api'
import Toast from '../components/Toast.vue'

const toastRef = ref(null)
const albumId = ref('')
const downloading = ref(false)
const progress = ref(0)
const statusText = ref('')
const currentTitle = ref('')
const currentStatus = ref('')
const recentItems = ref([])
const historyItems = ref([])
const previewImage = ref('')
const previewTitle = ref('')
const showTransition = ref(false)
const isFadingOut = ref(false)
const newAddedId = ref('')

let pollInterval = null

// 禁止背景滚动
watch(previewImage, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})

onMounted(() => {
  loadData()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  if (pollInterval) clearInterval(pollInterval)
})

function handleKeydown(event) {
  if (event.key === 'Escape' && previewImage.value) {
    closePreview()
  }
}

async function loadData() {
  try {
    const [recentRes, historyRes] = await Promise.all([
      jmApi.getRecent(),
      jmApi.getHistory()
    ])
    if (recentRes.data.success) {
      recentItems.value = recentRes.data.items
    }
    if (historyRes.data.success) {
      historyItems.value = historyRes.data.items
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

async function startDownload() {
  if (!albumId.value.trim()) {
    showToast('请输入车牌号', 'warning')
    return
  }

  if (!/^\d+$/.test(albumId.value.trim())) {
    showToast('车牌号必须是数字', 'warning')
    return
  }

  const id = albumId.value.trim()
  
  downloading.value = true
  progress.value = 0
  statusText.value = '准备下载...'
  currentTitle.value = `本子 ${id}`
  currentStatus.value = ''
  isFadingOut.value = false
  showTransition.value = false
  newAddedId.value = ''

  try {
    const res = await jmApi.download(id)
    
    if (!res.data.success) {
      throw new Error(res.data.error || '下载失败')
    }

    if (res.data.cached) {
      showToast('该本子已缓存', 'info')
      downloadPdf(id)
      downloading.value = false
      albumId.value = ''
      return
    }

    // 开始轮询状态
    startPolling(id)

  } catch (error) {
    showToast(error.message || '下载失败', 'error')
    downloading.value = false
    albumId.value = ''
  }
}

function startPolling(taskId) {
  pollInterval = setInterval(async () => {
    try {
      const res = await jmApi.getStatus(taskId)
      
      if (!res.data.success) {
        throw new Error(res.data.error || '获取状态失败')
      }

      const status = res.data
      progress.value = status.progress || 0
      currentStatus.value = status.status || ''
      
      // 更新标题（如果有）
      if (status.title) {
        currentTitle.value = status.title
      }

      switch (status.status) {
        case 'fetching_info':
          statusText.value = '获取本子信息...'
          break
        case 'downloading':
          statusText.value = '下载中...'
          break
        case 'extracting_cover':
          statusText.value = '提取封面...'
          break
        case 'completed':
          statusText.value = '下载完成'
          progress.value = 100
          clearInterval(pollInterval)
          downloading.value = false
          const completedId = taskId
          albumId.value = ''
          showToast('下载完成', 'success')
          
          // 触发过渡动画
          isFadingOut.value = true
          showTransition.value = true
          newAddedId.value = completedId
          
          // 先加载数据
          await loadData()
          
          // 延迟清空过渡状态
          setTimeout(() => {
            isFadingOut.value = false
            showTransition.value = false
            newAddedId.value = ''
          }, 2000)
          
          downloadPdf(completedId)
          break
        case 'failed':
          statusText.value = '下载失败'
          clearInterval(pollInterval)
          downloading.value = false
          albumId.value = ''
          currentStatus.value = ''
          isFadingOut.value = false
          showTransition.value = false
          newAddedId.value = ''
          showToast(status.error || '下载失败', 'error')
          break
      }
    } catch (error) {
      console.error('轮询状态失败:', error)
    }
  }, 1000)
}

function getCoverUrl(albumId) {
  return jmApi.getCoverUrl(albumId)
}

function handleCoverError(event) {
  event.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23d1d5db"><rect width="24" height="24" rx="4"/><text x="12" y="14" text-anchor="middle" font-size="10">封面</text></svg>'
}

function openPreview(imageUrl, title) {
  previewImage.value = imageUrl
  previewTitle.value = title
}

function closePreview() {
  previewImage.value = ''
  previewTitle.value = ''
}

async function deleteItem(albumId) {
  const confirmed = await toastRef.value.confirm('确定要删除这个本子吗？删除后将移除所有相关数据，包括缓存和封面。')
  
  if (!confirmed) {
    return
  }

  try {
    const res = await jmApi.deleteItem(albumId)
    
    if (res.data.success) {
      showToast('删除成功', 'success')
      await loadData()
    } else {
      showToast(res.data.error || '删除失败', 'error')
    }
  } catch (error) {
    console.error('删除失败:', error)
    showToast('删除失败', 'error')
  }
}

function downloadPdf(albumId) {
  const url = jmApi.getPdfUrl(albumId)
  const link = document.createElement('a')
  link.href = url
  link.download = `${albumId}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  showToast('开始下载 PDF', 'success')
}

function showToast(message, type = 'info') {
  if (toastRef.value) {
    toastRef.value.showToast(message, { type, duration: 3000 })
  }
}
</script>

<style scoped>
.backdrop-blur-md {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
</style>
