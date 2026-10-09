"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { signOut, useSession } from "next-auth/react"
import {
  LayoutDashboard,
  FileText,
  Megaphone,
  BarChart2,
  Bot,
  LogOut,
  Zap,
} from "lucide-react"
import clsx from "clsx"

const navItems = [
  { label: "Dashboard",  href: "/dashboard",   icon: LayoutDashboard },
  { label: "Posts",      href: "/posts",        icon: FileText },
  { label: "Campaigns",  href: "/campaigns",    icon: Megaphone },
  { label: "Analytics",  href: "/analytics",    icon: BarChart2 },
  { label: "Agent",      href: "/agent",        icon: Bot },
]

export function Sidebar() {
  const pathname = usePathname()
  const { data: session } = useSession()

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-gray-200 bg-white">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-gray-100">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600">
          <Zap className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-gray-900">Primemash</p>
          <p className="text-xs text-gray-400">Marketing Hub</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map(({ label, href, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              pathname.startsWith(href)
                ? "bg-brand-50 text-brand-700"
                : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        ))}
      </nav>

      {/* User */}
      <div className="border-t border-gray-100 p-3">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2">
          {session?.user?.image && (
            <img
              src={session.user.image}
              alt="avatar"
              className="h-7 w-7 rounded-full"
            />
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-gray-900">
              {session?.user?.name}
            </p>
            <p className="truncate text-xs text-gray-400">{session?.user?.email}</p>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/auth/signin" })}
            className="text-gray-400 hover:text-gray-600"
            title="Sign out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  )
}
