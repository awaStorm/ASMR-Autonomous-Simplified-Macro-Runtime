<template>
  <div class="image-view">
    <Toast ref="toastRef" />

    <!-- 大图预览模态框 -->
    <div
      v-if="largePreviewVisible"
      class="fixed inset-0 z-50 flex items-center justify-center"
    >
      <!-- 遮罩层：点击关闭 -->
      <div class="absolute inset-0 bg-black/70 backdrop-blur-sm cursor-pointer" @click="closeLargePreview"></div>
      <button
        @click="closeLargePreview"
        class="absolute top-4 right-4 z-10 w-10 h-10 bg-[var(--bg-card)]/90 backdrop-blur-md rounded-full shadow-lg flex items-center justify-center hover:bg-[var(--bg-card)] transition-colors"
      >
        <svg class="w-6 h-6 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
      <!-- 内容区：阻止冒泡 -->
      <div class="relative flex flex-col items-center justify-center max-w-4xl max-h-[90vh] p-4" @click.stop>
        <img
          :src="largePreviewImage"
          alt="预览"
          class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
          crossorigin="anonymous"
        />
      </div>
    </div>

    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold" style="color: var(--text-primary);">图片搜索</h2>
    </div>

    <!-- 搜索表单 -->
    <div class="bg-[var(--bg-card)] p-4 rounded-lg shadow mb-6">
      <div class="flex flex-wrap gap-4">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium mb-1 text-[var(--text-primary)]">搜索关键词</label>
          <input
            v-model="keyword"
            type="text"
            class="w-full border border-[var(--border)] rounded px-3 py-2 transition-colors bg-[var(--bg-surface)] text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            :class="{ 'bg-[var(--bg-surface)] text-[var(--text-secondary)]': source === 'cat' }"
            :placeholder="placeholderText"
            @keyup.enter="searchImages"
            :disabled="source === 'cat'"
          />
        </div>
        <div class="min-w-[120px]">
          <label class="block text-sm font-medium mb-1 text-[var(--text-primary)]">图片数量</label>
          <select v-model="count" class="w-full border border-[var(--border)] rounded px-3 py-2 bg-[var(--bg-surface)] text-[var(--text-primary)]">
            <option v-for="n in 10" :key="n" :value="n">{{ n }}张</option>
          </select>
        </div>
        <div class="min-w-[150px]">
          <label class="block text-sm font-medium mb-1 text-[var(--text-primary)]">搜索来源</label>
          <div class="flex items-center gap-2">
            <select v-model="source" class="flex-1 border border-[var(--border)] rounded px-3 py-2 bg-[var(--bg-surface)] text-[var(--text-primary)]">
              <option value="baidu">百度图片</option>
              <option value="pexels">Pexels</option>
              <option value="cat">猫图</option>
              <option value="lolicon">Lolicon</option>
            </select>
            <label v-if="source === 'lolicon'" class="flex items-center gap-1 cursor-pointer">
              <input
                v-model="r18"
                type="checkbox"
                class="w-4 h-4 text-red-500 rounded"
              />
              <span class="text-sm text-[var(--text-secondary)]">R18</span>
            </label>
          </div>
        </div>
        <div class="flex items-end">
          <button
            @click="searchImages"
            class="px-6 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
          >
            <span v-if="loading">搜索中...</span>
            <span v-else>{{ source === 'cat' ? '随机获取' : '搜索' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 图片网格 -->
    <div v-if="images.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      <div
        v-for="(imageItem, index) in images"
        :key="imageItem.id || index"
        class="bg-[var(--bg-card)] rounded-xl shadow-lg overflow-hidden group relative cursor-pointer"
        @click="openLargePreview(imageItem.url)"
        @mouseenter="handleMouseEnter(imageItem, $event)"
        @mousemove="handleMouseMove($event)"
        @mouseleave="handleMouseLeave"
      >
        <div class="relative overflow-hidden" style="aspect-ratio: 1/1;">
          <img
            :src="imageItem.url"
            :alt="`图片${index + 1}`"
            class="w-full h-full object-cover transition-opacity duration-300"
            :class="{ 'opacity-0': !imageItem.loaded && !imageItem.failed }"
            loading="lazy"
            @load="() => onImageLoad(imageItem)"
            @error="() => onImageError(imageItem)"
          />
          <!-- 加载中遮罩 -->
          <div v-if="!imageItem.loaded && !imageItem.failed" class="absolute inset-0 flex items-center justify-center bg-[var(--bg-surface)]">
            <div class="animate-spin rounded-full h-8 w-8 border-2 border-[var(--primary)]/30 border-t-[var(--primary)]"></div>
          </div>
          <!-- 失败遮罩 -->
          <div v-if="imageItem.failed" class="absolute inset-0 flex flex-col items-center justify-center bg-[var(--bg-surface)]/80">
            <span class="text-[var(--text-secondary)] text-sm mb-2">加载失败</span>
            <button
              @click.stop="retryLoadImage(imageItem)"
              class="px-3 py-1 bg-[var(--primary)] text-white rounded text-sm hover:bg-[var(--primary-hover)]"
            >
              重试
            </button>
          </div>
          <!-- 悬浮遮罩 - 下载按钮 -->
          <div v-if="imageItem.loaded && !imageItem.failed" class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-300 flex items-center justify-center">
            <button
              @click.stop="downloadImage(imageItem)"
              class="opacity-0 group-hover:opacity-100 backdrop-blur-md bg-white/30 border border-white/50 px-4 py-2 rounded-lg text-white text-sm font-medium shadow-lg transition-all duration-300 hover:bg-white/50 hover:scale-105"
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
          <div class="flex items-center gap-2">
            <input
              type="text"
              :value="imageItem.url"
              class="flex-1 text-xs text-[var(--text-secondary)] bg-[var(--bg-surface)] rounded px-2 py-1 truncate"
              readonly
              @click="copyImageUrl(imageItem.url)"
            />
            <button
              @click="copyImageUrl(imageItem.url)"
              class="text-[var(--text-secondary)] hover:text-[var(--primary)] transition-colors"
              title="复制链接"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 大图预览浮层 -->
    <div
      v-show="previewVisible && previewUrl"
      class="fixed z-[10000] pointer-events-none"
      :style="{
        left: previewX + 'px',
        top: previewY + 'px',
        transform: 'translate(-50%, -110%)'
      }"
    >
      <div class="bg-[var(--bg-card)] rounded-xl shadow-2xl p-2 border border-[var(--border)]">
        <img
          :src="previewUrl"
          alt="预览"
          class="max-w-[400px] max-h-[400px] object-contain rounded-lg"
          style="max-width: 50vw; max-height: 50vh;"
          crossorigin="anonymous"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="images.length === 0 && !loading" class="text-center py-16">
      <div class="text-[var(--text-secondary)] text-6xl mb-4">🔍</div>
      <div class="text-[var(--text-secondary)] text-lg">{{ source === 'cat' ? '点击"随机获取"开始' : '输入关键词开始搜索图片' }}</div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-16">
      <div class="animate-spin rounded-full h-16 w-16 border-4 border-[var(--primary)]/30 border-t-[var(--primary)] mx-auto"></div>
      <div class="text-[var(--text-secondary)] mt-6">正在搜索...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { imageApi } from '../api'
import Toast from '../components/Toast.vue'

const toastRef = ref(null)
const keyword = ref('')
const count = ref(3)
const source = ref('baidu')
const r18 = ref(false)
const images = ref([])
const loading = ref(false)

const previewX = ref(0)
const previewY = ref(0)
const previewVisible = ref(false)
const previewUrl = ref('')

// 大图预览相关
const largePreviewImage = ref('')
const largePreviewVisible = ref(false)

const placeholderText = computed(() => {
  if (source.value === 'cat') {
    return '该搜索引擎仅返回猫图'
  } else if (source.value === 'lolicon') {
    return '输入二次元图片标签（如：萝莉、少女）'
  }
  return '输入搜索关键词'
})

watch(source, () => {
  keyword.value = ''
  images.value = []
  hidePreview()
})

// 禁止背景滚动
watch(largePreviewVisible, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})

