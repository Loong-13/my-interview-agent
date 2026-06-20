import { defineStore } from 'pinia'

const storageKey = 'pyoffer_project_refs'

function defaultProjectRef() {
  return {
    resumeId: '',
    resumeFileName: '',
    jdId: '',
    jdTitle: '',
    lastTaskId: '',
    lastSessionId: '',
    matchReportGenerated: false,
    questionsGenerated: false,
    interviewStarted: false,
  }
}

export const useProjectDraftsStore = defineStore('projectDrafts', {
  state: () => ({
    refs: JSON.parse(localStorage.getItem(storageKey) || '{}'),
  }),
  actions: {
    save() {
      localStorage.setItem(storageKey, JSON.stringify(this.refs))
    },
    ensure(projectId) {
      this.refs[projectId] = { ...defaultProjectRef(), ...(this.refs[projectId] || {}) }
      return this.refs[projectId]
    },
    patch(projectId, payload) {
      this.refs[projectId] = { ...this.ensure(projectId), ...payload }
      this.save()
    },
  },
})
