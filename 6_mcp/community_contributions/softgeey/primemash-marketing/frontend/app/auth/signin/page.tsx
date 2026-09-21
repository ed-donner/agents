"use client"

import { signIn } from "next-auth/react"
import { useState } from "react"

export default function SignInPage() {
  const [loading, setLoading] = useState(false)

  async function handleSignIn() {
    setLoading(true)
    await signIn("google", { callbackUrl: "/dashboard" })
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-900 via-brand-700 to-brand-500">
      <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-2xl">
        {/* Logo / Brand */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-brand-600">
            <span className="text-2xl font-bold text-white">P</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Primemash</h1>
          <p className="mt-1 text-sm text-gray-500">Marketing Hub</p>
        </div>

        <p className="mb-6 text-center text-sm text-gray-600">
          Sign in to manage your autonomous marketing agents
        </p>

        <button
          onClick={handleSignIn}
          disabled={loading}
          className="btn-primary w-full justify-center py-3 text-base"
        >
          {loading ? (
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            <GoogleIcon />
          )}
          {loading ? "Signing in…" : "Continue with Google"}
        </button>

        <p className="mt-6 text-center text-xs text-gray-400">
          Automating African Businesses, Amplifying Growth
        </p>
      </div>
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  )
}
