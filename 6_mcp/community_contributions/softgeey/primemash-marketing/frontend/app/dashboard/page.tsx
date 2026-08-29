import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/authOptions"
import { getPosts, getAnalytics } from "@/lib/api"
import { DashboardClient } from "./DashboardClient"

// Always fetch fresh data — never use cached response
export const dynamic = "force-dynamic"
export const revalidate = 0

export default async function DashboardPage() {
  const session = await getServerSession(authOptions)
  const token = session!.backendToken

  const [posts, analytics] = await Promise.allSettled([
    getPosts(token, 5),
    getAnalytics(token),
  ])

  return (
    <DashboardClient
      recentPosts={posts.status === "fulfilled" ? posts.value : []}
      analytics={
        analytics.status === "fulfilled"
          ? analytics.value
          : { total_posts: 0, by_platform: {}, by_status: {} }
      }
      userName={session?.user?.name ?? ""}
    />
  )
}
