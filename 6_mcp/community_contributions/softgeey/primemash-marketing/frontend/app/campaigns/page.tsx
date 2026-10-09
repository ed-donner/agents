import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/authOptions"
import { getCampaigns } from "@/lib/api"
import { CampaignsClient } from "./CampaignsClient"

// Always fetch fresh data
export const dynamic = "force-dynamic"
export const revalidate = 0

export default async function CampaignsPage() {
  const session = await getServerSession(authOptions)
  const token = session!.backendToken
  const campaigns = await getCampaigns(token).catch(() => [])
  return <CampaignsClient initialCampaigns={campaigns} />
}
