<template>
  <div class="todo-view">
    <Toast ref="toastRef" />
    
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold" style="color: var(--text-primary);">待办事项</h2>
      <div class="flex gap-3">
        <button 
          @click="toggleCalendarMode"
          style="padding: 8px 16px; border-radius: 8px; transition: all 0.2s ease; border: none; cursor: pointer; background-color: var(--bg-surface); color: var(--text-secondary);"
          @mouseenter="($event.target.style.backgroundColor = 'var(--border)')"
          @mouseleave="($event.target.style.backgroundColor = 'var(--bg-surface)')"
        >
          {{ isCalendarMode ? '← 返回列表' : '📅 切换日历模式' }}
        </button>
        <button 
          @click="showForm = true"
          style="background-color: var(--primary); color: white; padding: 8px 16px; border-radius: 8px; transition: background-color 0.2s ease;"
          @mouseenter="($event.target.style.backgroundColor = 'var(--primary-hover)')"
          @mouseleave="($event.target.style.backgroundColor = 'var(--primary)')"
        >
          + 新建待办
        </button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div style="background-color: var(--bg-card); padding: 16px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="font-size: 14px; color: var(--text-secondary);">总数</div>
        <div style="font-size: 24px; font-weight: bold; color: var(--text-primary);">{{ stats.total }}</div>
      </div>
      <div style="background-color: var(--bg-card); padding: 16px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="font-size: 14px; color: var(--text-secondary);">完成</div>
        <div style="font-size: 24px; font-weight: bold; color: #10b981;">{{ stats.completed }}</div>
      </div>
      <div style="background-color: var(--bg-card); padding: 16px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="font-size: 14px; color: var(--text-secondary);">进行中</div>
        <div style="font-size: 24px; font-weight: bold; color: #f59e0b;">{{ stats.pending }}</div>
      </div>
      <div style="background-color: var(--bg-card); padding: 16px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="font-size: 14px; color: var(--text-secondary);">已超时</div>
        <div style="font-size: 24px; font-weight: bold; color: #ef4444;">{{ stats.overdue }}</div>
      </div>
    </div>

    <!-- 日历模式（已替换为新版设计） -->
    <div v-if="isCalendarMode" class="calendar-mode-container">
      <!-- 日历 -->
      <div class="calendar-container">
        <div class="calendar-header">
          <button class="nav-btn" @click="prevMonth">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
          </button>
          
          <div class="title-group">
            <h2 class="month-title">{{ currentMonthName }}</h2>
          </div>

          <div class="header-actions">
            <button class="today-btn" @click="goToToday">今天</button>
            <button class="nav-btn" @click="nextMonth">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
            </button>
          </div>
        </div>

        <div class="weekdays-row">
          <div v-for="day in weekDays" :key="day" class="weekday-cell">
            {{ day }}
          </div>
        </div>

        <div class="days-grid">
          <div
            v-for="(day, index) in calendarDays"
            :key="index"
            class="day-cell"
            :class="{
              'is-today': day.isToday,
              'is-current-month': day.isCurrentMonth,
              'is-other-month': !day.isCurrentMonth,
              'has-events': day.pendingCount > 0,
              'is-selected': selectedDate && selectedDate.toDateString() === day.date.toDateString()
            }"
            @click="day.isCurrentMonth && selectDate(day.date)"
          >
            <span class="day-number">{{ day.date.getDate() }}</span>
            
            <div v-if="day.pendingCount > 0" class="event-dots">
              <span 
                v-for="n in Math.min(day.pendingCount, 3)" 
                :key="n" 
                class="event-dot"
                :class="getPriorityClass(day.date, n - 1)"
              ></span>
              <span v-if="day.pendingCount > 3" class="event-more">+</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 待办预览区域 -->
      <div class="todo-preview-container">
        <div class="preview-header">
          <h3 class="preview-title">当日待办预览</h3>
          <div v-if="selectedDate" class="preview-date">
            {{ formatPreviewDate(selectedDate) }}
          </div>
        </div>
        
        <div class="preview-content">
          <div v-if="!selectedDate" class="empty-state">
            <div class="empty-icon">📅</div>
            <p>单击一个日期以预览当日即将结束的待办事项</p>
          </div>
          
          <div v-else-if="selectedDateTodos.length === 0" class="empty-state">
            <div class="empty-icon">✅</div>
            <p>当日暂无待办事项</p>
          </div>
          
          <div v-else class="todo-list">
            <div 
              v-for="todo in selectedDateTodos" 
              :key="todo.id"
              class="todo-item"
              :class="{ completed: todo.completed }"
            >
              <div class="todo-priority" :class="getPriorityClassForTodo(todo.priority)"></div>
              <div class="todo-info">
                <span class="todo-content">{{ todo.content }}</span>
                <span class="todo-deadline">{{ formatTime(todo.deadline) }}</span>
              </div>
              <div class="todo-status">
                <span v-if="todo.completed" class="status-badge completed">已完成</span>
                <span v-else-if="isOverdue(todo)" class="status-badge overdue">已过期</span>
                <span v-else class="status-badge pending">进行中</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表模式 -->
    <div v-else>
      <!-- 筛选 -->
      <div class="flex gap-2 mb-4">
        <button 
          @click="filter = 'all'"
          :style="{
            padding: '4px 12px',
            borderRadius: '4px',
            transition: 'all 0.2s ease',
            backgroundColor: filter === 'all' ? 'var(--primary)' : 'var(--bg-surface)',
            color: filter === 'all' ? 'white' : 'var(--text-secondary)',
            border: 'none',
            cursor: 'pointer'
          }"
          @mouseenter="($event.target.style.backgroundColor = filter !== 'all' ? 'var(--border)' : $event.target.style.backgroundColor)"
          @mouseleave="($event.target.style.backgroundColor = filter === 'all' ? 'var(--primary)' : 'var(--bg-surface)')"
        >全部</button>
        <button 
          @click="filter = 'pending'"
          :style="{
            padding: '4px 12px',
            borderRadius: '4px',
            transition: 'all 0.2s ease',
            backgroundColor: filter === 'pending' ? 'var(--primary)' : 'var(--bg-surface)',
            color: filter === 'pending' ? 'white' : 'var(--text-secondary)',
            border: 'none',
            cursor: 'pointer'
          }"
          @mouseenter="($event.target.style.backgroundColor = filter !== 'pending' ? 'var(--border)' : $event.target.style.backgroundColor)"
          @mouseleave="($event.target.style.backgroundColor = filter === 'pending' ? 'var(--primary)' : 'var(--bg-surface)')"
        >进行中</button>
        <button 
          @click="filter = 'completed'"
          :style="{
            padding: '4px 12px',
            borderRadius: '4px',
            transition: 'all 0.2s ease',
            backgroundColor: filter === 'completed' ? 'var(--primary)' : 'var(--bg-surface)',
            color: filter === 'completed' ? 'white' : 'var(--text-secondary)',
            border: 'none',
            cursor: 'pointer'
          }"
          @mouseenter="($event.target.style.backgroundColor = filter !== 'completed' ? 'var(--border)' : $event.target.style.backgroundColor)"
          @mouseleave="($event.target.style.backgroundColor = filter === 'completed' ? 'var(--primary)' : 'var(--bg-surface)')"
        >已完成</button>
      </div>

      <!-- 待办列表 -->
      <div class="space-y-3">
        <div 
          v-for="todo in filteredTodos" 
          :key="todo.id"
          :style="{
            backgroundColor: 'var(--bg-card)',
            padding: '16px',
            borderRadius: '8px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            transition: 'all 0.3s ease',
            opacity: todo.completed ? 0.6 : 1,
            borderLeft: isOverdue(todo) && !todo.completed ? '4px solid #ef4444' : '4px solid transparent'
          }"
        >
          <div class="flex items-start gap-4">
            <button 
              @click="toggleComplete(todo)"
              :style="{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                border: '2px solid',
                borderColor: todo.completed ? '#10b981' : 'var(--border)',
                backgroundColor: todo.completed ? '#10b981' : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
                cursor: 'pointer'
              }"
              @mouseenter="($event.target.style.borderColor = todo.completed ? '#10b981' : '#10b981')"
              @mouseleave="($event.target.style.borderColor = todo.completed ? '#10b981' : 'var(--border)')"
              :title="todo.completed ? '点击恢复待办' : '点击标记完成'"
            >
              <span v-if="todo.completed" style="color: white; font-size: 12px;">✓</span>
            </button>
            <div class="flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span 
                  :style="{
                    padding: '2px 8px',
                    fontSize: '12px',
                    borderRadius: '4px',
                    backgroundColor: todo.priority === 3 ? '#fef2f2' : (todo.priority === 2 ? '#fefce8' : '#eff6ff'),
                    color: todo.priority === 3 ? '#dc2626' : (todo.priority === 2 ? '#ca8a04' : '#2563eb')
                  }"
                >
                  {{ priorityLabel(todo.priority) }}
                </span>
                <span :style="{ textDecoration: todo.completed ? 'line-through' : 'none', color: 'var(--text-primary)' }">{{ todo.content }}</span>
                <span v-if="isOverdue(todo) && !todo.completed" style="font-size: 12px; color: #ef4444;">已过期</span>
              </div>
              <div style="font-size: 14px; color: var(--text-secondary); margin-top: 4px;">
                截止: {{ formatDate(todo.deadline) }}
                <span v-if="todo.completed_at" style="margin-left: 8px;">完成于: {{ formatDate(todo.completed_at) }}</span>
              </div>
            </div>
            <div class="flex gap-2">
              <button 
                v-if="!todo.completed" 
                @click="editTodo(todo)" 
                style="color: var(--primary); cursor: pointer; transition: color 0.2s ease;"
                @mouseenter="($event.target.style.color = 'var(--primary-hover)')"
                @mouseleave="($event.target.style.color = 'var(--primary)')"
                title="编辑"
              >
                ✏️
              </button>
              <button 
                @click="deleteTodo(todo.id)" 
                style="color: #ef4444; cursor: pointer; transition: color 0.2s ease;"
                @mouseenter="($event.target.style.color = '#dc2626')"
                @mouseleave="($event.target.style.color = '#ef4444')"
                title="删除"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建/编辑待办表单 -->
    <Transition name="modal">
      <div v-if="showForm" style="position: fixed; inset: 0; background-color: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 50;">
        <div style="background-color: var(--bg-card); padding: 24px; border-radius: 8px; width: 100%; max-width: 400px; transform: scale(1);">
          <h3 style="font-size: 20px; font-weight: bold; color: var(--text-primary); margin-bottom: 16px;">{{ isEditing ? '编辑待办' : '新建待办' }}</h3>
          <div style="display: flex; flex-direction: column; gap: 16px;">
            <div>
              <label style="display: block; font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-bottom: 4px;">内容</label>
              <input 
                v-model="formData.content" 
                type="text" 
                style="width: 100%; border: 1px solid var(--border); border-radius: 4px; padding: 8px 12px; background-color: var(--bg-surface); color: var(--text-primary);"
                placeholder="请输入待办内容" 
              />
            </div>
            <div>
              <label style="display: block; font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-bottom: 4px;">优先级</label>
              <select 
                v-model="formData.priority" 
                style="width: 100%; border: 1px solid var(--border); border-radius: 4px; padding: 8px 12px; background-color: var(--bg-surface); color: var(--text-primary);"
              >
                <option :value="3">高</option>
                <option :value="2">中</option>
                <option :value="1">低</option>
              </select>
            </div>
            <div>
              <label style="display: block; font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-bottom: 4px;">截止时间</label>
              <input 
                v-model="formData.deadline" 
                type="datetime-local" 
                style="width: 100%; border: 1px solid var(--border); border-radius: 4px; padding: 8px 12px; background-color: var(--bg-surface); color: var(--text-primary);"
              />
            </div>
          </div>
          <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 24px;">
            <button 
              @click="cancelForm" 
              style="padding: 8px 16px; border: 1px solid var(--border); border-radius: 4px; background-color: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.2s ease;"
              @mouseenter="($event.target.style.backgroundColor = 'var(--bg-surface)')"
              @mouseleave="($event.target.style.backgroundColor = 'transparent')"
            >取消</button>
            <button 
              @click="saveTodo" 
              style="padding: 8px 16px; border-radius: 4px; background-color: var(--primary); color: white; border: none; cursor: pointer; transition: background-color 0.2s ease;"
              @mouseenter="($event.target.style.backgroundColor = 'var(--primary-hover)')"
              @mouseleave="($event.target.style.backgroundColor = 'var(--primary)')"
            >保存</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { todoApi } from '../api'