async function searchImages() {
  if (!keyword.value.trim() && source.value !== 'cat' && source.value !== 'lolicon') {
    showToast('请输入搜索关键词', 'warning')
    return
  }

  loading.value = true
  images.value = []
  hidePreview()

  try {
    let urls = []
    if (source.value === 'cat') {
      const res = await imageApi.getCatImages(count.value)
      urls = res.data || []
    } else if (source.value === 'lolicon') {
      const res = await imageApi.getLoliconImages(keyword.value, count.value, r18.value ? 1 : 0)
      urls = res.data || []
    } else {
      const res = await imageApi.searchImages(keyword.value, count.value, source.value)
      urls = res.data || []
    }

    images.value = urls.map((url, idx) => ({
      id: `img_${Date.now()}_${idx}`,
      url,
      loaded: false,
      failed: false,
      retryCount: 0
    }))

    if (images.value.length === 0) {
      showToast('没有找到图片，请稍后重试', 'info')
    } else {
      showToast(`找到 ${images.value.length} 张图片`, 'success')
    }
  } catch (error) {
    showToast('搜索失败，请稍后重试', 'error')
    console.error('搜索失败:', error)
  } finally {
    loading.value = false
  }
}

function onImageLoad(imageItem) {
  imageItem.loaded = true
  imageItem.failed = false
}

