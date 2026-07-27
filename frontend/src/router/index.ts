import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('~/pages/LoginPage.vue'),
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('~/pages/RegisterPage.vue'),
    },
    {
      path: '/',
      name: 'Home',
      component: () => import('~/pages/HomePage.vue'),
    },
    {
      path: '/article/:idOrSlug',
      name: 'Article',
      component: () => import('~/pages/ArticlePage.vue'),
    },
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('~/pages/AdminPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/search',
      name: 'Search',
      component: () => import('~/pages/SearchPage.vue'),
    },
  ],
})

// 路由守卫：未登录跳转 /login
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
