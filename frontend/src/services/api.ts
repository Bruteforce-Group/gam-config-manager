import axios from 'axios'
import type {
  Configuration,
  ConfigComparison,
  SecurityAnalysis,
  ConfigTemplate,
  SecurityScore,
  GAMExtractRequest,
  GAMExtractResponse,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''
const API_V1 = `${API_BASE_URL}/api/v1`

const api = axios.create({
  baseURL: API_V1,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Configurations
export const configurationsApi = {
  list: (params?: { skip?: number; limit?: number; is_template?: boolean }) =>
    api.get<Configuration[]>('/configurations/', { params }),
  
  get: (id: number) =>
    api.get<Configuration>(`/configurations/${id}`),
  
  create: (data: Partial<Configuration>) =>
    api.post<Configuration>('/configurations/', data),
  
  update: (id: number, data: Partial<Configuration>) =>
    api.put<Configuration>(`/configurations/${id}`, data),
  
  delete: (id: number) =>
    api.delete(`/configurations/${id}`),
}

// Comparisons
export const comparisonsApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    api.get<ConfigComparison[]>('/comparisons/', { params }),
  
  get: (id: number) =>
    api.get<ConfigComparison>(`/comparisons/${id}`),
  
  create: (data: { source_config_id: number; target_config_id: number }) =>
    api.post<ConfigComparison>('/comparisons/', data),
}

// Security
export const securityApi = {
  analyze: (configId: number) =>
    api.post<SecurityAnalysis[]>(`/security/analyze/${configId}`),
  
  getAnalyses: (configId: number) =>
    api.get<SecurityAnalysis[]>(`/security/analyses/${configId}`),
  
  getScore: (configId: number) =>
    api.get<SecurityScore>(`/security/score/${configId}`),
}

// Templates
export const templatesApi = {
  list: (params?: { skip?: number; limit?: number; is_active?: boolean }) =>
    api.get<ConfigTemplate[]>('/templates/', { params }),
  
  get: (id: number) =>
    api.get<ConfigTemplate>(`/templates/${id}`),
  
  create: (data: Partial<ConfigTemplate>) =>
    api.post<ConfigTemplate>('/templates/', data),
  
  delete: (id: number) =>
    api.delete(`/templates/${id}`),
}

// GAM
export const gamApi = {
  extract: (data: GAMExtractRequest) =>
    api.post<GAMExtractResponse>('/gam/extract', data),
  
  testConnection: () =>
    api.get<{ status: string; message: string; version?: string }>('/gam/test-connection'),
}

// Remediation
export const remediationApi = {
  execute: (data: { finding_id: number; action_id: string; parameters?: Record<string, any>; auto_rescan?: boolean }) =>
    api.post<{
      success: boolean
      message: string
      finding_id: number
      action_executed: string
      gam_output?: string
      new_configuration_id?: number
      security_score_before?: number
      security_score_after?: number
      finding_resolved: boolean
    }>('/remediation/execute', data),
}

export default api

