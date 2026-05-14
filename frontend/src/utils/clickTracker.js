/**
 * 全局点击计数器
 * 监听整个网站的用户点击行为，本地暂存后批量上报到后端
 */

const STORAGE_KEY = 'click_stats'
const REPORT_INTERVAL = 3600000 // 1小时
const DEBOUNCE_DELAY = 500 // 防抖延迟

// 预设页面列表
const PREDEFINED_PAGES = [
  'home',
  'todo',
  'image', 
  'bili',
  'jm',
  'miao'
]

class ClickTracker {
  constructor() {
    this.stats = null
    this.debounceMap = new Map()
    this.reportTimer = null
    this.isReporting = false
    this.failedRequests = []
    
    this.init()
  }

  init() {
    // 加载本地存储的数据
    this.loadStats()
    
    // 绑定全局点击事件
    document.addEventListener('click', this.handleClick.bind(this), true)
    
    // 绑定页面关闭事件
    window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this))
    
    // 设置定时上报
    this.scheduleReport()
    
    // 恢复失败的请求队列
    this.loadFailedRequests()
    
    // 提供全局调试接口
    window.__forceReportClickStats = this.forceReport.bind(this)
  }

  loadStats() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        this.stats = JSON.parse(stored)
        
        // 版本检查和迁移
        if (this.stats.version !== '1.0') {
          this.migrateStats()
        }
      } else {
        this.reset()
      }
    } catch (e) {
      console.error('加载点击统计数据失败:', e)
      this.reset()
    }
  }

  saveStats() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.stats))
    } catch (e) {
      console.error('保存点击统计数据失败:', e)
    }
  }

  reset() {
    this.stats = {
      version: '1.0',
      start_time: Date.now(),
      last_report_time: 0,
      counts: {},
      pending_report: false
    }
    this.saveStats()
  }

  migrateStats() {
    // 如果版本不匹配，重置为新版本
    const oldCounts = this.stats.counts || {}
    this.stats = {
      version: '1.0',
      start_time: Date.now(),
      last_report_time: 0,
      counts: oldCounts,
      pending_report: false
    }
    this.saveStats()
  }

  getPagePath() {
    let path = window.location.pathname
    
    // 处理根路径（显示首页）
    if (path === '/') {
      return 'home'
    }
    
    // 去掉开头的斜杠
    if (path.startsWith('/')) {
      path = path.slice(1)
    }
    
    // 处理空路径（显示首页）
    if (!path) {
      return 'home'
    }
    
    // 处理带参数的路径
    const index = path.indexOf('?')
    if (index > -1) {
      path = path.slice(0, index)
    }
    
    return path
  }

  shouldCount(target) {
    // 忽略开发者工具和控制台
    if (target.tagName === 'IFRAME') return false
    
    // 使用唯一key进行防抖
    const key = `${target.tagName}_${target.innerText.substring(0, 50)}_${target.className}`
    const now = Date.now()
    
    const lastClick = this.debounceMap.get(key)
    if (lastClick && now - lastClick < DEBOUNCE_DELAY) {
      return false
    }
    
    this.debounceMap.set(key, now)
    
    // 清理过期的防抖记录
    setTimeout(() => {
      this.debounceMap.delete(key)
    }, DEBOUNCE_DELAY + 100)
    
    return true
  }

  handleClick(event) {
    const target = event.target
    
    // 检查是否应该计数（防抖）
    if (!this.shouldCount(target)) {
      return
    }
    
    // 获取页面路径
    const page = this.getPagePath()
    
    // 增加计数
    this.increment(page)
  }

  increment(page) {
    if (!this.stats) {
      this.loadStats()
    }
    
    // 检查是否属于预设页面，否则归类为 Unknown
    let pageKey = page
    if (!PREDEFINED_PAGES.includes(page)) {
      pageKey = 'Unknown'
    }
    
    if (!this.stats.counts[pageKey]) {
      this.stats.counts[pageKey] = 0
    }
    
    this.stats.counts[pageKey]++
    this.saveStats()
  }

  scheduleReport() {
    if (this.reportTimer) {
      clearTimeout(this.reportTimer)
    }
    
    this.reportTimer = setTimeout(() => {
      this.report()
      this.scheduleReport()
    }, REPORT_INTERVAL)
  }

  async report() {
    if (this.isReporting) return
    
    this.isReporting = true
    this.stats.pending_report = true
    this.saveStats()
    
    try {
      // 合并失败的请求
      const payloads = this.failedRequests.slice()
      
      // 创建本次上报数据
      const payload = {
        start_time: this.stats.start_time,
        end_time: Date.now(),
        duration: Date.now() - this.stats.start_time,
        counts: { ...this.stats.counts },
        user_agent: navigator.userAgent,
        screen_size: `${window.screen.width}x${window.screen.height}`
      }
      
      payloads.push(payload)
      
      for (let i = 0; i < payloads.length; i++) {
        const success = await this.sendReport(payloads[i])
        
        if (success) {
          // 上报成功，移除该请求
          this.failedRequests.shift()
          this.saveFailedRequests()
        } else {
          // 上报失败，保留在队列中
          break
        }
      }
      
      // 如果全部上报成功，重置统计
      if (this.failedRequests.length === 0) {
        this.stats.start_time = Date.now()
        this.stats.last_report_time = Date.now()
        this.stats.counts = {}
      }
      
      this.stats.pending_report = false
      this.saveStats()
      
    } catch (e) {
      console.error('上报点击统计失败:', e)
      this.stats.pending_report = false
      this.saveStats()
    } finally {
      this.isReporting = false
    }
  }

  async sendReport(payload, retryCount = 0) {
    try {
      const response = await fetch('/api/click/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        keepalive: true
      })
      
      const result = await response.json()
      
      if (response.status >= 500 && retryCount < 3) {
        // 服务器错误，重试
        await this.delay(5000)
        return this.sendReport(payload, retryCount + 1)
      }
      
      return response.status >= 200 && response.status < 400 && result.success
    } catch (e) {
      // 网络错误，保留数据
      console.error('发送请求失败:', e)
      return false
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  async handleBeforeUnload() {
    // 页面关闭前尝试上报
    if (Object.keys(this.stats.counts).length > 0 || this.failedRequests.length > 0) {
      const payload = {
        start_time: this.stats.start_time,
        end_time: Date.now(),
        duration: Date.now() - this.stats.start_time,
        counts: { ...this.stats.counts },
        user_agent: navigator.userAgent,
        screen_size: `${window.screen.width}x${window.screen.height}`
      }
      
      // 使用 keepalive 请求确保页面关闭前发送完成
      try {
        await fetch('/api/click/report', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload),
          keepalive: true
        })
        
        // 如果成功，清空失败队列
        this.failedRequests = []
        this.saveFailedRequests()
      } catch (e) {
        // 保存到失败队列，下次启动时重试
        this.failedRequests.push(payload)
        this.saveFailedRequests()
      }
    }
  }

  loadFailedRequests() {
    try {
      const stored = localStorage.getItem(`${STORAGE_KEY}_failed`)
      if (stored) {
        this.failedRequests = JSON.parse(stored)
      } else {
        this.failedRequests = []
      }
      
      // 如果有失败的请求，尝试立即上报
      if (this.failedRequests.length > 0) {
        setTimeout(() => this.report(), 5000)
      }
    } catch (e) {
      console.error('加载失败请求队列失败:', e)
      this.failedRequests = []
    }
  }

  saveFailedRequests() {
    try {
      localStorage.setItem(`${STORAGE_KEY}_failed`, JSON.stringify(this.failedRequests))
    } catch (e) {
      console.error('保存失败请求队列失败:', e)
    }
  }

  forceReport() {
    return this.report()
  }

  getStats() {
    return { ...this.stats }
  }
}

// 创建单例实例
let instance = null

export function getClickTracker() {
  if (!instance) {
    instance = new ClickTracker()
  }
  return instance
}

export default getClickTracker()