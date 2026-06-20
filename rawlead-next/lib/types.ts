export type Source = 'fl' | 'kwork' | 'youdo' | 'tg' | 'freelance-ru' | 'freelancejob' | 'pchyol'

export interface LeadItem {
  id: number
  source: Source
  title: string
  body: string
  task_summary: string
  url: string
  budget_text: string | null
  ai_score: number
  keyword_match: number | null
  final_rank: number
  category: string
  lead_tags: string[]
  lead_tag_labels: Record<string, string>
  tools_required: string[]
  difficulty: string | null
  tz_attachment: object | null
  created_at: string
  is_hot: boolean
  display_views: number
  display_replies: number
  reply_draft: string
  replied_at?: string
}

export interface FeedResponse {
  items: LeadItem[]
  limit: number
  offset: number
  count: number
  today_count: number
  sort: string
  min_match: number
  skills: string[]
  category: string[]
  source: string[]
  feed_delayed: boolean
}

export interface UserProfile {
  user_id: string
  tg_user_id: number
  username: string
  first_name: string
  avatar_url: string
  has_avatar: boolean
  can_ops_admin: boolean
}

export interface UserTags {
  tags: string[]
  weights: Record<string, number>
}

export interface BotSessionResponse {
  auth_token: string
  deep_link: string
  expires_at: string
}

export interface BotCompleteResponse {
  access_token: string
  token_type: string
  user_id: string
  tg_user_id: number
  username: string
  first_name: string
  avatar_url: string
  has_avatar: boolean
}

export interface DraftResponse {
  status: 'ready' | 'pending' | 'failed'
  lead_id: number
  reply_draft?: string
  tools_required?: string[]
  keyword_match?: number
  queued?: boolean
  queue_ahead?: number
  error?: string
}

export interface DraftQuota {
  draft_hourly_limit: number
  draft_used: number
  draft_remaining: number
  draft_retry_after_sec: number
}

export interface SubscriptionStatus {
  plan: 'free' | 'trial' | 'agent' | 'pro' | 'owner'
  plan_label: string
  is_active: boolean
  active_until?: string
  status: string
  effective_access: boolean
  yookassa_available: boolean
  trial_used?: boolean
  trial_used_at?: string | null
  has_prepaid?: boolean
  prepaid_active_until?: string | null
}

export interface SiteStats {
  radar_online: boolean
  leads_week: number
  leads_week_display: string
}

export interface QuizCard {
  id: string
  title: string
  body: string
  tags: string[]
  source?: string
  category?: string
  budget_text?: string
  complexity?: number
}

export interface HistoryEntry {
  card_id: string
  liked: boolean
  tags: string[]
  complexity?: number
}

export interface QuizNextResponse {
  done: boolean
  card?: QuizCard
  profile?: {
    tags: Record<string, number>
    niches: string[]
    leads_per_week: number
  }
}

export interface NotificationSettings {
  threshold: 60 | 80 | 100
  push_enabled: boolean
}
