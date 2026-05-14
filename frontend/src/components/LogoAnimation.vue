<template>
  <div class="logo-animation" :class="{ 'animation-done': isDone }" ref="rootRef">
    <div class="logo-container">
      <div class="letters-wrapper">
        <div class="letters">
          <div
            class="letter-group"
            v-for="(item, index) in letterData"
            :key="item.letter"
          >
            <span
              class="single-letter"
              :style="{ '--letter-color': item.color }"
            >
              {{ item.letter }}
            </span>
            <span
              class="word-part"
              :style="{ '--word-color': item.color }"
            >
              <span
                v-for="(char, charIndex) in item.word.split('')"
                :key="charIndex"
                class="word-char"
              >
                {{ char }}
              </span>
            </span>
          </div>
        </div>
      </div>
      <div class="chinese-logo">
        <span
          v-for="(char, index) in chineseChars"
          :key="index"
          class="chinese-char"
        >
          {{ char }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { createTimeline, stagger, utils, cubicBezier } from 'animejs'

const emit = defineEmits(['animationComplete'])
const isDone = ref(false)
const rootRef = ref(null)

const letterData = [
  { letter: 'A', word: 'utonomous', color: '#ef4444', spacing: 265 },
  { letter: 'S', word: 'implified', color: '#22c55e', spacing: 205 },
  { letter: 'M', word: 'acro',      color: '#3b82f6', spacing: 105 },
  { letter: 'R', word: 'untime',    color: '#a855f7', spacing: 150 }
]

const chineseChars = ['自', '简', '宏', '枢']

onMounted(() => {
  // 精确还原你原来的两条 cubic-bezier 曲线
  const easeFloat  = cubicBezier(0.16, 1, 0.3, 1)   // 字母/字符浮现
  const easeSpread = cubicBezier(0.22, 1, 0.36, 1)  // 先快后慢展开

  // 设置初始状态（替代 CSS @keyframes 的 0%）
  utils.set('.single-letter', {
    opacity: 0, y: 40, scale: 0.9, filter: 'blur(10px)'
  })
  utils.set('.letter-group', { marginRight: 0 })
  utils.set('.word-char', {
    opacity: 0, y: 12, filter: 'blur(8px)'
  })
  utils.set('.chinese-char', {
    opacity: 0, y: 20, filter: 'blur(6px)'
  })

  const tl = createTimeline()

  // 1. 大写字母依次砸下来（0ms 开始，互相错开 150ms）
  tl.add('.single-letter', {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: 'blur(0px)',
    duration: 1000,
    ease: easeFloat,
    delay: stagger(150)
  })

  // 2. 字母组先快后慢展开（800ms 处切入，持续 1200ms）
  tl.add('.letter-group', {
    marginRight: (el, i) => letterData[i].spacing,
    duration: 1600,
    ease: easeSpread
  }, 1200)

  // 3. 四个单词同时展开，组内字符依次浮现（2000ms 处切入）
  letterData.forEach((_, i) => {
    tl.add(`.letter-group:nth-child(${i + 1}) .word-char`, {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      duration: 1200,
      ease: easeFloat,
      delay: stagger(50)   // 只在该单词内部错开
    }, 2000)
  })

  // 4. 中文依次浮现（3500ms 处切入）
  tl.add('.chinese-char', {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    duration: 1200,
    ease: easeFloat,
    delay: stagger(150)
  }, 3300)

  // 5. 收尾状态（保留 setTimeout 与 CSS transition 配合）
  setTimeout(() => { isDone.value = true }, 6000)
  setTimeout(() => { emit('animationComplete') }, 7500)
})
</script>

<style scoped>
/* 所有 @keyframes 和 animation 已移除，纯样式定义 */
.logo-animation {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--bg-page);
  z-index: 9999;
  opacity: 1;
  transition: opacity 1s ease-out;
  pointer-events: none;
}
.logo-animation.animation-done {
  opacity: 0;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
}

.letters-wrapper {
  display: flex;
  justify-content: center;
}

.letters {
  display: flex;
  align-items: center;
}

.letter-group {
  display: flex;
  align-items: flex-end;
  position: relative;
  flex-shrink: 0;
  margin-right: 0px;
}

.single-letter {
  font-size: 80px;
  font-weight: 700;
  color: var(--letter-color);
  display: inline-block;
  will-change: transform, opacity, filter;
}

.word-part {
  font-size: 48px;
  font-weight: 600;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  white-space: nowrap;
  position: absolute;
  left: 100%;
  bottom: 0.25em;
  transform: none;
  padding-left: 2px;
}

.word-char {
  display: inline-block;
  will-change: transform, opacity, filter;
}

.chinese-logo {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.chinese-char {
  font-size: 36px;
  font-weight: 600;
  color: var(--text-secondary);
  will-change: transform, opacity, filter;
}

@media (max-width: 768px) {
  .single-letter { font-size: 48px; }
  .word-part { font-size: 28px; }
  .chinese-char { font-size: 24px; }
}

@media (max-width: 480px) {
  .single-letter { font-size: 36px; }
  .word-part { font-size: 22px; }
  .chinese-char { font-size: 20px; }
}
</style>