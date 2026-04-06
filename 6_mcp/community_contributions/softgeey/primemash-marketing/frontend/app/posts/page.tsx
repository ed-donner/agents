import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/authOptions"
import { getPosts } from "@/lib/api"
import { PostsClient } from "./PostsClient"

// Always fetch fresh data
export const dynamic = "force-dynamic"
export const revalidate = 0

export default async function PostsPage() {
  const session = await getServerSession(authOptions)
  const token = session!.backendToken
  const posts = await getPosts(token, 100).catch(() => [])
  return <PostsClient initialPosts={posts} />
}
