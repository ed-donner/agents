"use client"

import { useState } from "react"
import { useSession } from "next-auth/react"
import { Campaign, Platform } from "@/types"
import { createCampaign, getCampaigns } from "@/lib/api"
import { formatDistanceToNow } from "date-fns"
import { Loader2, Plus, Megaphone, RefreshCw } from "lucide-react"
import clsx from "clsx"

const ALL_PLATFORMS: Platform[] = ["linkedin", "twitter", "instagram"]

interface Props { initialCampaigns: Campaign[] }

export function CampaignsClient({ initialCampaigns }: Props) {
  const { data: session } = useSession()
  const [campaigns, setCampaigns] = useState<Campaign[]>(initialCampaigns)
  const [showForm, setShowForm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [result, setResult] = useState("")

  // Form state
  const [name, setName] = useState("")
  const [objective, setObjective] = useState("")
  const [platforms, setPlatforms] = useState<Platform[]>(["linkedin", "twitter", "instagram"])
  const [duration, setDuration] = useState(14)

  const token = session?.backendToken ?? ""

  function togglePlatform(p: Platform) {
    setPlatforms((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    )
  }

  async function handleRefresh() {
    setRefreshing(true)
    const fresh = await getCampaigns(token).catch(() => campaigns)
    setCampaigns(fresh)
    setRefreshing(false)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token || platforms.length === 0) return
    setLoading(true)
    setResult("")
    try {
      const res = await createCampaign(token, { name, objective, platforms, duration_days: duration })
      setResult(res.result ?? "Campaign created!")
      await handleRefresh()
      setShowForm(false)
      setName(""); setObjective("")
    } catch (err: unknown) {
      setResult(err instanceof Error ? err.message : "Failed to create campaign")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
          <p className="mt-1 text-sm text-gray-500">
            AI-planned multi-platform content campaigns
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleRefresh} disabled={refreshing} className="btn-secondary">
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          </button>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            <Plus className="h-4 w-4" />
            New Campaign
          </button>
        </div>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="card border-brand-200 bg-brand-50">
          <h2 className="mb-4 text-sm font-semibold text-brand-800">
            Create Campaign — AI will generate the full content calendar
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">Campaign Name</label>
                <input
                  required
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  placeholder="e.g. Q3 SME Automation Push"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-gray-700">Duration (days)</label>
                <input
                  type="number"
                  min={7}
                  max={90}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">Objective</label>
              <textarea
                required
                rows={2}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                placeholder="e.g. Generate 30 qualified leads from Lagos-based SME owners interested in workflow automation"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-medium text-gray-700">Platforms</label>
              <div className="flex gap-3">
                {ALL_PLATFORMS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => togglePlatform(p)}
                    className={clsx(
                      "rounded-lg border px-3 py-1.5 text-xs font-medium capitalize transition-colors",
                      platforms.includes(p)
                        ? "border-brand-600 bg-brand-600 text-white"
                        : "border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
                    )}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" disabled={loading || platforms.length === 0} className="btn-primary">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                {loading ? "Creating Campaign…" : "Create & Generate Plan"}
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
          {result && (
            <pre className="mt-4 max-h-64 overflow-y-auto rounded-lg border border-gray-200 bg-white p-3 text-xs text-gray-700 whitespace-pre-wrap">
              {result}
            </pre>
          )}
        </div>
      )}

      {/* Campaign list */}
      {campaigns.length === 0 ? (
        <div className="card py-16 text-center">
          <Megaphone className="mx-auto h-10 w-10 text-gray-300" />
          <p className="mt-3 text-sm text-gray-400">No campaigns yet. Create your first one.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {campaigns.map((c) => (
            <CampaignCard key={c.id} campaign={c} />
          ))}
        </div>
      )}
    </div>
  )
}

function CampaignCard({ campaign }: { campaign: Campaign }) {
  const age = formatDistanceToNow(new Date(campaign.created_at), { addSuffix: true })
  return (
    <div className="card flex items-start justify-between gap-4">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900 truncate">{campaign.name}</h3>
          <span className={clsx(
            "badge capitalize",
            campaign.status === "active" ? "bg-green-50 text-green-700" :
            campaign.status === "paused" ? "bg-yellow-50 text-yellow-700" :
            "bg-gray-100 text-gray-600"
          )}>
            {campaign.status}
          </span>
        </div>
        <p className="mt-1 text-sm text-gray-500 line-clamp-1">{campaign.objective}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {campaign.platforms.map((p) => (
            <span key={p} className="badge bg-gray-100 text-gray-600 capitalize">{p}</span>
          ))}
          <span className="text-xs text-gray-400">{campaign.duration_days} days</span>
          <span className="text-xs text-gray-400">· {age}</span>
        </div>
      </div>
    </div>
  )
}
