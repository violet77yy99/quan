import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import DefaultLayout from '../layouts/DefaultLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'

import HomeView from '../views/HomeView.vue'
import RecognizeView from '../views/RecognizeView.vue'
import EncyclopediaView from '../views/EncyclopediaView.vue'
import BreedDetailView from '../views/BreedDetailView.vue'
import HistoryView from '../views/HistoryView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import NotFoundView from '../views/NotFoundView.vue'

import AdminDashboardView from '../views/admin/AdminDashboardView.vue'
import AdminUsersView from '../views/admin/AdminUsersView.vue'
import AdminRecordsView from '../views/admin/AdminRecordsView.vue'
import AdminBreedsView from '../views/admin/AdminBreedsView.vue'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      component: DefaultLayout,
      children: [
        { path: '', name: 'home', component: HomeView },
        { path: 'recognize', name: 'recognize', component: RecognizeView },
        { path: 'encyclopedia', name: 'encyclopedia', component: EncyclopediaView },
        { path: 'breed/:slug', name: 'breed-detail', component: BreedDetailView },
        {
          path: 'history',
          name: 'history',
          component: HistoryView,
          meta: { requiresAuth: true }
        },
        { path: 'login', name: 'login', component: LoginView },
        { path: 'register', name: 'register', component: RegisterView }
      ]
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAdmin: true },
      children: [
        { path: '', name: 'admin-dashboard', component: AdminDashboardView },
        { path: 'users', name: 'admin-users', component: AdminUsersView },
        { path: 'records', name: 'admin-records', component: AdminRecordsView },
        { path: 'breeds', name: 'admin-breeds', component: AdminBreedsView }
      ]
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.token && !auth.user) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'home' }
  }

  if ((to.name === 'login' || to.name === 'register') && auth.isLoggedIn) {
    return { name: 'home' }
  }

  return true
})

export default router