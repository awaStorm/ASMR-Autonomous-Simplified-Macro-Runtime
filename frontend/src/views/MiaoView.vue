<template>
  <div class="miao-container">
    <!-- 顶部统计区域 -->
    <div class="top-section">
      <div class="moe-counter">
        <span class="counter-label">全站总点击</span>
        <img 
          :src="counterImageUrl"
          class="counter-image"
          alt="点击计数"
        />
      </div>
    </div>

    <!-- 中间柱状图区域 -->
    <div class="chart-section">
      <div class="chart-header">
        <div class="title-row">
          <h2>点击量统计</h2>
        </div>
        <div class="controls">
          <div class="granularity-buttons">
            <button 
              v-for="g in granularities" 
              :key="g.value"
              :class="['gran-btn', { active: granularity === g.value }]"
              @click="changeGranularity(g.value)"
            >
              {{ g.label }}
            </button>
          </div>
          <div class="direction-buttons">
            <button 
              :class="['dir-btn', { active: direction === 'vertical' }]"
              @click="changeDirection('vertical')"
            >
              ↕ 纵向
            </button>
            <button 
              :class="['dir-btn', { active: direction === 'horizontal' }]"
              @click="changeDirection('horizontal')"
            >
              ↔ 横向
            </button>
          </div>
        </div>
      </div>
      
      <div class="chart-wrapper" :class="{ 'pointer': granularity === 'week' }" @click="handleChartClick">
        <div ref="chartRef" class="main-chart"></div>
      </div>
    </div>

    <!-- 底部详细统计区域（仅周视图显示） -->
    <div v-if="granularity === 'week' && selectedDay" class="detail-section">
      <div class="detail-header">
        <h3>{{ selectedDay.label }} 的页面分布</h3>
        <span class="detail-date">{{ selectedDay.date }}</span>
      </div>
      <div ref="detailChartRef" class="detail-chart"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

// 状态
const granularity = ref('week')
const direction = ref('vertical')
const totalClicks = ref(0)
const chartData = ref([])
const detailData = ref({})
const selectedDay = ref(null)

// 图表实例
let mainChart = null
let detailChart = null

// 时间粒度选项
const granularities = [
  { value: 'year', label: '年' },
  { value: 'month', label: '月' },
  { value: 'week', label: '周' }
]

// 页面名称映射
const pageNames = {
  '/': '首页',
  '/home': '首页',
  '/todo': '待办事项',
  '/image': '图片搜索',
  '/bili': 'B站监控',
  '/jm': '禁漫下载',
  '/miao': '喵呜统计',
  'home': '首页',
  'todo': '待办事项',
  'image': '图片搜索',
  'bili': 'B站监控',
  'jm': '禁漫下载',
  'miao': '喵呜统计',
  'Unknown': '未知页面'
}

// 图表颜色
const chartColors = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899']

// Moe-counter 主题列表
const moeThemes = [
  'gelbooru', 'green', 'rule34', 'original-new', 'booru-smtg',
  'booru-qualityhentais', 'booru-lisu', 'booru-lewd', 'booru-jaypee', 'asoul'
]

// 随机选择的主题
const currentTheme = ref('')

// 计算 Moe-counter 图片 URL
const counterImageUrl = computed(() => {
  const theme = currentTheme.value || 'miku'
  return `https://count.getloli.com/get/@miao-total?theme=${theme}&num=${totalClicks.value}&darkmode=0`
})

// 随机选择主题
function randomizeTheme() {
  const randomIndex = Math.floor(Math.random() * moeThemes.length)
  currentTheme.value = moeThemes[randomIndex]
}

