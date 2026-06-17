import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/authOptions"
import { getAnalytics } from "@/lib/api"
import { AnalyticsClient } from "./AnalyticsClient"

// Always fetch fresh data
export const dynamic = "force-dynamic"
export const revalidate = 0

export default async function AnalyticsPage() {
  const session = await getServerSession(authOptions)
  const token = session!.backendToken
  const analytics = await getAnalytics(token).catch(() => ({
    total_posts: 0,
    by_platform: {},
    by_status: {},
  }))
  return <AnalyticsClient analytics={analytics} />
}
