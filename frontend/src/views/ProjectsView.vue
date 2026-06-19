<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">求职项目</h1>
        <p class="page-subtitle">按目标公司和岗位组织简历、JD、题目与模拟面试。</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="dialogVisible = true">创建项目</el-button>
    </div>

    <div v-if="projects.length" class="project-grid">
      <article v-for="project in projects" :key="project.id" class="project-card" @click="openProject(project.id)">
        <div class="project-card-head">
          <div>
            <h2>{{ project.name }}</h2>
            <p>{{ project.target_company || '未填写公司' }} · {{ project.target_role }}</p>
          </div>
          <el-tag :type="project.status === 'active' ? 'success' : 'info'">{{ project.status }}</el-tag>
        </div>
        <div class="project-meta">
          <span>{{ labelOf(directions, project.direction) }}</span>
          <span>{{ labelOf(experienceLevels, project.experience_level) }}</span>
          <span>匹配分 {{ project.latest_match_score ?? '-' }}</span>
        </div>
        <div class="project-actions" @click.stop>
          <el-button text type="primary" @click="openProject(project.id)">进入</el-button>
          <el-button text type="danger" @click="archiveProject(project.id)">归档</el-button>
        </div>
      </article>
    </div>
    <div v-else class="empty">还没有项目。创建一个目标岗位，训练流程就能跑起来。</div>

    <el-dialog v-model="dialogVisible" title="创建求职项目" width="560px">
      <el-form :model="form" label-position="top">
        <el-form-item label="项目名称">
          <el-input v-model="form.name" placeholder="Python 后端实习 - 字节" />
        </el-form-item>
        <el-form-item label="目标公司">
          <el-input v-model="form.target_company" placeholder="字节跳动" />
        </el-form-item>
        <el-form-item label="目标岗位">
          <el-input v-model="form.target_role" placeholder="Python Backend Intern" />
        </el-form-item>
        <div class="grid">
          <el-form-item label="方向" class="span-6">
            <el-select v-model="form.direction">
              <el-option v-for="item in directions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="经验级别" class="span-6">
            <el-select v-model="form.experience_level">
              <el-option v-for="item in experienceLevels" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="createProject">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { Plus } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { projectApi } from '@/api/modules'
import { directions, experienceLevels, labelOf } from '@/constants/options'

const router = useRouter()
const projects = ref([])
const dialogVisible = ref(false)
const saving = ref(false)
const form = reactive({
  name: '',
  target_company: '',
  target_role: '',
  direction: 'python_backend',
  experience_level: 'intern',
})

async function loadProjects() {
  const data = await projectApi.list()
  projects.value = data.items
}

function openProject(id) {
  router.push(`/projects/${id}`)
}

async function createProject() {
  saving.value = true
  try {
    const project = await projectApi.create(form)
    dialogVisible.value = false
    router.push(`/projects/${project.id}`)
  } finally {
    saving.value = false
  }
}

async function archiveProject(id) {
  await ElMessageBox.confirm('确认归档这个项目？', '归档项目', { type: 'warning' })
  await projectApi.archive(id)
  await loadProjects()
}

onMounted(loadProjects)
</script>

<style scoped>
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.project-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  padding: 18px;
  cursor: pointer;
  transition:
    border-color 0.18s ease,
    transform 0.18s ease;
}

.project-card:hover {
  border-color: #60a5fa;
  transform: translateY(-2px);
}

.project-card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

h2 {
  margin: 0;
  color: #111827;
  font-size: 18px;
}

.project-card p {
  margin: 8px 0 0;
  color: #6b7280;
}

.project-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

.project-meta span {
  border-radius: 8px;
  background: #f1f5f9;
  padding: 6px 10px;
  color: #475569;
  font-size: 13px;
}

.project-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}
</style>