import Toast from '../components/Toast.vue'

const toastRef = ref(null)
const todos = ref([])
const stats = ref({ total: 0, completed: 0, pending: 0, overdue: 0 })
const filter = ref('all')
const showForm = ref(false)
const isEditing = ref(false)
const isCalendarMode = ref(false)
const currentDate = ref(new Date())
const selectedDate = ref(null)
const formData = ref({
  id: null,
  content: '',
  priority: 2,
  deadline: ''
})

const filteredTodos = computed(() => {
  if (filter.value === 'pending') {
    return todos.value.filter(t => !t.completed)
  } else if (filter.value === 'completed') {
    return todos.value.filter(t => t.completed)
  }
  return todos.value
})

async function loadTodos() {
  const res = await todoApi.getTodos()
  todos.value = res.data
}

async function loadStats() {
  const res = await todoApi.getStats()
  stats.value = res.data
}

async function createTodo() {
  await todoApi.createTodo(formData.value)
  cancelForm()
  await loadTodos()
  await loadStats()
  showToastMessage('待办创建成功', 'success')
}

async function updateTodo() {
  await todoApi.updateTodo(formData.value.id, formData.value)
  cancelForm()
  await loadTodos()
  await loadStats()
  showToastMessage('待办更新成功', 'success')
}

