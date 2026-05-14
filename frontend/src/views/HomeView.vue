<template>
  <div class="home-container">
    <LogoAnimation v-if="showAnimation" @animation-complete="onAnimationComplete" />
    <div v-if="!showAnimation" class="typewriter-wrapper">
      <p class="quote-text">
        <span v-for="(char, index) in displayedText" :key="index">
          {{ char }}
        </span>
        <span class="cursor">|</span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import LogoAnimation from '../components/LogoAnimation.vue'

const hitokoto = ref('')
const author = ref('')
const displayedText = ref([])
const typingSpeed = ref(80)
const deletingSpeed = ref(40)
const showAnimation = ref(false)
let timer = null

async function fetchHitokoto() {
  try {
    const response = await fetch('https://v1.hitokoto.cn')
    const data = await response.json()
    hitokoto.value = data.hitokoto || '生活不止眼前的苟且，还有诗和远方。'
    author.value = data.from_who || ''
  } catch (error) {
    console.error('获取名言失败:', error)
    hitokoto.value = '生活不止眼前的苟且，还有诗和远方。'
    author.value = ''
  }
}

async function typeText(text) {
  displayedText.value = []
  for (let i = 0; i < text.length; i++) {
    displayedText.value.push(text[i])
    await new Promise(resolve => setTimeout(resolve, typingSpeed.value))
  }
}

async function deleteText() {
  while (displayedText.value.length > 0) {
    displayedText.value.pop()
    await new Promise(resolve => setTimeout(resolve, deletingSpeed.value))
  }
}

async function runCycle() {
  await fetchHitokoto()
  await typeText(hitokoto.value)
  await delay(2000)
  await deleteText()
  if (author.value) {
    await typeText(`出自 ${author.value}`)
    await delay(3000)
    await deleteText()
  }
  await delay(1000)
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function startAutoRefresh() {
  while (true) {
    await runCycle()
  }
}

function onAnimationComplete() {
  showAnimation.value = false
  timer = setTimeout(startAutoRefresh, 100)
}

onMounted(() => {
  showAnimation.value = true
})

onUnmounted(() => {
  if (timer) {
    clearTimeout(timer)
  }
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: transparent;
}

.typewriter-wrapper {
  max-width: 900px;
  padding: 40px 60px;
  text-align: center;
}

.quote-text {
  font-size: 36px;
  font-weight: 300;
  color: var(--text-primary);
  line-height: 1.6;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.cursor {
  animation: blink 1s infinite;
  color: var(--text-primary);
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@media (max-width: 768px) {
  .typewriter-wrapper {
    padding: 30px 20px;
  }

  .quote-text {
    font-size: 24px;
  }
}
</style>
