<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ project?.name || '项目详情' }}</h1>
        <p class="page-subtitle">
          {{ project?.target_company || '未填写公司' }} · {{ project?.target_role || '目标岗位' }}
        </p>
      </div>
      <div class="toolbar">
        <el-button :icon="Upload" @click="router.push(`/projects/${projectId}/materials`)">简历与 JD</el-button>
        <el-button :icon="Tickets" @click="router.push(`/projects/${projectId}/questions`)">题目训练</el-button>
        <el-button type="primary" :icon="ChatLineRound" @click="router.push(`/projects/${projectId}/interview`)">
          模拟面试
        </el-button>
      </div>
    </div>

    <TaskStatus
      :task-id="refs.lastTaskId"
      title="最近任务"
      @success="loadProject"
      @failed="loadProject"
    />

    <div class="grid">
      <section class="panel span-4">
        <h2 class="panel-title">匹配概览</h2>
        <div class="metric">
          <span class="muted">最近匹配分</span>
          <strong>{{ project?.latest_match_score ?? '-' }}</strong>
        </div>
      </section>

      <section class="panel span-4">
        <h2 class="panel-title">简历状态</h2>
        <el-descriptions :column="1" size="small">
          <el-descriptions-item label="简历 ID">{{ refs.resumeId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="文件">{{ refs.resumeFileName || '-' }}</el-descriptions-item>
        </el-descriptions>
      </section>

      <section class="panel span-4">
        <h2 class="panel-title">JD 状态</h2>
        <el-descriptions :column="1" size="small">
          <el-descriptions-item label="JD ID">{{ refs.jdId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="岗位">{{ refs.jdTitle || '-' }}</el-descriptions-item>
        </el-descriptions>
      </section>

      <section class="panel span-8">
        <h2 class="panel-title">下一步建议</h2>
        <el-steps :active="stepActive" finish-status="success" align-center>
          <el-step title="上传简历" />
          <el-step title="粘贴 JD" />
          <el-step title="生成匹配" />
          <el-step title="题目训练" />
          <el-step title="模拟面试" />
        </el-steps>
      </section>

      <section class="panel span-4">
        <h2 class="panel-title">项目信息</h2>
        <el-descriptions :column="1" size="small">
          <el-descriptions-item label="方向">{{ labelOf(directions, project?.direction) }}</el-descriptions-item>
          <el-descriptions-item label="级别">{{ labelOf(experienceLevels, project?.experience_level) }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ project?.status || '-' }}</el-descriptions-item>
        </el-descriptions>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ChatLineRound, Tickets, Upload } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { projectApi } from '@/api/modules'
import TaskStatus from '@/components/TaskStatus.vue'
import { directions, experienceLevels, labelOf } from '@/constants/options'
import { useProjectDraftsStore } from '@/stores/projectDrafts'

const route = useRoute()
const router = useRouter()
const drafts = useProjectDraftsStore()
const projectId = route.params.id.toString()
const project = ref(null)
const refs = computed(() => drafts.ensure(projectId))

const stepActive = computed(() => {
  if (!refs.value.resumeId) return 0
  if (!refs.value.jdId) return 1
  if (!project.value?.latest_match_score) return 2
  return 3
})

async function loadProject() {
  project.value = await projectApi.get(projectId)
}

onMounted(loadProject)
</script>
