import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/history' },
  { path: '/history', component: () => import('./views/History.vue') },
  { path: '/workspace/:id', component: () => import('./views/Workspace.vue'), props: true },
  { path: '/glossary', component: () => import('./views/Glossary.vue') },
  { path: '/settings', component: () => import('./views/Settings.vue') },
  { path: '/diff', component: () => import('./views/Diff.vue') }
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes
})