async function saveTodo() {
  if (!formData.value.content.trim()) {
    showToastMessage('请输入待办内容', 'warning')
    return
  }
  if (!formData.value.deadline) {
    showToastMessage('请设置截止时间', 'warning')
    return
  }
  
  if (isEditing.value) {
    await updateTodo()
  } else {
    await createTodo()
  }
}

async function toggleComplete(todo) {
  if (todo.completed) {
    const now = new Date()
    const deadline = new Date(todo.deadline)
    let confirmMessage = '确定要恢复该待办事项吗？'
    
    if (deadline < now) {
      confirmMessage = '该待办已过期，确定要恢复吗？建议新建一个待办事项。'
    }
    
    const confirmed = await toastRef.value.confirm(confirmMessage)
    if (!confirmed) {
      return
    }
  }
  
  try {
    await todoApi.toggleTodo(todo.id)
    await loadTodos()
    await loadStats()
    
    if (todo.completed) {
      showToastMessage('待办已恢复', 'info')
    } else {
      showToastMessage('待办已完成', 'success')
    }
  } catch (error) {
    showToastMessage('操作失败', 'error')
    console.error('切换状态失败:', error)
  }
}

async function deleteTodo(id) {
  const confirmed = await toastRef.value.confirm('确定要删除该待办吗？')
  if (!confirmed) {
    return
  }
  
  try {
    await todoApi.deleteTodo(id)
    await loadTodos()
    await loadStats()
    showToastMessage('待办已删除', 'info')
  } catch (error) {
    showToastMessage('删除失败', 'error')
    console.error('删除失败:', error)
  }
}

