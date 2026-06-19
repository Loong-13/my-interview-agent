<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">个人题库</h1>
        <p class="page-subtitle">维护高频题、参考答案、评价点和标签，用于复习与知识库增强出题。</p>
      </div>
      <div class="toolbar">
        <el-button :icon="Upload" @click="importDialog = true">批量导入</el-button>
        <el-button type="primary" :icon="Plus" @click="createDialog = true">新增题目</el-button>
      </div>
    </div>

    <TaskStatus :task-id="lastTaskId" title="题库导入任务" @success="loadItems" />

    <section class="panel">
      <div class="filters">
        <el-select v-model="filters.collection_id" clearable placeholder="集合">
          <el-option v-for="item in collections" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="filters.difficulty" clearable placeholder="难度">
          <el-option label="实习" value="intern" />
          <el-option label="校招" value="new_grad" />
        </el-select>
        <el-input v-model="filters.type" placeholder="类型" clearable />
        <el-input v-model="filters.tag" placeholder="标签" clearable />
        <el-input v-model="filters.keyword" placeholder="关键词" clearable />
        <el-button type="primary" @click="loadItems">筛选</el-button>
      </div>

      <el-table :data="items" class="bank-table">
        <el-table-column prop="question" label="题目" min-width="260" />
        <el-table-column prop="type" label="类型" width="150" />
        <el-table-column prop="difficulty" label="难度" width="100" />
        <el-table-column label="标签" min-width="180">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" class="tag" effect="plain">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expanded">
              <h3>参考答案</h3>
              <p>{{ row.reference_answer || '暂无' }}</p>
              <h3>评价点</h3>
              <div class="tag-list">
                <el-tag v-for="point in row.evaluation_points" :key="point" type="success" effect="plain">
                  {{ point }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="createDialog" title="新增题目" width="720px">
      <el-form :model="form" label-position="top">
        <div class="grid">
          <el-form-item label="集合" class="span-6">
            <el-select v-model="form.collection_id" clearable>
              <el-option v-for="item in collections" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="类型" class="span-6">
            <el-input v-model="form.type" placeholder="fastapi_backend" />
          </el-form-item>
        </div>
        <el-form-item label="难度">
          <el-select v-model="form.difficulty">
            <el-option label="实习" value="intern" />
            <el-option label="校招" value="new_grad" />
          </el-select>
        </el-form-item>
        <el-form-item label="题目">
          <el-input v-model="form.question" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="参考答案">
          <el-input v-model="form.reference_answer" type="textarea" :rows="6" />
        </el-form-item>
        <el-form-item label="评价点">
          <el-select v-model="form.evaluation_points" multiple filterable allow-create default-first-option />
        </el-form-item>
        <el-form-item label="标签">
          <el-select v-model="form.tags" multiple filterable allow-create default-first-option />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialog = false">取消</el-button>
        <el-button type="primary" @click="createItem">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialog" title="批量导入题库" width="720px">
      <el-form :model="importForm" label-position="top">
        <el-form-item label="集合">
          <el-select v-model="importForm.collection_id">
            <el-option v-for="item in collections" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="格式">
          <el-input v-model="importForm.format" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="importForm.content" type="textarea" :rows="14" placeholder="## FastAPI&#10;Q: ...&#10;A: ..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialog = false">取消</el-button>
        <el-button type="primary" @click="importItems">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Plus, Upload } from '@element-plus/icons-vue'
import { onMounted, reactive, ref } from 'vue'

import { knowledgeApi, questionBankApi } from '@/api/modules'
import TaskStatus from '@/components/TaskStatus.vue'

const collections = ref([])
const items = ref([])
const lastTaskId = ref('')
const createDialog = ref(false)
const importDialog = ref(false)

const filters = reactive({
  collection_id: '',
  type: '',
  difficulty: '',
  tag: '',
  keyword: '',
})

const form = reactive({
  collection_id: '',
  type: 'fastapi_backend',
  difficulty: 'intern',
  question: '',
  reference_answer: '',
  evaluation_points: [],
  tags: [],
})

const importForm = reactive({
  collection_id: '',
  format: 'qa_markdown',
  content: '',
})

function cleanParams(payload) {
  return Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== '' && value !== null))
}

async function loadCollections() {
  const data = await knowledgeApi.collections()
  collections.value = data.items
  if (!importForm.collection_id && data.items[0]) {
    importForm.collection_id = data.items[0].id
  }
}

async function loadItems() {
  const data = await questionBankApi.list(cleanParams(filters))
  items.value = data.items
}

async function createItem() {
  await questionBankApi.create({ ...form, collection_id: form.collection_id || null })
  createDialog.value = false
  await loadItems()
}

async function importItems() {
  const task = await questionBankApi.import(importForm)
  lastTaskId.value = task.task_id
  importDialog.value = false
}

onMounted(() => {
  loadCollections()
  loadItems()
})
</script>

<style scoped>
.filters {
  display: grid;
  grid-template-columns: 180px 140px 160px 160px minmax(180px, 1fr) 88px;
  gap: 10px;
}

.bank-table {
  margin-top: 16px;
}

.tag {
  margin: 0 6px 6px 0;
}

.expanded {
  padding: 8px 22px 18px;
}

.expanded h3 {
  margin: 12px 0 8px;
  font-size: 15px;
}

.expanded p {
  margin: 0;
  color: #4b5563;
  line-height: 1.7;
}

@media (max-width: 980px) {
  .filters {
    grid-template-columns: 1fr;
  }
}
</style>
