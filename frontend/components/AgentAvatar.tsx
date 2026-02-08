import { Bot, Zap, Search, AlertTriangle, User, Mic2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface AgentAvatarProps {
    role: string
    name: string
    className?: string
}

export function AgentAvatar({ role, name, className }: AgentAvatarProps) {
    // Map roles to specific visual styles
    const config: Record<string, { icon: any, color: string, text: string }> = {
        "Host": { icon: Mic2, color: "bg-gray-700", text: "text-gray-100" },
        "Manager": { icon: Bot, color: "bg-gray-700", text: "text-gray-100" },
        "Skeptic": { icon: AlertTriangle, color: "bg-red-500/20", text: "text-red-400" },
        "Hype": { icon: Zap, color: "bg-yellow-500/20", text: "text-yellow-400" },
        "Researcher": { icon: Search, color: "bg-blue-500/20", text: "text-blue-400" },
        "Analyst": { icon: User, color: "bg-purple-500/20", text: "text-purple-400" }
    }

    // Default or matched config
    const style = config[role] || { icon: Bot, color: "bg-gray-800", text: "text-gray-400" }
    const Icon = style.icon

    return (
        <div className={cn("flex items-center justify-center w-10 h-10 rounded-full border border-white/5", style.color, className)} title={role}>
            <Icon className={cn("w-5 h-5", style.text)} />
        </div>
    )
}
