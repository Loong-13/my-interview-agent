export const directions = [
  { label: 'Python 后端', value: 'python_backend' },
  { label: 'Agent 工程', value: 'agent_engineer' },
  { label: 'LLM 应用', value: 'llm_application' },
]

export const experienceLevels = [
  { label: '实习', value: 'intern' },
  { label: '校招', value: 'new_grad' },
]

export const interviewModes = [
  { label: 'Python 基础', value: 'python_basic' },
  { label: '后端项目', value: 'python_backend_project' },
  { label: 'FastAPI 后端', value: 'fastapi_backend' },
  { label: 'Agent 基础', value: 'agent_basic' },
  { label: 'RAG 项目深挖', value: 'rag_project_deep_dive' },
  { label: '题库复习', value: 'question_bank_review' },
]

export const contentTypes = [
  { label: '面试笔记', value: 'interview_notes' },
  { label: '题库', value: 'question_bank' },
  { label: '面经', value: 'experience_post' },
  { label: '项目文档', value: 'project_doc' },
  { label: '课程笔记', value: 'course_note' },
  { label: '其他', value: 'other' },
]

export function labelOf(options, value) {
  return options.find((item) => item.value === value)?.label || value || '-'
}
