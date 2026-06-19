import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/auth', name: 'auth', component: () => import('@/views/AuthView.vue') },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/projects' },
      { path: 'projects', name: 'projects', component: () => import('@/views/ProjectsView.vue') },
      { path: 'projects/:id', name: 'project-detail', component: () => import('@/views/ProjectDetailView.vue') },
      { path: 'projects/:id/materials', name: 'materials', component: () => import('@/views/MaterialsView.vue') },
      { path: 'projects/:id/questions', name: 'questions', component: () => import('@/views/QuestionsView.vue') },
      { path: 'projects/:id/interview', name: 'interview', component: () => import('@/views/InterviewView.vue') },
      { path: 'knowledge', name: 'knowledge', component: () => import('@/views/KnowledgeView.vue') },
      { path: 'question-bank', name: 'question-bank', component: () => import('@/views/QuestionBankView.vue') },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthed) {
    return { name: 'auth', query: { redirect: to.fullPath } }
  }
  if (to.name === 'auth' && auth.isAuthed) {
    return { name: 'projects' }
  }
})

export default router