function onImageError(imageItem) {
  imageItem.loaded = false
  imageItem.failed = true
}

function retryLoadImage(imageItem) {
  if (imageItem.retryCount < 3) {
    imageItem.failed = false
    imageItem.retryCount++
    const separator = imageItem.url.includes('?') ? '&' : '?'
    const newUrl = `${imageItem.url}${separator}_t=${Date.now()}`
    const oldUrl = imageItem.url
    imageItem.url = newUrl
    setTimeout(() => {
      if (imageItem.failed) {
        imageItem.url = oldUrl
      }
    }, 5000)
  } else {
    showToast('图片加载失败，请检查网络或复制链接下载', 'error')
  }
}

let hideTimer = null

function handleMouseEnter(imageItem, event) {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
  previewUrl.value = `/api/images/proxy?url=${encodeURIComponent(imageItem.url)}`
  previewX.value = event.clientX
  previewY.value = event.clientY
  previewVisible.value = true
}

function handleMouseMove(event) {
  previewX.value = event.clientX
  previewY.value = event.clientY
}

function handleMouseLeave() {
  hideTimer = setTimeout(() => {
    previewVisible.value = false
  }, 100)
}

function hidePreview() {
  previewVisible.value = false
}

function openLargePreview(imageUrl) {
  largePreviewImage.value = `/api/images/proxy?url=${encodeURIComponent(imageUrl)}`
  largePreviewVisible.value = true
}

function closeLargePreview() {
  largePreviewImage.value = ''
  largePreviewVisible.value = false
}

function handleImageKeydown(event) {
  if (event.key === 'Escape' && largePreviewVisible.value) {
    closeLargePreview()
  }
}

async function downloadImage(imageItem) {
  const url = imageItem.url

  try {
    const response = await fetch(`/api/images/proxy?url=${encodeURIComponent(url)}`)
    if (response.ok) {
      const blob = await response.blob()
      const fileName = `image_${Date.now()}.jpg`
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
      showToast('图片下载成功', 'success')
    } else {
      throw new Error('Proxy fetch failed')
    }
  } catch (error) {
    console.log('Proxy下载失败，尝试直接打开:', error)
    window.open(url, '_blank')
    showToast('由于跨域限制，已在新窗口打开图片，请右键另存为', 'info')
  }
}

function copyImageUrl(url) {
  navigator.clipboard.writeText(url).then(() => {
    showToast('链接已复制', 'success')
  }).catch(() => {
    showToast('复制失败', 'error')
  })
}

function showToast(message, type = 'info') {
  if (toastRef.value) {
    toastRef.value.showToast(message, { type, duration: 3000 })
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleImageKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleImageKeydown)
})
</script>

<style scoped>
.backdrop-blur-md {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

img {
  opacity: 1;
  transition: opacity 0.3s ease;
}
</style>
