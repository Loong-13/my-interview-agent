import { defineStore } from 'pinia'

const storageKey = 'pyoffer_project_refs'

export const useProjectDraftsStore = defineStore('projectDrafts', {
  state: () => ({
    refs: JSON.parse(localStorage.getItem(storageKey) || '{}'),
  }),
  actions: {
    save() {
      localStorage.setItem(storageKey, JSON.stringify(this.refs))
    },
    ensure(projectId) {
      if (!this.refs[projectId]) {
        this.refs[projectId] = {
          resumeId: '',
          resumeFileName: '',
          jdId: '',
          jdTitle: '',
          lastTaskId: '',
          lastSessionId: '',
        }
      }
      return this.refs[projectId]
    },
    patch(projectId, payload) {
      this.refs[projectId] = { ...this.ensure(projectId), ...payload }
      this.save()
    },
  },
})
