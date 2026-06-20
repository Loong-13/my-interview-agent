<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">模拟面试</h1>
        <p class="page-subtitle">选择模式后开始文本面试，结束后可触发报告生成。</p>
      </div>
      <el-button @click="router.push(`/projects/${projectId}`)">返回项目</el-button>
    </div>

    <TaskStatus :task-id="refs.lastTaskId" title="报告生成任务" @success="loadReport" />

    <div class="grid">
      <section class="panel span-4">
        <h2 class="panel-title">会话设置</h2>
        <el-form :model="form" label-position="top">
          <el-form-item label="模式">
            <el-select v-model="form.mode">
              <el-option v-for="item in interviewModes" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="难度">
            <el-select v-model="form.difficulty">
              <el-option v-for="item in experienceLevels" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="toolbar">
          <el-button type="primary" :disabled="Boolean(sessionId)" @click="createAndStart">开始</el-button>
          <el-button :disabled="!sessionId" @click="finishInterview">结束</el-button>
          <el-button :disabled="!sessionId" type="success" @click="generateReport">生成报告</el-button>
        </div>

        <el-divider />
        <el-descriptions :column="1" size="small">
          <el-descriptions-item label="会话 ID">{{ sessionId || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ finished ? '已结束' : sessionId ? '进行中' : '未开始' }}</el-descriptions-item>
        </el-descriptions>
      </section>

      <section class="panel span-8">
        <h2 class="panel-title">面试对话</h2>
        <div class="chat">
          <div v-for="(message, index) in messages" :key="message.id || index" class="message" :class="message.role">
            <div class="message-role">{{ message.role === 'candidate' ? '我' : '面试官' }}</div>
            <div>{{ message.content }}</div>
            <el-alert
              v-if="message.feedback"
              :title="message.feedback"
              type="info"
              show-icon
              :closable="false"
              class="feedback"
            />
          </div>
          <div v-if="!messages.length" class="empty">点击开始后，面试官会给出第一道题。</div>
        </div>

        <div class="answer-box">
          <el-input v-model="answer" type="textarea" :rows="4" placeholder="输入你的回答..." />
          <el-button type="primary" :disabled="!sessionId || !answer.trim()" :loading="answering" @click="submitAnswer">
            提交回答
          </el-button>
        </div>
      </section>

      <section v-if="report" class="panel span-12">
        <h2 class="panel-title">复盘报告</h2>
        <div class="grid">
          <div class="span-4 metric">
            <span class="muted">总分</span>
            <strong>{{ report.overall_score }}</strong>
          </div>
          <div class="span-8">
            <el-table :data="scoreRows" size="small">
              <el-table-column prop="name" label="维度" />
              <el-table-column prop="score" label="分数" width="120" />
            </el-table>
          </div>
        </div>
        <el-divider />
        <div class="grid">
          <div class="span-4">
            <h3>优势</h3>
            <el-tag v-for="item in report.strengths" :key="item" class="report-tag" type="success">{{ item }}</el-tag>
          </div>
          <div class="span-4">
            <h3>薄弱点</h3>
            <el-tag v-for="item in report.weaknesses" :key="item" class="report-tag" type="danger">{{ item }}</el-tag>
          </div>
          <div class="span-4">
            <h3>推荐主题</h3>
            <el-tag v-for="item in report.recommended_topics" :key="item" class="report-tag" type="warning">{{ item }}</el-tag>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { interviewApi } from '@/api/modules'
import TaskStatus from '@/components/TaskStatus.vue'
import { experienceLevels, interviewModes } from '@/constants/options'
import { useProjectDraftsStore } from '@/stores/projectDrafts'

const route = useRoute()
const router = useRouter()
const drafts = useProjectDraftsStore()
const projectId = route.params.id.toString()
const refs = computed(() => drafts.ensure(projectId))

const form = reactive({ mode: 'agent_basic', difficulty: 'intern' })
const sessionId = ref(refs.value.lastSessionId || '')
const messages = ref([])
const answer = ref('')
const answering = ref(false)
const finished = ref(false)
const report = ref(null)

const scoreRows = computed(() =>
  Object.entries(report.value?.scores || {}).map(([name, score]) => ({ name, score })),
)

async function createAndStart() {
  const session = await interviewApi.create(projectId, form)
  sessionId.value = session.session_id
  drafts.patch(projectId, { lastSessionId: session.session_id, interviewStarted: true })
  const start = await interviewApi.start(session.session_id)
  messages.value = [{ role: 'interviewer', content: start.first_question }]
}

async function submitAnswer() {
  const current = answer.value.trim()
  if (!current) return
  answering.value = true
  try {
    messages.value.push({ role: 'candidate', content: current })
    answer.value = ''
    const data = await interviewApi.answer(sessionId.value, { answer: current })
    messages.value.push({
      role: 'interviewer',
      content: data.next_question,
      feedback: data.feedback,
    })
    if (!data.should_continue) {
      finished.value = true
    }
  } finally {
    answering.value = false
  }
}

async function finishInterview() {
  await interviewApi.finish(sessionId.value)
  finished.value = true
}

async function generateReport() {
  const task = await interviewApi.generateReport(sessionId.value)
  drafts.patch(projectId, { lastTaskId: task.task_id })
}

async function loadReport() {
  if (!sessionId.value) return
  report.value = await interviewApi.getReport(sessionId.value)
}
</script>

<style scoped>
.answer-box {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 108px;
  gap: 12px;
  margin-top: 16px;
  align-items: end;
}

.feedback {
  margin-top: 10px;
}

h3 {
  margin: 0 0 10px;
  font-size: 15px;
}

.report-tag {
  margin: 0 8px 8px 0;
}

@media (max-width: 720px) {
  .answer-box {
    grid-template-columns: 1fr;
  }
}
</style>