function editTodo(todo) {
  isEditing.value = true
  formData.value = {
    id: todo.id,
    content: todo.content,
    priority: todo.priority,
    deadline: formatDatetimeLocal(todo.deadline)
  }
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  isEditing.value = false
  formData.value = {
    id: null,
    content: '',
    priority: 2,
    deadline: ''
  }
}

function showToastMessage(message, type = 'info') {
  if (toastRef.value) {
    toastRef.value.showToast(message, { type, duration: 3000 })
  }
}

function priorityLabel(priority) {
  return { 3: '高', 2: '中', 1: '低' }[priority]
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function formatDatetimeLocal(dateStr) {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

function isOverdue(todo) {
  const now = new Date()
  const deadline = new Date(todo.deadline)
  return deadline < now && !todo.completed
}

function toggleCalendarMode() {
  isCalendarMode.value = !isCalendarMode.value
  selectedDate.value = null
}

function selectDate(date) {
  if (selectedDate.value && selectedDate.value.toDateString() === date.toDateString()) {
    selectedDate.value = null
  } else {
    selectedDate.value = date
  }
}

const selectedDateTodos = computed(() => {
  if (!selectedDate.value) return []
  return getTodosForDate(selectedDate.value)
})

function getPriorityClass(date, index) {
  const dateTodos = getTodosForDate(date).filter(t => !t.completed)
  if (index >= dateTodos.length) return 'priority-low'
  const priority = dateTodos[index].priority
  return getPriorityClassForTodo(priority)
}

function getPriorityClassForTodo(priority) {
  switch (priority) {
    case 3: return 'priority-high'
    case 2: return 'priority-medium'
    case 1: return 'priority-low'
    default: return 'priority-low'
  }
}

function formatPreviewDate(date) {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const weekDay = weekDays[date.getDay()]
  return `${year}年${month}月${day}日 ${weekDay}`
}

function formatTime(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function getTodosForDate(date) {
  const dateStr = date.toISOString().split('T')[0]
  return todos.value.filter(todo => {
    const todoDate = new Date(todo.deadline).toISOString().split('T')[0]
    return todoDate === dateStr
  })
}

function getTodosCountForDate(date) {
  return getTodosForDate(date).length
}

function getPendingTodosCountForDate(date) {
  return getTodosForDate(date).filter(t => !t.completed).length
}

function prevMonth() {
  const date = new Date(currentDate.value)
  date.setMonth(date.getMonth() - 1)
  currentDate.value = date
}

function nextMonth() {
  const date = new Date(currentDate.value)
  date.setMonth(date.getMonth() + 1)
  currentDate.value = date
}

function goToToday() {
  currentDate.value = new Date()
}

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  
  const days = []
  
  const startDay = firstDay.getDay()
  for (let i = startDay - 1; i >= 0; i--) {
    const date = new Date(year, month, -i)
    days.push({
      date,
      isCurrentMonth: false,
      isToday: false,
      isSelected: false,
      todoCount: getTodosCountForDate(date),
      pendingCount: getPendingTodosCountForDate(date)
    })
  }
  
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const date = new Date(year, month, i)
    const today = new Date()
    days.push({
      date,
      isCurrentMonth: true,
      isToday: date.toDateString() === today.toDateString(),
      isSelected: false,
      todoCount: getTodosCountForDate(date),
      pendingCount: getPendingTodosCountForDate(date)
    })
  }
  
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    const date = new Date(year, month + 1, i)
    days.push({
      date,
      isCurrentMonth: false,
      isToday: false,
      isSelected: false,
      todoCount: getTodosCountForDate(date),
      pendingCount: getPendingTodosCountForDate(date)
    })
  }
  
  return days
})

