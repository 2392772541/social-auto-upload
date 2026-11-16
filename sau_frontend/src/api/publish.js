import { http } from '@/utils/request'

export const publishApi = {
  getPublishHistory(limit = 50, silent = true) {
    return http.get(`/getPublishHistory?limit=${limit}`, undefined, { silent })
  },

  deletePublishRecord(id) {
    return http.get(`/deletePublishRecord?id=${encodeURIComponent(id)}`)
  }
}
