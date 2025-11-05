export enum ConfigType {
  USER = 'user',
  GROUP = 'group',
  OU = 'organizational_unit',
  DOMAIN = 'domain',
  CALENDAR = 'calendar',
  DRIVE = 'drive',
  GMAIL = 'gmail',
  SECURITY = 'security',
  MOBILE = 'mobile',
  OAUTH_TOKENS = 'oauth_tokens',
  ADMIN_ROLES = 'admin_roles',
  SHARED_DRIVES = 'shared_drives',
  OTHER = 'other',
}

export enum SeverityLevel {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  INFO = 'info',
}

export interface Configuration {
  id: number
  name: string
  description?: string
  config_type: ConfigType
  config_data: Record<string, any>
  is_template: boolean
  extraction_errors?: {
    errors: string[]
    failed_types: string[]
  } | null
  created_at: string
  updated_at: string
}

export interface ConfigComparison {
  id: number
  source_config_id: number
  target_config_id: number
  differences: {
    items: Difference[]
  }
  drift_detected: boolean
  summary?: string
  created_at: string
}

export interface Difference {
  path: string
  type: 'added' | 'removed' | 'modified'
  source_value: any
  target_value: any
  severity: 'low' | 'medium' | 'high'
}

export interface SecurityAnalysis {
  id: number
  configuration_id: number
  severity: SeverityLevel
  category?: string
  title: string
  description: string
  recommendation: string
  affected_settings?: Record<string, any>
  remediation_steps?: string[]
  created_at: string
}

export interface ConfigTemplate {
  id: number
  name: string
  description?: string
  config_type: ConfigType
  template_data: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SecurityScore {
  configuration_id: number
  security_score: number
  total_findings: number
  critical_findings: number
  high_findings: number
  medium_findings: number
  low_findings: number
}

export interface GAMExtractRequest {
  config_types: ConfigType[]
  save_as_template: boolean
  template_name?: string
}

export interface GAMExtractResponse {
  success: boolean
  message: string
  configuration_id?: number
  extracted_types: ConfigType[]
  total_items: number
}

