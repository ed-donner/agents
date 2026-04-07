"use client"

import { useState } from "react"
import { useSession } from "next-auth/react"
import { AnalyticsSummary } from "@/types"
import { getAnalyticsReport } from "@/lib/api"
import { StatCard } from "@/components/ui/StatCard"
import {
  BarChart2, FileText, CheckCircle, XCircle,
  Loader2, Sparkles, Clock,
} from "lucide-react"

interface Props { analytics: AnalyticsSummary }

const PLATFORM_COLORS: Record<string, string> = {
  linkedin: "bg-blue-500",
  twitter: "bg-sky-400",
  instagram: "bg-pink-500",
}

export function AnalyticsClient({ analytics }: Props) {
  const { data: session } = useSession()
  const [report, setReport] = useState("")
  const [loadingReport, setLoadingReport] = useState(false)

  async function handleGetReport() {
    if (!session?.backendToken) return
    setLoadingReport(true)
    setReport("")
    try {
      const r = await getAnalyticsReport(session.backendToken)
      setReport(r)
    } catch (err: unknown) {
      setReport(err instanceof Error ? err.message : "Failed to generate report")
    } finally {
      setLoadingReport(false)
    }
  }

  const published = analytics.by_status?.published ?? 0
  const failed    = analytics.by_status?.failed ?? 0
  const scheduled = analytics.by_status?.scheduled ?? 0
  const draft     = analytics.by_status?.draft ?? 0

  // Build platform bar data
  const platformEntries = Object.entries(analytics.by_platform)
  const maxPlatformCount = Math.max(...platformEntries.map(([, v]) => v), 1)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Performance overview across all platforms
          </p>
        </div>
        <button
          onClick={handleGetReport}
          disabled={loadingReport}
          className="btn-primary"
        >
          {loadingReport
            ? <Loader2 className="h-4 w-4 animate-spin" />
            : <Sparkles className="h-4 w-4" />}
          {loadingReport ? "Generating…" : "AI Report"}
        </button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total Posts"  value={analytics.total_posts} icon={<FileText className="h-5 w-5 text-brand-600" />} />
        <StatCard label="Published"    value={published}             icon={<CheckCircle className="h-5 w-5 text-green-500" />} />
        <StatCard label="Scheduled"    value={scheduled}             icon={<Clock className="h-5 w-5 text-blue-500" />} />
        <StatCard label="Failed"       value={failed}                icon={<XCircle className="h-5 w-5 text-red-500" />} />
      </div>

      {/* Platform breakdown */}
      <div className="card">
        <h2 className="mb-5 text-sm font-semibold text-gray-700 flex items-center gap-2">
          <BarChart2 className="h-4 w-4" /> Posts by Platform
        </h2>
        {platformEntries.length === 0 ? (
          <p className="text-sm text-gray-400">No data yet.</p>
        ) : (
          <div className="space-y-3">
            {platformEntries.map(([platform, count]) => (
              <div key={platform} className="flex items-center gap-3">
                <span className="w-20 text-sm capitalize text-gray-600">{platform}</span>
                <div className="flex-1 rounded-full bg-gray-100 h-4 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${PLATFORM_COLORS[platform] ?? "bg-gray-400"}`}
                    style={{ width: `${(count / maxPlatformCount) * 100}%` }}
                  />
                </div>
                <span className="w-8 text-right text-sm font-medium text-gray-900">{count}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Status breakdown */}
      <div className="card">
        <h2 className="mb-5 text-sm font-semibold text-gray-700">Posts by Status</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: "Draft",     count: draft,     color: "bg-gray-200 text-gray-700" },
            { label: "Scheduled", count: scheduled, color: "bg-blue-100 text-blue-700" },
            { label: "Published", count: published, color: "bg-green-100 text-green-700" },
            { label: "Failed",    count: failed,    color: "bg-red-100 text-red-700" },
          ].map(({ label, count, color }) => (
            <div key={label} className={`rounded-xl p-4 ${color}`}>
              <p className="text-2xl font-bold">{count}</p>
              <p className="text-xs font-medium mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* AI Report */}
      {report && (
        <div className="card border-brand-200">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-brand-600" />
            <h2 className="text-sm font-semibold text-brand-800">AI Analytics Report</h2>
          </div>
          <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
            {report}
          </div>
        </div>
      )}
    </div>
  )
}
