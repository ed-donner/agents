import type { Metadata } from "next"
import "./globals.css"
import { AuthProvider } from "@/components/layout/AuthProvider"

export const metadata: Metadata = {
  title: "Primemash Marketing Hub",
  description: "Autonomous Digital Marketing Agent System",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, -apple-system, sans-serif" }}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
