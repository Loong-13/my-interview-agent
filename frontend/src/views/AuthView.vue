<template>
  <main class="auth-page">
    <section class="auth-intro">
      <div class="mark">P</div>
      <h1>PyOffer Agent</h1>
      <p>围绕简历、岗位和个人知识库的 Python 后端与 Agent 面试训练工作台。</p>
      <div class="auth-points">
        <span>项目匹配</span>
        <span>题目生成</span>
        <span>模拟追问</span>
        <span>知识库增强</span>
      </div>
    </section>

    <section class="auth-card">
      <el-tabs v-model="mode" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-position="top" @submit.prevent>
            <el-form-item label="邮箱">
              <el-input v-model="loginForm.email" autocomplete="email" placeholder="user@example.com" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" show-password autocomplete="current-password" />
            </el-form-item>
            <el-button type="primary" :loading="loading" class="wide" @click="submitLogin">登录</el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" label-position="top" @submit.prevent>
            <el-form-item label="昵称">
              <el-input v-model="registerForm.nickname" placeholder="小明" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="registerForm.email" autocomplete="email" placeholder="user@example.com" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="registerForm.password" type="password" show-password autocomplete="new-password" />
            </el-form-item>
            <el-button type="primary" :loading="loading" class="wide" @click="submitRegister">注册并登录</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </section>
  </main>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const mode = ref('login')
const loading = ref(false)

const loginForm = reactive({ email: '', password: '' })
const registerForm = reactive({ nickname: '', email: '', password: '' })

function nextPath() {
  return route.query.redirect?.toString() || '/projects'
}

async function submitLogin() {
  if (!loginForm.email || !loginForm.password) {
    ElMessage.warning('请输入邮箱和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(loginForm)
    router.push(nextPath())
  } finally {
    loading.value = false
  }
}

async function submitRegister() {
  if (!registerForm.email || registerForm.password.length < 8) {
    ElMessage.warning('请输入邮箱和至少 8 位密码')
    return
  }
  loading.value = true
  try {
    await auth.register(registerForm)
    router.push(nextPath())
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: grid;
  min-height: 100vh;
  grid-template-columns: minmax(0, 1fr) 420px;
  gap: 40px;
  align-items: center;
  background: #0f172a;
  padding: 48px clamp(18px, 7vw, 96px);
}

.auth-intro {
  color: #fff;
}

.mark {
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  border-radius: 8px;
  background: #2dd4bf;
  color: #042f2e;
  font-size: 24px;
  font-weight: 800;
}

h1 {
  margin: 26px 0 12px;
  font-size: clamp(36px, 6vw, 64px);
  letter-spacing: 0;
}

p {
  max-width: 620px;
  margin: 0;
  color: #cbd5e1;
  font-size: 18px;
  line-height: 1.7;
}

.auth-points {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 28px;
}

.auth-points span {
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 8px 12px;
  color: #e2e8f0;
}

.auth-card {
  border-radius: 8px;
  background: #fff;
  padding: 28px;
}

.wide {
  width: 100%;
}

@media (max-width: 860px) {
  .auth-page {
    grid-template-columns: 1fr;
  }
}
</style>
