
&lt;template&gt;
  &lt;div class="image-view"&gt;
    &lt;Toast ref="toastRef" /&gt;

    &lt;!-- 大图预览模态框 --&gt;
    &lt;div
      v-if="largePreviewVisible"
      class="fixed inset-0 flex items-center justify-center"
      style="z-index: 99999;"
    &gt;
      &lt;!-- 遮罩层：点击关闭 --&gt;
      &lt;div class="absolute inset-0 bg-black/70 backdrop-blur-sm cursor-pointer" @click="closeLargePreview" style="z-index: 99998;"&gt;&lt;/div&gt;
      &lt;button
        @click="closeLargePreview"
        class="absolute top-4 right-4 w-10 h-10 bg-[var(--bg-card)]/90 backdrop-blur-md rounded-full shadow-lg flex items-center justify-center hover:bg-[var(--bg-card)] transition-colors"
        style="z-index: 100000;"
      &gt;
        &lt;svg class="w-6 h-6 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"&gt;
          &lt;path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/&gt;
        &lt;/svg&gt;
      &lt;/button&gt;
      &lt;!-- 内容区：阻止冒泡 --&gt;
      &lt;div class="relative flex flex-col items-center justify-center max-w-4xl max-h-[90vh] p-4" @click.stop style="z-index: 99999;"&gt;
        &lt;img
          :src="largePreviewImage"
          alt="预览"
          class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
          crossorigin="anonymous"
        /&gt;
      &lt;/div&gt;
    &lt;/div&gt;

    &lt;div class="flex justify-between items-center mb-6"&gt;
      &lt;h2 class="text-2xl font-bold" style="color: var(--text-primary);"&gt;图片搜索&lt;/h2&gt;
    &lt;/div&gt;

    &lt;!-- 搜索表单 --&gt;
    &lt;div class="bg-[var(--bg-card)] p-4 rounded-lg shadow mb-6"&gt;
      &lt;div class="flex flex-wrap gap-4"&gt;
        &lt;div class="flex-1 min-w-[200px]"&gt;
          &lt;label class="block text-sm font-medium mb-1 text-[var(--text-primary)]"&gt;搜索关键词&lt;/label&gt;
          &lt;input
            v-model="keyword"
            type="text"
            class="w-full border border-[var(--border)] rounded px-3 py-2 transition-colors bg-[var(--bg-surface)] text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            :class="{ 'bg-[var(--bg-surface)] text-[var(--text-secondary)]': source === 'cat' }"
            :placeholder="placeholderText"
            @keyup.enter="searchImages"
            :disabled="source === 'cat'"
          /&gt;
        &lt;/div&gt;
        &lt;div class="min-w-[120px]"&gt;
          &lt;label class="block text-sm font-medium mb-1 text-[var(--text-primary)]"&gt;图片数量&lt;/label&gt;
          &lt;select v-model="count" class="w-full border border-[var(--border)] rounded px-3 py-2 bg-[var(--bg-surface)] text-[var(--text-primary)]"&gt;
            &lt;option v-for="n in 10" :key="n" :value="n"&gt;{{ n }}张&lt;/option&gt;
          &lt;/select&gt;
        &lt;/div&gt;
        &lt;div class="min-w-[150px]"&gt;
          &lt;label class="block text-sm font-medium mb-1 text-[var(--text-primary)]"&gt;搜索来源&lt;/label&gt;
          &lt;div class="flex items-center gap-2"&gt;
            &lt;select v-model="source" class="flex-1 border border-[var(--border)] rounded px-3 py-2 bg-[var(--bg-surface)] text-[var(--text-primary)]"&gt;
              &lt;option value="baidu"&gt;百度图片&lt;/option&gt;
              &lt;option value="pexels"&gt;Pexels&lt;/option&gt;
              &lt;option value="cat"&gt;猫图&lt;/option&gt;
              &lt;option value="lolicon"&gt;Lolicon&lt;/option&gt;
            &lt;/select&gt;
            &lt;label v-if="source === 'lolicon'" class="flex items-center gap-1 cursor-pointer"&gt;
              &lt;input
                v-model="r18"
                type="checkbox"
                class="w-4 h-4 text-red-500 rounded"
              /&gt;
              &lt;span class="text-sm text-[var(--text-secondary)]"&gt;R18&lt;/span&gt;
            &lt;/label&gt;
          &lt;/div&gt;
        &lt;/div&gt;
        &lt;div class="flex items-end"&gt;
          &lt;button
            @click="searchImages"
            class="px-6 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
          &gt;
            &lt;span v-if="loading"&gt;搜索中...&lt;/span&gt;
            &lt;span v-else&gt;{{ source === 'cat' ? '随机获取' : '搜索' }}&lt;/span&gt;
          &lt;/button&gt;
        &lt;/div&gt;
      &lt;/div&gt;
    &lt;/div&gt;

    &lt;!-- 图片网格 --&gt;
    &lt;div v-if="images.length &gt; 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"&gt;
      &lt;div
        v-for="(imageItem, index) in images"
        :key="imageItem.id || index"
        class="bg-[var(--bg-card)] rounded-xl shadow-lg overflow-hidden group relative cursor-pointer"
        @click="openLargePreview(imageItem.url)"
        @mouseenter="handleMouseEnter(imageItem, $event)"
        @mousemove="handleMouseMove($event)"
        @mouseleave="handleMouseLeave"
      &gt;
        &lt;div class="relative overflow-hidden" style="aspect-ratio: 1/1;"&gt;
          &lt;img
            :src="imageItem.url"
            :alt="`图片${index + 1}`"
            class="w-full h-full object-cover transition-opacity duration-300"
            :class="{ 'opacity-0': !imageItem.loaded &amp;&amp; !imageItem.failed }"
            loading="lazy"
            @load="() =&gt; onImageLoad(imageItem)"
            @error="() =&gt; onImageError(imageItem)"
          /&gt;
          &lt;!-- 加载中遮罩 --&gt;
          &lt;div v-if="!imageItem.loaded &amp;&amp; !imageItem.failed" class="absolute inset-0 flex items-center justify-center bg-[var(--bg-surface)]"&gt;
            &lt;div class="animate-spin rounded-full h-8 w-8 border-2 border-[var(--primary)]/30 border-t-[var(--primary)]"&gt;&lt;/div&gt;
          &lt;/div&gt;
          &lt;!-- 失败遮罩 --&gt;
          &lt;div v-if="imageItem.failed" class="absolute inset-0 flex flex-col items-center justify-center bg-[var(--bg-surface)]/80"&gt;
            &lt;span class="text-[var(--text-secondary)] text-sm mb-2"&gt;加载失败&lt;/span&gt;
            &lt;button
              @click.stop="retryLoadImage(imageItem)"
              class="px-3 py-1 bg-[var(--primary)] text-white rounded text-sm hover:bg-[var(--primary-hover)]"
            &gt;
              重试
            &lt;/button&gt;
          &lt;/div&gt;
          &lt;!-- 悬浮遮罩 - 下载按钮 --&gt;
          &lt;div v-if="imageItem.loaded &amp;&amp; !imageItem.failed" class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-300 flex items-center justify-center"&gt;
            &lt;button
              @click.stop="downloadImage(imageItem)"
              class="opacity-0 group-hover:opacity-100 backdrop-blur-md bg-white/30 border border-white/50 px-4 py-2 rounded-lg text-white text-sm font-medium shadow-lg transition-all duration-300 hover:bg-white/50 hover:scale-105"
            &gt;
              &lt;span class="flex items-center gap-2"&gt;
                &lt;svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"&gt;
                  &lt;path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 30 003 3h10a3 30 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/&gt;
                &lt;/svg&gt;
                下载
              &lt;/span&gt;
            &lt;/button&gt;
          &lt;/div&gt;
        &lt;/div&gt;
        &lt;div class="p-3"&gt;
          &lt;div class="flex items-center gap-2"&gt;
            &lt;input
              type="text"
              :value="imageItem.url"
              class="flex-1 text-xs text-[var(--text-secondary)] bg-[var(--bg-surface)] rounded px-2 py-1 truncate"
              readonly
              @click="copyImageUrl(imageItem.url)"
            /&gt;
            &lt;button
              @click="copyImageUrl(imageItem.url)"
              class="text-[var(--text-secondary)] hover:text-[var(--primary)] transition-colors"
              title="复制链接"
            &gt;
              &lt;svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"&gt;
                &lt;path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 20 01-2-2V6a2 20 012-2h8a2 20 012 2v2m-6 12h8a2 20 002-2v-8a2 20 00-2-2h-8a2 20 00-2 2v8a2 20 002 2z"/&gt;
              &lt;/svg&gt;
            &lt;/button&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/div&gt;
    &lt;/div&gt;

    &lt;!-- 大图预览浮层 --&gt;
    &lt;div
      v-show="previewVisible &amp;&amp; previewUrl"
      class="fixed pointer-events-none"
      style="z-index: 100000;"
      :style="{
        left: previewX + 'px',
        top: previewY + 'px',
        transform: 'translate(-50%, -110%)'
      }"
    &gt;
      &lt;div class="bg-[var(--bg-card)] rounded-xl shadow-2xl p-2 border border-[var(--border)]"&gt;
        &lt;img
          :src="previewUrl"
          alt="预览"
          class="max-w-[400px] max-h-[400px] object-contain rounded-lg"
          style="max-width: 50vw; max-height: 50vh;"
          crossorigin="anonymous"
        /&gt;
      &lt;/div&gt;
    &lt;/div&gt;

    &lt;!-- 空状态 --&gt;
    &lt;div v-if="images.length === 0 &amp;&amp; !loading" class="text-center py-16"&gt;
      &lt;div class="text-[var(--text-secondary)] text-6xl mb-4"&gt;🔍&lt;/div&gt;
      &lt;div class="text-[var(--text-secondary)] text-lg"&gt;{{ source === 'cat' ? '点击"随机获取"开始' : '输入关键词开始搜索图片' }}&lt;/div&gt;
    &lt;/div&gt;

    &lt;!-- 加载状态 --&gt;
    &lt;div v-if="loading" class="text-center py-16"&gt;
      &lt;div class="animate-spin rounded-full h-16 w-16 border-4 border-[var(--primary)]/30 border-t-[var(--primary)] mx-auto"&gt;&lt;/div&gt;
      &lt;div class="text-[var(--text-secondary)] mt-6"&gt;正在搜索...&lt;/div&gt;
    &lt;/div&gt;
  &lt;/div&gt;
