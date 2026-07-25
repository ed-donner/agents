import { Post } from "@/types"
import { formatDistanceToNow } from "date-fns"
import clsx from "clsx"

const STATUS_STYLES: Record<string, string> = {
  published: "bg-green-50 text-green-700",
  scheduled: "bg-blue-50 text-blue-700",
  draft:     "bg-gray-100 text-gray-600",
  failed:    "bg-red-50 text-red-700",
}

const PLATFORM_STYLES: Record<string, string> = {
  linkedin:  "bg-blue-600 text-white",
  twitter:   "bg-sky-500 text-white",
  instagram: "bg-pink-500 text-white",
}

export function PostCard({ post }: { post: Post }) {
  const timeAgo = formatDistanceToNow(new Date(post.created_at), { addSuffix: true })

  return (
    <div className="card flex items-start gap-4">
      {/* Platform badge */}
      <span
        className={clsx(
          "mt-0.5 shrink-0 rounded-md px-2 py-0.5 text-xs font-semibold capitalize",
          PLATFORM_STYLES[post.platform] ?? "bg-gray-200 text-gray-700"
        )}
      >
        {post.platform}
      </span>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p className="line-clamp-2 text-sm text-gray-800">{post.content}</p>
        <div className="mt-1.5 flex items-center gap-3">
          <span
            className={clsx(
              "badge capitalize",
              STATUS_STYLES[post.status] ?? "bg-gray-100 text-gray-600"
            )}
          >
            {post.status}
          </span>
          <span className="text-xs text-gray-400">{post.content_type}</span>
          <span className="text-xs text-gray-400">{timeAgo}</span>
        </div>
        {post.error_message && (
          <p className="mt-1 text-xs text-red-500">{post.error_message}</p>
        )}
      </div>
    </div>
  )
}
