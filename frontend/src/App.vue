<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header 56px -->
    <header class="h-14 shrink-0 bg-white border-b border-gray-200 flex items-center px-4 gap-4">
      <div class="font-semibold text-gray-800">涉外法务翻译与合规风控</div>
      <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
        本地内存处理
      </span>
      <nav class="ml-auto flex items-center gap-1 text-sm">
        <RouterLink to="/history" class="nav-link">历史</RouterLink>
        <RouterLink to="/glossary" class="nav-link">术语</RouterLink>
        <RouterLink to="/diff" class="nav-link">版本比对</RouterLink>
        <RouterLink to="/settings" class="nav-link">设置</RouterLink>
      </nav>
    </header>

    <main class="flex-1 min-h-0 overflow-hidden">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.nav-link {
  @apply px-3 py-1.5 rounded hover:bg-gray-100 text-gray-600;
}
.nav-link.router-link-active {
  @apply bg-brand-50 text-brand-700;
}
</style>
