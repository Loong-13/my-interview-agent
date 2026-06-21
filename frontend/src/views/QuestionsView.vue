<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">题目训练</h1>
        <p class="page-subtitle">根据项目或个人知识库生成面试题，并浏览已生成题目。</p>
      </div>
      <el-button @click="router.push(`/projects/${projectId}`)">返回项目</el-button>
    </div>

    <TaskStatus :task-id="refs.lastTaskId" title="题目生成任务" @success="handleTaskSuccess" />

    <div class="grid question-layout">
      <section class="panel span-5 generate-panel">
        <h2 class="panel-title">生成题目</h2>
        <el-form :model="form" label-position="top">
          <el-form-item label="模式">
            <el-select v-model="form.mode">
              <el-option
                v-for="item in questionModes"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <div class="grid">
            <el-form-item label="难度" class="span-6">
              <el-select v-model="form.difficulty">
                <el-option v-for="item in experienceLevels" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="数量" class="span-6">
              <el-input-number v-model="form.count" :min="1" :max="20" />
            </el-form-item>
          </div>
          <el-form-item label="关注点">
            <el-select v-model="focusTags" multiple filterable allow-create default-first-option placeholder="FastAPI / RAG / PostgreSQL">
              <el-option v-for="tag in focusTags" :key="tag" :label="tag" :value="tag" />
            </el-select>
          </el-form-item>
          <el-form-item label="知识库集合">
            <el-select v-model="collectionIds" multiple clearable placeholder="可选，用于知识库增强出题">
              <el-option
                v-for="item in collections"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="toolbar">
          <el-button type="primary" @click="generate(false)">按项目生成</el-button>
          <el-button :disabled="!collectionIds.length" @click="generate(true)">知识库增强</el-button>
        </div>
      </section>

      <section class="panel span-7 questions-panel">
        <div class="panel-head">
          <h2 class="panel-title">项目题目</h2>
          <el-button text type="primary" @click="loadQuestions">刷新</el-button>
        </div>

        <div class="questions-scroll">
          <div v-if="questions.length" class="question-list">
            <article v-for="item in questions" :key="item.id" class="question-card">
              <div class="question-meta">
                <el-tag>{{ labelOf(questionModes, item.type) }}</el-tag>
                <el-tag type="info">{{ labelOf(experienceLevels, item.difficulty) }}</el-tag>
              </div>
              <h3>{{ item.question }}</h3>
              <div v-if="item.reference_answer" class="answer-section">
                <el-button text size="small" @click="item._showAnswer = !item._showAnswer">
                  {{ item._showAnswer ? '收起答案 ▴' : '展开答案 ▾' }}
                </el-button>
                <p v-show="item._showAnswer" class="answer-text">{{ item.reference_answer }}</p>
              </div>
              <div class="tag-list">
                <el-tag v-for="point in item.evaluation_points" :key="point" type="success" effect="plain">
                  {{ point }}
                </el-tag>
              </div>
            </article>
          </div>
          <div v-else class="empty">暂无题目。先生成一组项目相关题。</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { knowledgeApi, questionApi } from '@/api/modules'
import TaskStatus from '@/components/TaskStatus.vue'
import { experienceLevels, interviewModes, labelOf } from '@/constants/options'
import { useProjectDraftsStore } from '@/stores/projectDrafts'

const route = useRoute()
const router = useRouter()
const drafts = useProjectDraftsStore()
const projectId = route.params.id.toString()
const refs = computed(() => drafts.ensure(projectId))

const questionModes = interviewModes.filter((item) => item.value !== 'question_bank_review')
const questions = ref([])
const collections = ref([])
const focusTags = ref([])
const collectionIds = ref([])
const form = reactive({
  mode: 'python_backend_project',
  difficulty: 'intern',
  count: 10,
})

async function loadQuestions() {
  const data = await questionApi.list(projectId)
  questions.value = data.questions || []
}

async function loadCollections() {
  const data = await knowledgeApi.collections()
  collections.value = data.items
}

async function generate(fromKnowledge) {
  const payload = {
    ...form,
    focus: focusTags.value,
  }
  const task = fromKnowledge
    ? await questionApi.generateFromKnowledge(projectId, { ...payload, collection_ids: collectionIds.value })
    : await questionApi.generate(projectId, payload)
  drafts.patch(projectId, { lastTaskId: task.task_id, questionsGenerated: false })
}

async function handleTaskSuccess() {
  drafts.patch(projectId, { matchReportGenerated: true, questionsGenerated: true })
  await loadQuestions()
}

onMounted(() => {
  loadQuestions()
  loadCollections()
})
</script>

<style scoped>
.panel-head {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
}

.question-layout {
  align-items: start;
}

.generate-panel {
  position: sticky;
  top: 24px;
}

.questions-panel {
  display: flex;
  height: calc(100vh - 250px);
  min-height: 420px;
  flex-direction: column;
}

.questions-scroll {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding-right: 6px;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.question-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
}

.question-card h3 {
  margin: 10px 0;
  font-size: 16px;
  line-height: 1.6;
}

.question-meta {
  display: flex;
  gap: 8px;
}

.answer-section {
  margin: 6px 0 0;
}

.answer-text {
  margin: 8px 0;
  padding: 10px 12px;
  background: #f5f7fa;
  border-left: 3px solid var(--el-color-primary);
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.7;
  color: #4a5568;
  white-space: pre-wrap;
}

@media (max-width: 900px) {
  .generate-panel {
    position: static;
  }

  .questions-panel {
    height: auto;
    max-height: none;
  }

  .questions-scroll {
    overflow-y: visible;
    padding-right: 0;
  }
}
</style>
