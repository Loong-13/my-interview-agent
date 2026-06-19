<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">知识库</h1>
        <p class="page-subtitle">沉淀面经、八股文、项目文档和复习资料，用于检索和增强出题。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="collectionDialog = true">新建集合</el-button>
    </div>

    <TaskStatus :task-id="lastTaskId" title="知识库任务" @success="loadDocuments" />

    <div class="grid">
      <section class="panel span-4">
        <h2 class="panel-title">集合</h2>
        <el-table :data="collections" highlight-current-row @current-change="selectCollection">
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="visibility" label="可见性" width="92" />
        </el-table>
      </section>

      <section class="panel span-8">
        <div class="panel-head">
          <h2 class="panel-title">文档</h2>
          <div class="toolbar">
            <el-button :disabled="!currentCollectionId" @click="uploadDialog = true">上传文件</el-button>
            <el-button :disabled="!currentCollectionId" @click="textDialog = true">粘贴文本</el-button>
          </div>
        </div>

        <el-table :data="documents">
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="content_type" label="类型" width="120">
            <template #default="{ row }">{{ labelOf(contentTypes, row.content_type) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="110" />
          <el-table-column prop="chunk_count" label="切片" width="80" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button text type="primary" @click="indexDocument(row.id)">索引</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="panel span-12">
        <h2 class="panel-title">检索</h2>
        <div class="search-bar">
          <el-input v-model="searchForm.query" placeholder="FastAPI 依赖注入面试题" />
          <el-input-number v-model="searchForm.top_k" :min="1" :max="20" />
          <el-button type="primary" :disabled="!searchForm.query" @click="search">检索</el-button>
        </div>
        <div v-if="searchResults.length" class="result-list">
          <article v-for="item in searchResults" :key="item.chunk_id" class="result-item">
            <div class="result-title">{{ item.title || '未命名片段' }} · {{ item.score.toFixed(3) }}</div>
            <p>{{ item.content }}</p>
          </article>
        </div>
        <div v-else class="empty">选择集合并输入关键词，检索个人资料中的相关片段。</div>
      </section>
    </div>

    <el-dialog v-model="collectionDialog" title="新建知识集合" width="520px">
      <el-form :model="collectionForm" label-position="top">
        <el-form-item label="名称">
          <el-input v-model="collectionForm.name" placeholder="Python 后端八股文" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="collectionForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="collectionDialog = false">取消</el-button>
        <el-button type="primary" @click="createCollection">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="uploadDialog" title="上传知识文档" width="560px">
      <el-form :model="uploadForm" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="uploadForm.title" placeholder="Python 高频八股题" />
        </el-form-item>
        <el-form-item label="内容类型">
          <el-select v-model="uploadForm.content_type">
            <el-option v-for="item in contentTypes" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-upload drag :auto-upload="false" :limit="1" :on-change="(file) => (uploadFile = file.raw)">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div>支持 PDF / DOCX / TXT / Markdown</div>
        </el-upload>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!uploadFile" @click="uploadDocument">上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="textDialog" title="粘贴文本资料" width="680px">
      <el-form :model="textForm" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="textForm.title" />
        </el-form-item>
        <el-form-item label="内容类型">
          <el-select v-model="textForm.content_type">
            <el-option v-for="item in contentTypes" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="正文">
          <el-input v-model="textForm.raw_text" type="textarea" :rows="12" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="textDialog = false">取消</el-button>
        <el-button type="primary" @click="createTextDocument">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Plus, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { knowledgeApi } from '@/api/modules'
import TaskStatus from '@/components/TaskStatus.vue'
import { contentTypes, labelOf } from '@/constants/options'

const collections = ref([])
const documents = ref([])
const searchResults = ref([])
const currentCollectionId = ref('')
const lastTaskId = ref('')
const collectionDialog = ref(false)
const uploadDialog = ref(false)
const textDialog = ref(false)
const uploadFile = ref(null)

const collectionForm = reactive({ name: '', description: '', visibility: 'private' })
const uploadForm = reactive({ title: '', content_type: 'interview_notes' })
const textForm = reactive({ title: '', content_type: 'interview_notes', raw_text: '', metadata: {} })
const searchForm = reactive({ query: '', top_k: 5 })

async function loadCollections() {
  const data = await knowledgeApi.collections()
  collections.value = data.items
  if (!currentCollectionId.value && data.items[0]) {
    currentCollectionId.value = data.items[0].id
  }
  await loadDocuments()
}

async function loadDocuments() {
  const data = await knowledgeApi.documents(currentCollectionId.value)
  documents.value = data.items
}

function selectCollection(row) {
  if (!row) return
  currentCollectionId.value = row.id
  loadDocuments()
}

async function createCollection() {
  const item = await knowledgeApi.createCollection(collectionForm)
  collectionDialog.value = false
  currentCollectionId.value = item.id
  await loadCollections()
}

async function uploadDocument() {
  await knowledgeApi.uploadDocument(currentCollectionId.value, { ...uploadForm, file: uploadFile.value })
  uploadDialog.value = false
  uploadFile.value = null
  ElMessage.success('文档已上传')
  await loadDocuments()
}

async function createTextDocument() {
  await knowledgeApi.createTextDocument(currentCollectionId.value, textForm)
  textDialog.value = false
  ElMessage.success('文本资料已保存')
  await loadDocuments()
}

async function indexDocument(documentId) {
  const task = await knowledgeApi.indexDocument(documentId, { extract_questions: true })
  lastTaskId.value = task.task_id
}

async function search() {
  const data = await knowledgeApi.search({
    ...searchForm,
    collection_ids: currentCollectionId.value ? [currentCollectionId.value] : [],
  })
  searchResults.value = data.items
}

onMounted(loadCollections)
</script>

<style scoped>
.panel-head,
.search-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.search-bar {
  justify-content: flex-start;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.result-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
}

.result-title {
  color: #111827;
  font-weight: 700;
}

.result-item p {
  margin: 8px 0 0;
  color: #4b5563;
  line-height: 1.7;
}

.upload-icon {
  color: #64748b;
  font-size: 32px;
}

@media (max-width: 760px) {
  .panel-head,
  .search-bar {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
