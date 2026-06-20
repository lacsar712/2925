import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      component: () => import('../components/layout/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
        { path: 'market', name: 'Market', component: () => import('../views/MarketView.vue') },
        { path: 'market/:id', name: 'BondDetail', component: () => import('../views/BondDetail.vue') },
        { path: 'trades', name: 'Trades', component: () => import('../views/TradesView.vue') },
        { path: 'futures', name: 'Futures', component: () => import('../views/FuturesView.vue') },
        { path: 'swaps', name: 'Swaps', component: () => import('../views/SwapsView.vue') },
        { path: 'favorites', name: 'Favorites', component: () => import('../views/FavoritesView.vue') },
        { path: 'admin/users', name: 'AdminUsers', component: () => import('../views/admin/UserManagement.vue') },
        { path: 'admin/sources', name: 'AdminSources', component: () => import('../views/admin/SourceManagement.vue') },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth !== false && !authStore.token) {
    next('/login')
  } else {
    next()
  }
})

export default router
