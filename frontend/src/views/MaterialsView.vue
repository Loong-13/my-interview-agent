<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">简历与 JD 分析</h1>
        <p class="page-subtitle">上传简历、粘贴岗位描述，再触发解析、分析和匹配任务。</p>
      </div>
      <el-button @click="router.push(`/projects/${projectId}`)">返回项目</el-button>
    </div>

    <TaskStatus
      :task-id="refs.lastTaskId"
      title="当前分析任务"
      @success="handleTaskDone"
    />

    <div class="grid">
      <section class="panel span-6">
        <h2 class="panel-title">简历</h2>
        <el-upload
          drag
          :auto-upload="false"
          :limit="1"
          :on-change="handleResumeChange"
          :on-remove="() => (resumeFile = null)"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div>拖入或选择 PDF / DOCX / TXT 简历</div>
        </el-upload>

        <div class="toolbar material-actions">
          <el-button type="primary" :disabled="!resumeFile" :loading="uploading" @click="uploadResume">上传简历</el-button>
          <el-button :disabled="!refs.resumeId" @click="startParseResume">解析文本</el-button>
          <el-button :disabled="!refs.resumeId" @click="startAnalyzeResume">分析简历</el-button>
        </div>

        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="简历 ID">{{ refs.resumeId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="文件">{{ refs.resumeFileName || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-input
          v-model="resumeText"
          type="textarea"
          :rows="12"
          class="text-block"
          placeholder="解析完成后可查看简历文本"
        />
      </section>

      <section class="panel span-6">
        <h2 class="panel-title">岗位 JD</h2>
        <el-form :model="jdForm" label-position="top">
          <div class="grid">
            <el-form-item label="公司" class="span-6">
              <el-input v-model="jdForm.company" placeholder="某公司" />
            </el-form-item>
            <el-form-item label="岗位" class="span-6">
              <el-input v-model="jdForm.position" placeholder="AI Agent 实习生" />
            </el-form-item>
          </div>
          <el-form-item label="JD 原文">
            <el-input v-model="jdForm.raw_text" type="textarea" :rows="12" placeholder="粘贴岗位要求..." />
          </el-form-item>
        </el-form>

        <div class="toolbar material-actions">
          <el-button type="primary" :loading="savingJd" @click="createJd">保存 JD</el-button>
          <el-button :disabled="!refs.jdId" @click="startAnalyzeJd">分析 JD</el-button>
          <el-button type="success" :disabled="!canMatch" @click="startMatch">生成匹配报告</el-button>
        </div>

        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="JD ID">{{ refs.jdId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="岗位">{{ refs.jdTitle || '-' }}</el-descriptions-item>
        </el-descriptions>
      </section>
    </div>
  </div>
</template>

<script setup>
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { jdApi, matchApi, resumeApi } from '@/api/modules'
import TaskStatus from '@/components/TaskStatus.vue'
import { useProjectDraftsStore } from '@/stores/projectDrafts'

const route = useRoute()
const router = useRouter()
const drafts = useProjectDraftsStore()
const projectId = route.params.id.toString()
const refs = computed(() => drafts.ensure(projectId))

const resumeFile = ref(null)
const resumeText = ref('')
const uploading = ref(false)
const savingJd = ref(false)
const jdForm = reactive({ company: '', position: '', raw_text: '' })
const canMatch = computed(() => refs.value.resumeId && refs.value.jdId)

function handleResumeChange(uploadFile) {
  resumeFile.value = uploadFile.raw
}

async function uploadResume() {
  uploading.value = true
  try {
    const data = await resumeApi.upload(projectId, resumeFile.value)
    drafts.patch(projectId, { resumeId: data.resume_id, resumeFileName: data.file_name })
    ElMessage.success('简历已上传')
  } finally {
    uploading.value = false
  }
}

async function startParseResume() {
  const task = await resumeApi.parse(refs.value.resumeId)
  drafts.patch(projectId, { lastTaskId: task.task_id })
}

async function startAnalyzeResume() {
  const task = await resumeApi.analyze(refs.value.resumeId, { target_direction: undefined })
  drafts.patch(projectId, { lastTaskId: task.task_id })
}

async function createJd() {
  savingJd.value = true
  try {
    const jd = await jdApi.create(projectId, jdForm)
    drafts.patch(projectId, { jdId: jd.id, jdTitle: jd.position || jd.company || '岗位 JD' })
    ElMessage.success('JD 已保存')
  } finally {
    savingJd.value = false
  }
}

async function startAnalyzeJd() {
  const task = await jdApi.analyze(refs.value.jdId)
  drafts.patch(projectId, { lastTaskId: task.task_id })
}

async function startMatch() {
  const task = await matchApi.create(projectId, {
    resume_id: refs.value.resumeId,
    job_description_id: refs.value.jdId,
  })
  drafts.patch(projectId, { lastTaskId: task.task_id })
}

async function handleTaskDone(task) {
  if (task.task_type === 'resume.parse' && refs.value.resumeId) {
    const resume = await resumeApi.get(refs.value.resumeId)
    resumeText.value = resume.raw_text || ''
  }
}
</script>

<style scoped>
.upload-icon {
  color: #64748b;
  font-size: 32px;
}

.material-actions {
  margin: 16px 0;
}

.text-block {
  margin-top: 16px;
}
</style>
