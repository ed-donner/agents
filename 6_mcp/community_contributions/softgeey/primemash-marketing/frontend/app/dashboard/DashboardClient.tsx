"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useSession } from "next-auth/react"
import { AnalyticsSummary, Post } from "@/types"
import { triggerDailyRun } from "@/lib/api"
import { PostCard } from "@/components/ui/PostCard"
import { StatCard } from "@/components/ui/StatCard"
import {
  Zap, FileText, CheckCircle, XCircle, Play, Loader2,
  Linkedin, Twitter, Instagram,
} from "lucide-react"

interface Props {
  recentPosts: Post[]
  analytics: AnalyticsSummary
  userName: string
}

export function DashboardClient({ recentPosts, analytics, userName }: Props) {
  const { data: session } = useSession()
  const router = useRouter()
  const [running, setRunning] = useState(false)
  const [runMsg, setRunMsg] = useState("")

  async function handleDailyRun() {
    if (!session?.backendToken) return
    setRunning(true)
    setRunMsg("")
    try {
      const res = await triggerDailyRun(session.backendToken)
      setRunMsg(res.message || "Daily run triggered! Refresh in a moment to see new posts.")
      setTimeout(() => router.refresh(), 5000)
    } catch (e: unknown) {
      setRunMsg(e instanceof Error ? e.message : "Error triggering run")
    } finally {
      setRunning(false)
    }
  }

  const published = analytics.by_status?.published ?? 0
  const failed = analytics.by_status?.failed ?? 0
  const draft = analytics.by_status?.draft ?? 0

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Good {getGreeting()}, {userName.split(" ")[0]} 👋
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Your autonomous marketing agents are standing by.
          </p>
        </div>
        <button
          onClick={handleDailyRun}
          disabled={running}
          className="btn-primary"
        >
          {running ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {running ? "Running…" : "Run Daily Posts"}
        </button>
      </div>

      {runMsg && (
        <div className="rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-700">
          {runMsg}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total Posts" value={analytics.total_posts} icon={<FileText className="h-5 w-5 text-brand-600" />} />
        <StatCard label="Published" value={published} icon={<CheckCircle className="h-5 w-5 text-green-500" />} color="green" />
        <StatCard label="Drafts" value={draft} icon={<Zap className="h-5 w-5 text-yellow-500" />} color="yellow" />
        <StatCard label="Failed" value={failed} icon={<XCircle className="h-5 w-5 text-red-500" />} color="red" />
      </div>

      {/* Platform breakdown */}
      <div className="card">
        <h2 className="mb-4 text-sm font-semibold text-gray-700">Posts by Platform</h2>
        <div className="flex gap-6">
          <PlatformStat
            icon={<Linkedin className="h-5 w-5 text-blue-600" />}
            label="LinkedIn"
            count={analytics.by_platform?.linkedin ?? 0}
          />
          <PlatformStat
            icon={<Twitter className="h-5 w-5 text-sky-500" />}
            label="X (Twitter)"
            count={analytics.by_platform?.twitter ?? 0}
          />
          <PlatformStat
            icon={<Instagram className="h-5 w-5 text-pink-500" />}
            label="Instagram"
            count={analytics.by_platform?.instagram ?? 0}
          />
        </div>
      </div>

      {/* Recent Posts */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Recent Posts</h2>
        {recentPosts.length === 0 ? (
          <div className="card text-center text-sm text-gray-400 py-10">
            No posts yet. Click <strong>Run Daily Posts</strong> to get started.
          </div>
        ) : (
          <div className="space-y-3">
            {recentPosts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function PlatformStat({ icon, label, count }: { icon: React.ReactNode; label: string; count: number }) {
  return (
    <div className="flex items-center gap-2">
      {icon}
      <div>
        <p className="text-lg font-bold text-gray-900">{count}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  )
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return "morning"
  if (h < 17) return "afternoon"
  return "evening"
}
