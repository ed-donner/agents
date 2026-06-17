interface Props {
  label: string
  value: number
  icon: React.ReactNode
  color?: "blue" | "green" | "yellow" | "red"
}

export function StatCard({ label, value, icon }: Props) {
  return (
    <div className="card flex items-center gap-3">
      <div className="rounded-lg bg-gray-50 p-2">{icon}</div>
      <div>
        <p className="text-xl font-bold text-gray-900">{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  )
}
