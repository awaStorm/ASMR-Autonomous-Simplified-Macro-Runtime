<template>
  <div class="bili-view">
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
      <div class="relative flex flex-col items-center justify-center max-w-6xl max-h-[90vh] p-4" @click.stop>
        <img
          :src="largePreviewImage"
          alt="预览"
          class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
          crossorigin="anonymous"
        />
      </div>
    </div>

    <!-- 配置弹窗 -->
    <div
      v-if="showConfigModal"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="showConfigModal = false"
    >
      <div class="absolute inset-0 bg-black/50"></div>
      <div class="relative bg-[var(--bg-card)] rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-xl font-bold text-[var(--text-primary)]">B站监控配置</h3>
          <button
            @click="showConfigModal = false"
            class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        
        <div class="space-y-4 mb-6">
          <div class="flex justify-between items-center">
            <h4 class="text-sm font-medium text-[var(--text-primary)]">已监控UP主</h4>
            <span class="text-xs text-[var(--text-secondary)]">点击名称切换启用状态</span>
          </div>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <div
              v-for="up in ups"
              :key="up.name"
              class="flex items-center justify-between gap-2 p-2 rounded-lg"
              :class="up.enabled ? 'bg-green-50' : 'bg-[var(--bg-surface)]'"
            >
              <button
                @click="toggleUpEnabled(up.name)"
                class="flex-1 text-left"
              >
                <span :class="up.enabled ? 'text-green-700' : 'text-[var(--text-secondary)]'">{{ up.name }}</span>
              </button>
              <input
                v-model.number="up.check_interval"
                type="number"
                min="1"
                max="1440"
                class="w-20 px-2 py-1 text-sm border border-[var(--border)] rounded text-center text-[var(--text-primary)] bg-[var(--bg-surface)]"
              />
              <span class="text-[var(--text-secondary)] text-xs">分钟</span>
              <button
                @click="removeUp(up.name)"
                class="text-red-500 hover:text-red-700 p-1"
                title="删除"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>
          <div v-if="ups.length === 0" class="text-center text-[var(--text-secondary)] py-4">
            暂无监控的UP主
          </div>
        </div>

        <!-- 启动时检查配置 -->
        <div class="flex items-center justify-between mb-6">
          <span class="text-[var(--text-primary)]">启动时自动检查所有UP主</span>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              v-model="checkOnStart"
              type="checkbox"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        <!-- 调度器状态 -->
        <div class="flex items-center justify-between mb-6 p-3 bg-[var(--bg-surface)] rounded-lg">
          <span class="text-[var(--text-primary)]">定时任务状态</span>
          <span
            :class="[
              'px-3 py-1 rounded-full text-sm font-medium',
              schedulerRunning ? 'bg-green-100 text-green-700' : 'bg-[var(--bg-card)] text-[var(--text-secondary)]'
            ]"
          >
            {{ schedulerRunning ? '运行中' : '已停止' }}
          </span>
        </div>

        <!-- 操作按钮 -->
        <div class="flex gap-3">
          <button
            @click="saveConfig"
            class="flex-1 px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
          >
            保存配置
          </button>
          <button
            @click="toggleScheduler"
            :class="[
              'flex-1 px-4 py-2 rounded-lg transition-colors',
              schedulerRunning ? 'bg-[var(--bg-surface)] hover:bg-[var(--border)] text-[var(--text-primary)]' : 'bg-green-600 hover:bg-green-700 text-white'
            ]"
          >
            {{ schedulerRunning ? '停止调度' : '启动调度' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 添加UP主弹窗 -->
    <div
      v-if="showAddUpModal"
      class="fixed inset-0 z-50 flex items-center justify-center"
      @click.self="showAddUpModal = false"
    >
      <div class="absolute inset-0 bg-black/50"></div>
      <div class="relative bg-[var(--bg-card)] rounded-xl shadow-2xl p-6 w-full max-w-md mx-4">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-xl font-bold text-[var(--text-primary)]">添加新UP主</h3>
          <button
            @click="showAddUpModal = false"
            class="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-[var(--text-primary)] mb-1">UP主名称</label>
            <input
              v-model="newUpName"
              type="text"
              placeholder="输入UP主名称"
              class="w-full px-3 py-2 border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-[var(--bg-surface)] text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--text-primary)] mb-1">UP主UID</label>
            <input
              v-model="newUpUid"
              type="text"
              placeholder="输入UP主UID"
              class="w-full px-3 py-2 border border-[var(--border)] rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-[var(--bg-surface)] text-[var(--text-primary)] placeholder-[var(--text-secondary)]"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-[var(--text-primary)] mb-2">检查间隔（分钟）</label>
            <div class="grid grid-cols-4 gap-2 mb-2">
              <button
                v-for="option in intervalOptions"
                :key="option.value"
                @click="newUpInterval = option.value"
                :class="[
                  'px-2 py-1 text-sm rounded-lg border transition-colors',
                  newUpInterval === option.value
                    ? 'bg-[var(--primary)] text-white border-[var(--primary)]'
                    : 'bg-[var(--bg-surface)] text-[var(--text-primary)] border-[var(--border)] hover:border-[var(--primary)]'
                ]"
              >
                {{ option.label }}
              </button>
            </div>
            <input
              v-model.number="newUpInterval"
              type="number"
              min="1"
              max="1440"
              class="w-full px-3 py-2 border border-[var(--border)] rounded-lg text-center focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-[var(--bg-surface)] text-[var(--text-primary)]"
            />
          </div>
          <button
            @click="addUp"
            :disabled="!newUpName || !newUpUid"
            class="w-full px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            添加
          </button>
        </div>
      </div>
    </div>

    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-[var(--text-primary)]">B站监控</h2>
      <button
        @click="showConfigModal = true"
        class="flex items-center gap-2 px-4 py-2 bg-[var(--bg-surface)] hover:bg-[var(--border)] rounded-lg transition-colors text-[var(--text-primary)]"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        <span class="text-sm font-medium">设置</span>
      </button>
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

    <!-- 登录状态卡片 -->
    <div class="bg-[var(--bg-card)] p-4 rounded-lg shadow mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div :class="['w-3 h-3 rounded-full', status.logged_in ? 'bg-green-500' : 'bg-red-500']"></div>
          <span class="font-medium text-[var(--text-primary)]">{{ status.logged_in ? '已登录B站' : '未登录' }}</span>
        </div>
        <div class="flex gap-2">
          <button
            v-if="!status.logged_in"
            @click="showLoginQr"
            :disabled="qrPolling"
            class="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors text-sm disabled:opacity-50"
          >
            {{ qrPolling ? '等待扫码...' : '扫码登录' }}
          </button>
          <template v-else>
            <button
              @click="checkAllDynamics"
              :disabled="loading"
              class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm disabled:opacity-50"
            >
              {{ loading ? '检查中...' : '检查新动态' }}
            </button>
            <button
              @click="showLoginQr"
              :disabled="qrPolling"
              class="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm disabled:opacity-50"
            >
              {{ qrPolling ? '等待扫码...' : '重新登录' }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- UP主列表 -->
    <div class="bg-[var(--bg-card)] rounded-lg shadow">
      <div class="p-4 border-b border-[var(--border)] flex justify-between items-center">
        <h3 class="font-bold text-[var(--text-primary)]">监控的UP主 ({{ status.up_count }})</h3>
        <button
          @click="showAddUpModal = true"
          class="w-8 h-8 flex items-center justify-center text-[var(--primary)] hover:bg-[var(--bg-surface)] rounded-full transition-colors"
          title="添加UP主"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
        </button>
      </div>
      <div class="divide-y divide-[var(--border)]">
        <div
          v-for="up in ups"
          :key="up.name"
          class="p-4"
        >
          <div class="flex items-center justify-between cursor-pointer hover:bg-[var(--bg-surface)] -mx-4 px-4 py-2 rounded" @click="toggleUp(up.name)">
            <div class="flex items-center gap-3">
              <span class="text-xl text-[var(--text-primary)]">{{ expandedUps.includes(up.name) ? '▼' : '▶' }}</span>
              <div>
                <div class="font-medium text-[var(--text-primary)]">{{ up.name }}</div>
                <div class="text-sm text-[var(--text-secondary)]">
                  UID: {{ up.uid }} | 间隔: {{ up.check_interval }}分钟 | 已发: {{ up.sent_count || 0 }} | 缓存: {{ up.cache_count || 0 }}
                </div>
              </div>
            </div>
            <button
              @click.stop="checkSingleUp(up.name)"
              :disabled="loading || !status.logged_in"
              class="px-3 py-1 text-sm border border-[var(--primary)] text-[var(--primary)] rounded hover:bg-[var(--bg-surface)] transition-colors disabled:opacity-50"
            >
              检查
            </button>
          </div>

          <!-- 展开的缓存图片 -->
          <div v-if="expandedUps.includes(up.name)" class="mt-4 pt-4 border-t border-[var(--border)]">
            <div v-if="cachedImages[up.name] && cachedImages[up.name].length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              <div
                v-for="(img, idx) in cachedImages[up.name]"
                :key="idx"
                class="relative group aspect-square overflow-hidden rounded-lg border border-[var(--border)] cursor-pointer"
                @click="openLargePreview(biliApi.getImageProxyUrl(img.url))"
                @mouseenter="handleMouseEnter(img, $event)"
                @mousemove="handleMouseMove($event)"
                @mouseleave="handleMouseLeave"
              >
                <img
                  :src="biliApi.getImageProxyUrl(img.url)"
                  :alt="img.description"
                  class="w-full h-full object-cover"
                  loading="lazy"
                  crossorigin="anonymous"
                />
                <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center">
                  <button
                    @click.stop="downloadImage(img.url)"
                    class="opacity-0 group-hover:opacity-100 backdrop-blur-md bg-white/30 border border-white/50 px-3 py-1 rounded-lg text-white text-sm"
                  >
                    下载
                  </button>
                </div>
              </div>
            </div>
            <div v-else class="text-center text-[var(--text-secondary)] py-4">
              暂无缓存图片
            </div>
          </div>
        </div>
        <div v-if="ups.length === 0" class="p-8 text-center text-[var(--text-secondary)]">
          暂无监控的UP主
        </div>
      </div>
    </div>

    <!-- 新动态展示 -->
    <div v-if="newDynamics.length > 0" class="mt-6">
      <h3 class="font-bold text-[var(--text-primary)] mb-4">最新发现的图片</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        <div
          v-for="(dyn, index) in newDynamics"
          :key="index"
          class="bg-[var(--bg-card)] rounded-lg shadow overflow-hidden"
        >
          <div class="relative group cursor-pointer"
            @click="openLargePreview(biliApi.getImageProxyUrl(dyn.url))"
            @mouseenter="handleMouseEnter(dyn, $event)"
            @mousemove="handleMouseMove($event)"
            @mouseleave="handleMouseLeave"
          >
            <img
              :src="biliApi.getImageProxyUrl(dyn.url)"
              :alt="dyn.description"
              class="w-full aspect-square object-cover"
              loading="lazy"
              crossorigin="anonymous"
            />
            <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center">
              <button
                @click.stop="downloadImage(dyn.url)"
                class="opacity-0 group-hover:opacity-100 backdrop-blur-md bg-white/30 border border-white/50 px-3 py-1 rounded-lg text-white text-sm"
              >
                下载
              </button>
            </div>
          </div>
          <div class="p-3">
            <div class="text-sm text-[var(--text-primary)] truncate">{{ dyn.description || '无描述' }}</div>
            <div class="text-xs text-[var(--text-secondary)] mt-1">{{ dyn.pub_time }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 登录二维码弹窗 -->
    <div v-if="qrModalShown" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="closeQrModal">
      <div class="bg-[var(--bg-card)] rounded-xl p-6 max-w-sm w-full mx-4">
        <h3 class="text-lg font-bold mb-4 text-center text-[var(--text-primary)]">扫码登录B站</h3>
        <div v-if="qrLoading" class="flex flex-col items-center justify-center py-8">
          <div class="animate-spin rounded-full h-12 w-12 border-4 border-[var(--primary)]/30 border-t-[var(--primary)] mb-4"></div>
          <p class="text-sm text-[var(--text-secondary)]">正在获取二维码...</p>
        </div>
        <div v-else-if="qrCodeUrl" class="text-center">
          <div class="inline-block bg-[var(--bg-surface)] p-4 rounded-lg border border-[var(--border)]">
            <img 
              :src="qrCodeUrl" 
              alt="登录二维码" 
              class="w-48 h-48 rounded-lg" 
              crossorigin="anonymous"
              @error="handleQrImageError"
            />
          </div>
          <p v-if="qrStatus === 'scanned'" class="text-sm text-green-500 mt-3">
            <span class="inline-flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
              已扫码，请在APP中确认
            </span>
          </p>
          <p v-else-if="qrStatus === 'expired'" class="text-sm text-red-500 mt-3">二维码已过期，请刷新</p>
          <p v-else class="text-sm text-[var(--text-secondary)] mt-3">请使用B站APP扫码登录</p>
          <p class="text-xs text-[var(--text-secondary)] mt-2">有效期2分钟</p>
          <!-- 倒计时 -->
          <div class="mt-3">
            <div class="w-full bg-[var(--bg-surface)] rounded-full h-1.5">
              <div 
                class="bg-[var(--primary)] h-1.5 rounded-full"
                :style="{ width: qrTimeRemaining + '%' }"
              ></div>
            </div>
          </div>
        </div>
        <div v-else-if="qrError" class="text-center py-8">
          <div class="text-4xl mb-3">⚠️</div>
          <p class="text-red-500">{{ qrError }}</p>
          <button
            @click="refreshQr"
            class="mt-4 px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:bg-[var(--primary-hover)] transition-colors"
          >
            重新获取
          </button>
        </div>
        <div v-else class="text-center py-8">
          <div class="text-4xl mb-3">🔄</div>
          <p class="text-[var(--text-secondary)]">准备获取二维码...</p>
        </div>
        <div class="mt-4 flex justify-end gap-2">
          <button
            v-if="qrStatus === 'expired'"
            @click="refreshQr"
            class="px-4 py-2 text-[var(--primary)] hover:bg-[var(--bg-surface)] rounded-lg transition-colors"
          >
            刷新
          </button>
          <button
            v-if="!qrPolling || qrStatus === 'expired'"
            @click="closeQrModal"
            class="px-4 py-2 text-[var(--text-primary)] hover:bg-[var(--bg-surface)] rounded-lg transition-colors"
          >
            关闭
          </button>
          <button
            v-if="qrPolling && qrStatus !== 'expired'"
            :disabled="true"
            class="px-4 py-2 text-[var(--text-secondary)] bg-[var(--bg-surface)] rounded-lg cursor-not-allowed"
          >
            等待中...
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { biliApi } from '../api'
import Toast from '../components/Toast.vue'

const toastRef = ref(null)
const loading = ref(false)
const qrPolling = ref(false)
const qrLoading = ref(false)
const qrStatus = ref('')
const qrCodeUrl = ref('')
const qrError = ref('')
const qrModalShown = ref(false)
const qrTimeRemaining = ref(100)
const status = ref({ logged_in: false, is_running: false, up_count: 0, ups: [] })
const ups = ref([])

// 配置相关
const showConfigModal = ref(false)
const showAddUpModal = ref(false)
const checkOnStart = ref(false)
const schedulerRunning = ref(false)

// 添加UP主相关
const newUpName = ref('')
const newUpUid = ref('')
const newUpInterval = ref(60)
const intervalOptions = [
  { label: '15min', value: 15 },
  { label: '30min', value: 30 },
  { label: '60min', value: 60 },
  { label: '90min', value: 90 },
]

const newDynamics = ref([])
const expandedUps = ref([])
const cachedImages = ref({})
const pollTimer = ref(null)
const qrCountdownTimer = ref(null)
let currentQrcodeKey = ''

// 预览相关
const previewX = ref(0)
const previewY = ref(0)
const previewVisible = ref(false)
const previewUrl = ref('')
let hideTimer = null

// 大图预览相关
const largePreviewImage = ref('')
const largePreviewVisible = ref(false)

// 禁止背景滚动
watch([showConfigModal, showAddUpModal, qrModalShown, largePreviewVisible], ([config, addUp, qr, large]) => {
  if (config || addUp || qr || large) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(async () => {
  loadStatus()
  await loadUps()
  await loadConfig()
  loadSchedulerStatus()
  document.addEventListener('keydown', handleBiliKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleBiliKeydown)
  clearPollTimer()
})

function clearPollTimer() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

async function loadStatus() {
  try {
    const res = await biliApi.getStatus()
    status.value = res.data
  } catch (error) {
    console.error('加载状态失败', error)
  }
}

async function loadUps() {
  try {
    const res = await biliApi.getUps()
    ups.value = res.data.ups || []
  } catch (error) {
    console.error('加载UP主列表失败', error)
  }
}

async function showLoginQr() {
  qrModalShown.value = true
  qrLoading.value = true
  qrStatus.value = ''
  qrCodeUrl.value = ''
  qrError.value = ''
  qrTimeRemaining.value = 100
  clearPollTimer()
  clearCountdownTimer()

  try {
    const response = await fetch('/api/bili/login/qr')
    if (!response.ok) {
      throw new Error('获取二维码失败')
    }

    currentQrcodeKey = response.headers.get('X-QRCode-Key')
    const blob = await response.blob()
    qrCodeUrl.value = URL.createObjectURL(blob)
    
    qrLoading.value = false
    qrPolling.value = true

    await biliApi.pollLogin(currentQrcodeKey)

    let elapsed = 0
    pollTimer.value = setInterval(async () => {
      elapsed += 2
      qrTimeRemaining.value = Math.max(0, 100 - (elapsed / 120 * 100))

      if (elapsed >= 120) {
        qrStatus.value = 'expired'
        qrPolling.value = false
        clearPollTimer()
        clearCountdownTimer()
        URL.revokeObjectURL(qrCodeUrl.value)
        return
      }

      try {
        const resultRes = await biliApi.getLoginResult(currentQrcodeKey)
        if (resultRes.data.success) {
          clearPollTimer()
          clearCountdownTimer()
          qrPolling.value = false
          qrStatus.value = 'success'
          URL.revokeObjectURL(qrCodeUrl.value)
          setTimeout(() => {
            showToast('登录成功！', 'success')
            closeQrModal()
            loadStatus()
            loadUps()
          }, 500)
        } else if (resultRes.data.status === 'done' && !resultRes.data.success) {
          clearPollTimer()
          clearCountdownTimer()
          qrPolling.value = false
          qrStatus.value = 'expired'
          URL.revokeObjectURL(qrCodeUrl.value)
          showToast(resultRes.data.message || '登录失败', 'error')
        } else if (resultRes.data.message === 'scanned') {
          qrStatus.value = 'scanned'
        }
      } catch (err) {
        console.error('查询结果错误', err)
      }
    }, 2000)
  } catch (error) {
    qrLoading.value = false
    qrError.value = '获取二维码失败，请检查网络连接'
    showToast(qrError.value, 'error')
    console.error(error)
  }
}

function startCountdown() {
  let remaining = 100
  qrCountdownTimer.value = setInterval(() => {
    remaining -= (100 / 60) // 2分钟=120秒，每秒减少约0.83%
    qrTimeRemaining.value = Math.max(0, remaining)
  }, 1000)
}

function clearCountdownTimer() {
  if (qrCountdownTimer.value) {
    clearInterval(qrCountdownTimer.value)
    qrCountdownTimer.value = null
  }
}

function handleQrImageError() {
  console.error('二维码图片加载失败')
  qrError.value = '二维码图片加载失败，请刷新重试'
}

async function refreshQr() {
  clearPollTimer()
  qrPolling.value = false
  showLoginQr()
}

function closeQrModal() {
  qrModalShown.value = false
  clearPollTimer()
  qrPolling.value = false
}

async function toggleUp(upName) {
  const idx = expandedUps.value.indexOf(upName)
  if (idx === -1) {
    expandedUps.value.push(upName)
    await loadUpCache(upName)
  } else {
    expandedUps.value.splice(idx, 1)
  }
}

async function loadUpCache(upName) {
  try {
    const res = await biliApi.getCache(upName)
    if (res.data.success) {
      cachedImages.value[upName] = res.data.images
    }
  } catch (error) {
    console.error('加载缓存图片失败', error)
  }
}

async function checkSingleUp(upName) {
  if (!status.value.logged_in) {
    showToast('请先登录B站', 'warning')
    return
  }

  loading.value = true
  try {
    const res = await biliApi.checkUp(upName)
    if (res.data.success && res.data.images.length > 0) {
      newDynamics.value = res.data.images
      showToast(`${upName} 发现 ${res.data.new_count} 张新图片`, 'success')
      await loadUpCache(upName)
      await loadUps()
    } else {
      showToast(`${upName} 没有新图片`, 'info')
    }
  } catch (error) {
    showToast('检查失败', 'error')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function checkAllDynamics() {
  if (!status.value.logged_in) {
    showToast('请先登录B站', 'warning')
    return
  }

  loading.value = true
  newDynamics.value = []
  try {
    const res = await biliApi.checkAll()
    if (res.data.success && res.data.total_new > 0) {
      const allImages = []
      for (const [upName, images] of Object.entries(res.data.results)) {
        allImages.push(...images)
        await loadUpCache(upName)
      }
      newDynamics.value = allImages
      showToast(`共发现 ${res.data.total_new} 张新图片`, 'success')
      await loadUps()
    } else {
      showToast('没有发现新图片', 'info')
    }
  } catch (error) {
    showToast('检查失败', 'error')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 图片预览相关
function handleMouseEnter(imageItem, event) {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
  previewUrl.value = biliApi.getImageProxyUrl(imageItem.url)
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

function handleBiliKeydown(event) {
  if (event.key === 'Escape' && largePreviewVisible.value) {
    closeLargePreview()
  }
}

function openLargePreview(imageUrl) {
  largePreviewImage.value = imageUrl
  largePreviewVisible.value = true
}

function closeLargePreview() {
  largePreviewImage.value = ''
  largePreviewVisible.value = false
}

async function downloadImage(url) {
  try {
    const proxyUrl = biliApi.getImageProxyUrl(url)
    const response = await fetch(proxyUrl)
    const blob = await response.blob()
    const urlObj = new URL(url)
    const fileName = urlObj.pathname.split('/').pop() || `bili_${Date.now()}.jpg`

    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)

    showToast('下载成功', 'success')
  } catch (error) {
    showToast('下载失败，尝试直接打开', 'warning')
    window.open(url, '_blank')
  }
}

// 配置相关方法
async function loadConfig() {
  try {
    const res = await biliApi.getConfig()
    if (res.data.success) {
      const config = res.data.config
      checkOnStart.value = config.check_on_start || false
      // 更新UP主间隔配置
      if (config.up_intervals) {
        for (const up of ups.value) {
          if (config.up_intervals[up.name]) {
            up.check_interval = config.up_intervals[up.name]
          }
        }
      }
    }
  } catch (error) {
    console.error('加载配置失败', error)
  }
}

async function saveConfig() {
  try {
    // 先保存每个UP主的间隔配置
    for (const up of ups.value) {
      await biliApi.updateInterval(up.name, up.check_interval)
    }
    // 保存启动时检查配置
    await biliApi.saveConfig(checkOnStart.value)
    showToast('配置保存成功', 'success')
    showConfigModal.value = false
    await loadUps()
    await loadStatus()
  } catch (error) {
    showToast('保存失败', 'error')
    console.error(error)
  }
}

async function toggleScheduler() {
  try {
    if (schedulerRunning.value) {
      await biliApi.stopScheduler()
      schedulerRunning.value = false
      showToast('调度器已停止', 'info')
    } else {
      // 启动时根据配置决定是否立即检查
      await biliApi.startScheduler(checkOnStart.value)
      schedulerRunning.value = true
      showToast('调度器已启动', 'success')
    }
    await loadUps()
    await loadStatus()
  } catch (error) {
    showToast('操作失败', 'error')
    console.error(error)
  }
}

// UP主管理方法
async function addUp() {
  if (!newUpName.value || !newUpUid.value) {
    showToast('请填写完整信息', 'warning')
    return
  }

  try {
    const res = await biliApi.addUp(newUpName.value, newUpUid.value, newUpInterval.value)
    if (res.data.success) {
      showToast(res.data.message, 'success')
      showAddUpModal.value = false
      newUpName.value = ''
      newUpUid.value = ''
      newUpInterval.value = 60
      await loadUps()
      await loadStatus()
    } else {
      showToast(res.data.message, 'error')
    }
  } catch (error) {
    showToast('添加失败', 'error')
    console.error(error)
  }
}

async function removeUp(upName) {
  const confirmed = await toastRef.value.confirm(`确定要删除UP主 ${upName} 吗？`)
  if (!confirmed) {
    return
  }

  try {
    const res = await biliApi.removeUp(upName)
    if (res.data.success) {
      showToast(res.data.message, 'success')
      await loadUps()
      await loadStatus()
    } else {
      showToast(res.data.message, 'error')
    }
  } catch (error) {
    showToast('删除失败', 'error')
    console.error(error)
  }
}

async function toggleUpEnabled(upName) {
  try {
    const res = await biliApi.toggleUp(upName)
    if (res.data.success) {
      showToast(res.data.message, 'success')
      await loadUps()
    } else {
      showToast(res.data.message, 'error')
    }
  } catch (error) {
    showToast('操作失败', 'error')
    console.error(error)
  }
}

async function loadSchedulerStatus() {
  try {
    const res = await biliApi.getSchedulerStatus()
    if (res.data.success) {
      schedulerRunning.value = res.data.is_running
    }
  } catch (error) {
    console.error('加载调度器状态失败', error)
  }
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
