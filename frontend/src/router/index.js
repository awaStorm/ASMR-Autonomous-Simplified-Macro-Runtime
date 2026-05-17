import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue')
  },
  {
    path: '/todo',
    name: 'todo',
    component: () => import('../views/TodoView.vue')
  },
  {
    path: '/image',
    name: 'image',
    component: () => import('../views/ImageView.vue')
  },
  {
    path: '/bili',
    name: 'bili',
    component: () => import('../views/BiliView.vue')
  },
  {
    path: '/jm',
    name: 'jm',
    component: () => import('../views/JmView.vue')
  },
  {
    path: '/miao',
    name: 'miao',
    component: () => import('../views/MiaoView.vue')
  },
  {
    path: '/setting',
    name: 'setting',
    component: () => import('../views/SettingView.vue')
  },
  // 404 页面 - 必须放在最后
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    component: () => import('../views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