&lt;/template&gt;

&lt;script setup&gt;
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

const placeholderText = computed(() =&gt; {
  if (source.value === 'cat') {
    return '该搜索引擎仅返回猫图'
  } else if (source.value === 'lolicon') {
    return '输入二次元图片标签（如：萝莉、少女）'
  }
  return '输入搜索关键词'
})

watch(source, () =&gt; {
  keyword.value = ''
  images.value = []
  hidePreview()
})

// 禁止背景滚动
watch(largePreviewVisible, (val) =&gt; {
  document.body.style.overflow = val ? 'hidden' : ''
})

// 检查 API 配置状态
async function checkConfigStatus() {
  try {
    const res = await fetch('/api/images/config/status')
    const status = await res.json()
    return status
  } catch (error) {
    console.error('获取配置状态失败:', error)
    return {}
  }
}

async function searchImages() {
  if (!keyword.value.trim() &amp;&amp; source.value !== 'cat' &amp;&amp; source.value !== 'lolicon') {
    showToast('请输入搜索关键词', 'warning')
    return
  }

  // 检查配置状态
  const configStatus = await checkConfigStatus()
  const sourceStatus = configStatus[source.value]
  
  if (sourceStatus &amp;&amp; !sourceStatus.configured &amp;&amp; sourceStatus.errors.length &gt; 0) {
    // 优先显示 URL 错误，然后是密钥错误
    const urlError = sourceStatus.errors.find(e =&gt; e.includes('URL'))
    const keyError = sourceStatus.errors.find(e =&gt; e.includes('Key'))
    const idError = sourceStatus.errors.find(e =&gt; e.includes('ID'))
    
    if (urlError) {
      showToast(urlError + '，请在设置中配置', 'warning')
    } else if (keyError) {
      showToast(keyError + '，请在设置中配置', 'warning')
    } else if (idError) {
      showToast(idError + '，请在设置中配置', 'warning')
    } else {
      showToast(sourceStatus.errors[0] + '，请在设置中配置', 'warning')
    }
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

    images.value = urls.map((url, idx) =&gt; ({
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
  if (imageItem.retryCount &lt; 3) {
    imageItem.failed = false
    imageItem.retryCount++
    const separator = imageItem.url.includes('?') ? '&amp;' : '?'
    const newUrl = `${imageItem.url}${separator}_t=${Date.now()}`
    const oldUrl = imageItem.url
    imageItem.url = newUrl
    setTimeout(() =&gt; {
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
  hideTimer = setTimeout(() =&gt; {
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
  if (event.key === 'Escape' &amp;&amp; largePreviewVisible.value) {
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
  navigator.clipboard.writeText(url).then(() =&gt; {
    showToast('链接已复制', 'success')
  }).catch(() =&gt; {
    showToast('复制失败', 'error')
  })
}

function showToast(message, type = 'info') {
  if (toastRef.value) {
    toastRef.value.showToast(message, { type, duration: 3000 })
  }
}

onMounted(() =&gt; {
  document.addEventListener('keydown', handleImageKeydown)
})

onUnmounted(() =&gt; {
  document.removeEventListener('keydown', handleImageKeydown)
})
&lt;/script&gt;

&lt;style scoped&gt;
.backdrop-blur-md {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

img {
  opacity: 1;
  transition: opacity 0.3s ease;
}
&lt;/style&gt;

