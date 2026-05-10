import { createRouter, createWebHashHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import Users from '@/views/Users.vue'
import Records from '@/views/Records.vue'

import Analysis from '@/views/Analysis.vue'
import Sessions from '@/views/Sessions.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'login', component: Login },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    children: [
      { path: 'dashboard', name: 'dashboard', component: Dashboard },
      { path: 'users', name: 'users', component: Users },
      { path: 'records', name: 'records', component: Records },
      { path: 'analysis', name: 'analysis', component: Analysis },
      { path: 'sessions', name: 'sessions', component: Sessions },
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('admin_token')
  if (to.name !== 'login' && !token) {
    next('/login')
  } else if (to.name === 'login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
