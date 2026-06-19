<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">题目训练</h1>
        <p class="page-subtitle">根据项目或个人知识库生成面试题，并浏览已生成题目。</p>
      </div>
      <el-button @click="router.push(`/projects/${projectId}`)">返回项目</el-button>
    </div>

    <TaskStatus :task-id="refs.lastTaskId" title="题目生成任务" @success="loadQuestions" />

    <div class="grid">
      <section class="panel span-5">
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

      <section class="panel span-7">
        <div class="panel-head">
          <h2 class="panel-title">项目题目</h2>
          <el-button text type="primary" @click="loadQuestions">刷新</el-button>
        </div>

        <div v-if="questions.length" class="question-list">
          <article v-for="item in questions" :key="item.id" class="question-card">
            <div class="question-meta">
              <el-tag>{{ labelOf(questionModes, item.type) }}</el-tag>
              <el-tag type="info">{{ labelOf(experienceLevels, item.difficulty) }}</el-tag>
            </div>
            <h3>{{ item.question }}</h3>
            <div class="tag-list">
              <el-tag v-for="point in item.evaluation_points" :key="point" type="success" effect="plain">
                {{ point }}
              </el-tag>
            </div>
          </article>
        </div>
        <div v-else class="empty">暂无题目。先生成一组项目相关题。</div>
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
  drafts.patch(projectId, { lastTaskId: task.task_id })
}

onMounted(() => {
  loadQuestions()
  loadCollections()
})
</script>

<style scoped>
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
</style>
