<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <div class="error-message">页面走丢了</div>
      <div class="error-desc">您访问的页面不存在或已被移动</div>
      <button @click="goHome" class="home-button">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 10 01-1-1v-4a1 10 001-1 1m-4 8a4 40 018 0v-4a4 40 00-8 0v4z"/>
        </svg>
        返回首页
      </button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-page) 0%, var(--bg-card) 100%);
}

.not-found-content {
  text-align: center;
  padding: 40px;
  background: var(--bg-card);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
}

.error-code {
  font-size: 8rem;
  font-weight: bold;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  animation: float 3s ease-in-out infinite;
}

.error-message {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.error-desc {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 30px;
}

.home-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 32px;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.home-button:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}
</style>