const currentMonthName = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  const months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
  return `${year}年${months[month]}`
})

const weekDays = ['日', '一', '二', '三', '四', '五', '六']

onMounted(() => {
  loadTodos()
  loadStats()
})
</script>

<style scoped>
/* ===== 日历样式（新增） ===== */
.calendar-container {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 28px;
  box-shadow: 
    0 1px 2px rgba(0,0,0,0.04),
    0 4px 24px rgba(0,0,0,0.06);
  border: 1px solid var(--border, rgba(0,0,0,0.04));
  width: 100%;
  max-width: 420px;
  margin: 0 auto;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 0 4px;
}

.title-group {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.month-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.nav-btn:hover {
  background: var(--bg-surface);
  color: var(--text-primary);
  transform: scale(1.05);
}

.nav-btn:active {
  transform: scale(0.95);
}

.today-btn {
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--border, rgba(0,0,0,0.08));
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.today-btn:hover {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(var(--primary-rgb, 59, 130, 246), 0.3);
}

.weekdays-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border, rgba(0,0,0,0.06));
}

.weekday-cell {
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  opacity: 0.6;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 8px 0;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}

.day-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  cursor: pointer;
  position: relative;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
}

/* 当月日期 */
.day-cell.is-current-month {
  color: var(--text-primary);
  background: transparent;
}

.day-cell.is-current-month:hover {
  background: var(--bg-surface);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}

