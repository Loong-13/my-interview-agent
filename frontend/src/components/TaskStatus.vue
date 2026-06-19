<template>
  <div v-if="taskId" class="task-box">
    <div>
      <strong>{{ title }}</strong>
      <p>{{ task?.task_type || '任务已提交' }}</p>
    </div>
    <div class="task-side">
      <el-tag :type="tagType">{{ statusText }}</el-tag>
      <el-progress :percentage="progress" :stroke-width="8" />
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, watch } from 'vue'
import { ref } from 'vue'

import { taskApi } from '@/api/modules'

const props = defineProps({
  taskId: { type: String, default: '' },
  title: { type: String, default: '异步任务' },
})
const emit = defineEmits(['success', 'failed', 'change'])

const task = ref(null)
let timer = 0

const progress = computed(() => task.value?.progress ?? (props.taskId ? 8 : 0))
const statusText = computed(() => {
  const status = task.value?.status || 'pending'
  const map = {
    pending: '等待中',
    running: '处理中',
    success: '已完成',
    failed: '失败',
  }
  return map[status] || status
})
const tagType = computed(() => {
  if (task.value?.status === 'success') return 'success'
  if (task.value?.status === 'failed') return 'danger'
  return 'warning'
})

async function poll() {
  if (!props.taskId) return
  task.value = await taskApi.get(props.taskId)
  emit('change', task.value)
  if (task.value.status === 'success') {
    emit('success', task.value)
    stop()
  } else if (task.value.status === 'failed') {
    emit('failed', task.value)
    stop()
  }
}

function start() {
  stop()
  if (!props.taskId) return
  poll()
  timer = window.setInterval(poll, 2500)
}

function stop() {
  if (timer) {
    window.clearInterval(timer)
    timer = 0
  }
}

watch(() => props.taskId, start, { immediate: true })
onBeforeUnmount(stop)
</script>

<style scoped>
.task-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border: 1px solid #fde68a;
  border-radius: 8px;
  background: #fffbeb;
  padding: 12px 14px;
}

.task-box p {
  margin: 4px 0 0;
  color: #92400e;
  font-size: 13px;
}

.task-side {
  display: grid;
  min-width: 220px;
  grid-template-columns: 72px 1fr;
  align-items: center;
  gap: 10px;
}

@media (max-width: 720px) {
  .task-box {
    align-items: flex-start;
    flex-direction: column;
  }

  .task-side {
    width: 100%;
    min-width: 0;
  }
}
</style>
