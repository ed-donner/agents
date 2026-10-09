export type Platform = "linkedin" | "twitter" | "instagram"

export type PostStatus = "draft" | "scheduled" | "published" | "failed"

export interface Post {
  id: string
  platform: Platform
  content: string
  content_type: string
  status: PostStatus
  scheduled_at: string | null
  published_at: string | null
  platform_post_id: string | null
  campaign_id: string | null
  error_message: string | null
  metadata: Record<string, unknown>
  created_at: string
}

export interface Campaign {
  id: string
  name: string
  objective: string
  platforms: Platform[]
  duration_days: number
  status: "active" | "paused" | "completed"
  created_at: string
}

export interface AnalyticsSummary {
  total_posts: number
  by_platform: Record<string, number>
  by_status: Record<string, number>
}

export interface AgentTaskResult {
  success: boolean
  result?: string
  error?: string
}

// Extend next-auth Session type
declare module "next-auth" {
  interface Session {
    backendToken: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    backendToken?: string
  }
}
