<template>
  <el-container class="shell">
    <el-aside class="sidebar" width="248px">
      <div class="brand">
        <div class="brand-mark">P</div>
        <div>
          <strong>PyOffer Agent</strong>
          <span>面试训练工作台</span>
        </div>
      </div>

      <el-menu :default-active="activePath" router class="nav">
        <el-menu-item index="/projects">
          <el-icon><Briefcase /></el-icon>
          <span>求职项目</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/question-bank">
          <el-icon><Tickets /></el-icon>
          <span>个人题库</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-title">{{ routeTitle }}</div>
        <el-dropdown trigger="click" @command="handleCommand">
          <button class="user-button">
            <el-icon><User /></el-icon>
            <span>{{ auth.user?.nickname || auth.user?.email || '用户' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ArrowDown, Briefcase, Collection, Tickets, User } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activePath = computed(() => {
  if (route.path.startsWith('/knowledge')) return '/knowledge'
  if (route.path.startsWith('/question-bank')) return '/question-bank'
  return '/projects'
})

const routeTitle = computed(() => {
  if (route.path.startsWith('/knowledge')) return '知识库'
  if (route.path.startsWith('/question-bank')) return '个人题库'
  return '求职项目'
})

function handleCommand(command) {
  if (command === 'logout') {
    auth.logout()
    router.push('/auth')
  }
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
}

.sidebar {
  border-right: 1px solid #e5e7eb;
  background: #111827;
  color: #fff;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 72px;
  padding: 0 18px;
}

.brand-mark {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 8px;
  background: #2dd4bf;
  color: #042f2e;
  font-weight: 800;
}

.brand strong,
.brand span {
  display: block;
}

.brand span {
  margin-top: 3px;
  color: #9ca3af;
  font-size: 12px;
}

.nav {
  border-right: 0;
  background: transparent;
}

.nav :deep(.el-menu-item) {
  color: #d1d5db;
}

.nav :deep(.el-menu-item.is-active),
.nav :deep(.el-menu-item:hover) {
  background: #1f2937;
  color: #fff;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
}

.topbar-title {
  color: #111827;
  font-weight: 700;
}

.user-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  background: transparent;
  color: #374151;
  cursor: pointer;
  font: inherit;
}

.main {
  background: #f5f7fb;
  padding: 24px;
}

@media (max-width: 760px) {
  .sidebar {
    display: none;
  }

  .main {
    padding: 16px;
  }
}
</style>
