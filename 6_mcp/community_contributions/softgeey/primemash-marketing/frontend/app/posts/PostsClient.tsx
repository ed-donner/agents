"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useSession } from "next-auth/react"
import { Post, Platform } from "@/types"
import { generateContent, getPosts } from "@/lib/api"
import { PostCard } from "@/components/ui/PostCard"
import { Loader2, Plus, RefreshCw } from "lucide-react"

const PLATFORMS: Platform[] = ["linkedin", "twitter", "instagram"]

const CONTENT_TYPES: Record<Platform, string[]> = {
  linkedin:  ["educational", "case_study", "thought_leadership", "social_proof", "product_showcase", "motivation_and_tips"],
  twitter:   ["tip", "stat", "question", "thread_opener", "hot_take"],
  instagram: ["before_after", "client_spotlight", "quick_tip", "behind_scenes"],
}

interface Props { initialPosts: Post[] }

export function PostsClient({ initialPosts }: Props) {
  const { data: session } = useSession()
  const [posts, setPosts] = useState<Post[]>(initialPosts)
  const [filterPlatform, setFilterPlatform] = useState<string>("all")
  const [filterStatus, setFilterStatus] = useState<string>("all")
  const [showForm, setShowForm] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [msg, setMsg] = useState("")

  // Generate form state
  const [platform, setPlatform] = useState<Platform>("linkedin")
  const [contentType, setContentType] = useState("educational")
  const [topic, setTopic] = useState("")

  const router = useRouter()
  const token = session?.backendToken ?? ""

  function handleRefresh() {
    setRefreshing(true)
    router.refresh()
    setTimeout(() => setRefreshing(false), 1000)
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    if (!token) return
    setGenerating(true)
    setMsg("")
    try {
      const res = await generateContent(token, platform, contentType, topic || undefined)
      setMsg(res.result ?? "Post generated and saved as draft.")
      await handleRefresh()
      setShowForm(false)
      setTopic("")
    } catch (err: unknown) {
      setMsg(err instanceof Error ? err.message : "Generation failed")
    } finally {
      setGenerating(false)
    }
  }

  const filtered = posts.filter((p) => {
    const platOk = filterPlatform === "all" || p.platform === filterPlatform
    const statOk = filterStatus === "all" || p.status === filterStatus
    return platOk && statOk
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Posts</h1>
          <p className="mt-1 text-sm text-gray-500">{posts.length} total posts</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleRefresh} disabled={refreshing} className="btn-secondary">
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            <Plus className="h-4 w-4" />
            Generate Post
          </button>
        </div>
      </div>

      {/* Generate form */}
      {showForm && (
        <div className="card border-brand-200 bg-brand-50">
          <h2 className="mb-4 text-sm font-semibold text-brand-800">Generate New Post (AI)</h2>
          <form onSubmit={handleGenerate} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">Platform</label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={platform}
                onChange={(e) => {
                  const p = e.target.value as Platform
                  setPlatform(p)
                  setContentType(CONTENT_TYPES[p][0])
                }}
              >
                {PLATFORMS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">Content Type</label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                value={contentType}
                onChange={(e) => setContentType(e.target.value)}
              >
                {CONTENT_TYPES[platform].map((t) => (
                  <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">Topic (optional)</label>
              <input
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="e.g. WhatsApp automation for retail"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              />
            </div>
            <div className="sm:col-span-3 flex gap-2">
              <button type="submit" disabled={generating} className="btn-primary">
                {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                {generating ? "Generating…" : "Generate & Save Draft"}
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
          {msg && (
            <p className="mt-3 rounded-lg bg-white p-3 text-xs text-gray-700 border border-gray-200 whitespace-pre-wrap">
              {msg}
            </p>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Platform:</label>
          {["all", ...PLATFORMS].map((p) => (
            <button
              key={p}
              onClick={() => setFilterPlatform(p)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                filterPlatform === p
                  ? "bg-brand-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500">Status:</label>
          {["all", "draft", "scheduled", "published", "failed"].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                filterStatus === s
                  ? "bg-brand-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Posts list */}
      {filtered.length === 0 ? (
        <div className="card py-12 text-center text-sm text-gray-400">
          No posts match your filters.
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  )
}