/* 非当月日期 */
.day-cell.is-other-month {
  color: var(--text-secondary);
  opacity: 0.35;
  cursor: default;
}

.day-cell.is-other-month:hover {
  opacity: 0.5;
}

/* 今天 - 圆形高亮 */
.day-cell.is-today .day-number {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  font-weight: 700;
  box-shadow: 0 2px 10px rgba(var(--primary-rgb, 59, 130, 246), 0.35);
}

/* 数字 */
.day-number {
  font-size: 15px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  z-index: 1;
}

/* 事件指示器 */
.event-dots {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-top: 5px;
  height: 5px;
}

.event-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.event-dot.priority-high {
  background: #ef4444;
  box-shadow: 0 0 4px rgba(239, 68, 68, 0.4);
}

.event-dot.priority-medium {
  background: #eab308;
  box-shadow: 0 0 4px rgba(234, 179, 8, 0.4);
}

.event-dot.priority-low {
  background: #22c55e;
  box-shadow: 0 0 4px rgba(34, 197, 94, 0.4);
}

.event-more {
  font-size: 9px;
  font-weight: 700;
  color: var(--text-secondary);
  margin-left: 1px;
  line-height: 1;
}

/* 按下反馈 */
.day-cell.is-current-month:active {
  transform: scale(0.92);
}

/* 深色模式微调 */
@media (prefers-color-scheme: dark) {
  .calendar-container {
    box-shadow: 
      0 1px 2px rgba(0,0,0,0.2),
      0 4px 24px rgba(0,0,0,0.3);
  }
  
  .today-btn {
    border-color: rgba(255,255,255,0.08);
  }
  
  .day-cell.is-current-month:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  }
}

/* 选中状态 */
.day-cell.is-selected {
  background: var(--primary);
  color: white;
}

.day-cell.is-selected .day-number {
  font-weight: 700;
}

.day-cell.is-selected .event-dot {
  background: white !important;
  box-shadow: none !important;
}

/* 日历模式容器 */
.calendar-mode-container {
  display: flex;
  gap: 24px;
  justify-content: flex-end;
}

.calendar-mode-container .calendar-container {
  margin: 0;
  max-width: 420px;
}

/* 待办预览区域 */
.todo-preview-container {
  background: var(--bg-card);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 
    0 1px 2px rgba(0,0,0,0.04),
    0 4px 24px rgba(0,0,0,0.06);
  border: 1px solid var(--border, rgba(0,0,0,0.04));
  width: 320px;
  flex-shrink: 0;
  max-height: 500px;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.preview-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.preview-date {
  font-size: 13px;
  color: var(--text-secondary);
}

.preview-content {
  flex: 1;
  overflow-y: auto;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

/* 待办列表 */
.todo-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--bg-surface);
  border-radius: 12px;
  transition: all 0.2s ease;
}

.todo-item:hover {
  background: var(--border);
}

.todo-item.completed {
  opacity: 0.6;
}

.todo-priority {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.todo-priority.priority-high { background: #ef4444; }
.todo-priority.priority-medium { background: #eab308; }
.todo-priority.priority-low { background: #22c55e; }

.todo-info {
  flex: 1;
  min-width: 0;
}

.todo-content {
  display: block;
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-deadline {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.todo-status {
  flex-shrink: 0;
}

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 12px;
}

.status-badge.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-badge.pending {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.status-badge.overdue {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

/* 响应式 */
@media (max-width: 900px) {
  .calendar-mode-container {
    flex-direction: column;
    align-items: center;
  }
  
  .todo-preview-container {
    width: 100%;
    max-width: 420px;
  }
}

@media (max-width: 640px) {
  .calendar-container {
    padding: 20px 16px;
    border-radius: 16px;
  }
  
  .month-title {
    font-size: 18px;
  }
  
  .day-cell.is-today .day-number {
    width: 32px;
    height: 32px;
  }
  
  .day-number {
    font-size: 14px;
  }
  
  .todo-preview-container {
    padding: 16px;
  }
}

/* ===== 原有弹窗动画（保留） ===== */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white {
  transform: scale(0.95);
}

.modal-leave-to .bg-white {
  transform: scale(0.95);
}
</style>