// 获取统计数据
async function fetchStats() {
  try {
    const response = await fetch(`/api/click/stats/aggregate?granularity=${granularity.value}&direction=${direction.value}`)
    const data = await response.json()
    
    totalClicks.value = data.total
    chartData.value = data.data
    detailData.value = data.detail_data || {}
    
    nextTick(() => {
      updateMainChart()
    })
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 更新主图表
function updateMainChart() {
  if (!mainChart) {
    mainChart = echarts.init(document.querySelector('.main-chart'))
  }
  
  const isHorizontal = direction.value === 'horizontal'
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: isHorizontal ? 'shadow' : 'shadow'
      },
      formatter: (params) => {
        const item = params[0]
        return `<div style="padding: 8px;">
          <div style="font-weight: bold; margin-bottom: 4px;">${item.name}</div>
          <div style="color: #666;">点击数: <span style="color: ${item.color}; font-weight: bold;">${item.value}</span></div>
        </div>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: isHorizontal ? {
      type: 'value',
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { color: '#6b7280' }
    } : {
      type: 'category',
      data: chartData.value.map(item => item.label),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { color: '#6b7280' }
    },
    yAxis: isHorizontal ? {
      type: 'category',
      data: chartData.value.map(item => item.label),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { color: '#6b7280' }
    } : {
      type: 'value',
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisTick: { show: false },
      axisLabel: { color: '#6b7280' }
    },
    series: [{
      type: 'bar',
      data: chartData.value.map(item => ({
        value: item.count,
        itemStyle: {
          borderRadius: isHorizontal ? [0, 8, 8, 0] : [8, 8, 0, 0],
          color: new echarts.graphic.LinearGradient(
            isHorizontal ? 0 : 0, isHorizontal ? 0 : 0,
            isHorizontal ? 1 : 0, isHorizontal ? 0 : 1,
            [
              { offset: 0, color: '#818cf8' },
              { offset: 1, color: '#6366f1' }
            ]
          )
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(
              isHorizontal ? 0 : 0, isHorizontal ? 0 : 0,
              isHorizontal ? 1 : 0, isHorizontal ? 0 : 1,
              [
                { offset: 0, color: '#a5b4fc' },
                { offset: 1, color: '#818cf8' }
              ]
            )
          }
        }
      })),
      barWidth: '50%'
    }]
  }
  
  mainChart.setOption(option, true)
  
  // 绑定点击事件（仅周视图）
  if (granularity.value === 'week') {
    mainChart.off('click')
    mainChart.on('click', (params) => {
      const clickedItem = chartData.value[params.dataIndex]
      if (clickedItem && detailData.value[clickedItem.date]) {
        selectedDay.value = clickedItem
        // 关键：等 Vue 把底部的 v-if DOM 渲染出来后再执行
        nextTick(() => {
          updateDetailChart(clickedItem.date)
        })
      }
    })
  }
}

// 更新详细图表
function updateDetailChart(date) {
  // 1. 尝试获取最新的 DOM
  const detailChartEl = document.querySelector('.detail-chart')
  
  if (!detailChartEl) {
    // 如果还是没找到，可以在这里递归尝试一次 nextTick，或者报错
    console.warn('Detail chart DOM element not found')
    return
  }
  
  // 2. 检查该 DOM 是否已经有关联的 ECharts 实例
  // 防止重复 init 导致的警告
  let existingInstance = echarts.getInstanceByDom(detailChartEl)
  if (!existingInstance) {
    detailChart = echarts.init(detailChartEl)
  } else {
    detailChart = existingInstance
  }
  
  const dayData = detailData.value[date] || {}
  const items = Object.entries(dayData).map(([key, value]) => ({
    name: pageNames[key] || key,
    value: value
  })).sort((a, b) => b.value - a.value)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `<div style="padding: 8px;">
          <div style="font-weight: bold; margin-bottom: 4px;">${params.name}</div>
          <div style="color: #666;">点击数: <span style="color: ${params.color}; font-weight: bold;">${params.value}</span></div>
        </div>`
      }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        position: 'outside',
        formatter: '{b}: {c}',
        color: document.documentElement.classList.contains('dark') ? '#f9fafb' : '#374151'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold',
          color: document.documentElement.classList.contains('dark') ? '#f9fafb' : '#374151'
        }
      },
      labelLine: {
        show: true,
        lineStyle: {
          color: document.documentElement.classList.contains('dark') ? '#9ca3af' : '#6b7280'
        }
      },
      data: items.map((item, index) => ({
        value: item.value,
        name: item.name,
        itemStyle: {
          color: chartColors[index % chartColors.length]
        }
      }))
    }]
  }
  
  detailChart.setOption(option, true)
}

// 切换时间粒度
function changeGranularity(value) {
  granularity.value = value
  selectedDay.value = null
  // 清理饼状图实例，确保下次进入周视图时是全新的初始化过程
  if (detailChart) {
    detailChart.dispose()
    detailChart = null
  }
  fetchStats()
}

// 切换方向
function changeDirection(value) {
  direction.value = value
  nextTick(() => {
    updateMainChart()
  })
}

// 处理图表点击
function handleChartClick() {
  // 由echarts事件处理
}

// 窗口大小变化时重新调整图表
function handleResize() {
  if (mainChart) mainChart.resize()
  if (detailChart) detailChart.resize()
}

// 定时器变量
let refreshTimer = null

// 启动定时器
function startRefreshTimer() {
  if (refreshTimer) clearInterval(refreshTimer)
  // 可见时1分钟，不可见时2分钟
  const interval = document.visibilityState === 'visible' ? 60000 : 120000
  refreshTimer = setInterval(() => {
    fetchStats()
  }, interval)
}

// 处理页面可见性变化
function handleVisibilityChange() {
  startRefreshTimer()
}

onMounted(() => {
  // 随机选择主题
  randomizeTheme()
  
  fetchStats()
  window.addEventListener('resize', handleResize)
  
  // 监听页面可见性变化
  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  // 启动定时刷新
  startRefreshTimer()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (refreshTimer) clearInterval(refreshTimer)
  if (mainChart) mainChart.dispose()
  if (detailChart) detailChart.dispose()
})

watch([granularity, direction], () => {
  fetchStats()
})
</script>

<style scoped>
.miao-container {
  min-height: 100vh;
  padding: 20px;
  background: var(--bg-page);
}

.top-section {
  margin-bottom: 30px;
}

.moe-counter {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  padding: 30px 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.dark .moe-counter {
  background: var(--bg-card);
}

.counter-label {
  font-size: 18px;
  color: var(--text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.counter-image {
  height: 100px;
  image-rendering: -webkit-optimize-contrast;
}

.chart-section {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-row h2 {
  font-size: 24px;
  color: var(--text-primary);
  margin: 0;
}

.subtitle {
  font-size: 16px;
  color: #f59e0b;
}

.controls {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.granularity-buttons {
  display: flex;
  gap: 8px;
}

.gran-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.gran-btn:hover {
  background: var(--border);
}

.gran-btn.active {
  background: #f59e0b;
  color: white;
}

.direction-buttons {
  display: flex;
  gap: 8px;
}

.dir-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.dir-btn:hover {
  background: var(--border);
}

.dir-btn.active {
  background: var(--primary);
  color: white;
}

.chart-wrapper {
  cursor: default;
}

.chart-wrapper.pointer {
  cursor: pointer;
}

.main-chart {
  height: 400px;
  width: 100%;
}

.detail-section {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.detail-header h3 {
  font-size: 18px;
  color: var(--text-primary);
  margin: 0;
}

.detail-date {
  font-size: 14px;
  color: var(--text-secondary);
}

.detail-chart {
  height: 300px;
  width: 100%;
}

@media (max-width: 768px) {
  .miao-container {
    padding: 10px;
  }
  
  .moe-counter {
    flex-direction: column;
    text-align: center;
    padding: 20px;
  }
  
  .counter-icon {
    font-size: 40px;
  }
  
  .counter-image {
    height: 50px;
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .main-chart {
    height: 300px;
  }
  
  .detail-chart {
    height: 250px;
  }
}
</style>