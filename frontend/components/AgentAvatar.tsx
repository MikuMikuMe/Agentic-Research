import { AgentPersona } from "@/types"
import { Bot, Zap, Search, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"

interface AgentAvatarProps {
    persona: AgentPersona
    className?: string
}

export function AgentAvatar({ persona, className }: AgentAvatarProps) {
    const config = {
        Aggregator: { icon: Bot, color: "bg-blue-500", text: "text-blue-100" },
        Skeptic: { icon: AlertTriangle, color: "bg-red-500", text: "text-red-100" },
        Hype: { icon: Zap, color: "bg-green-500", text: "text-green-100" },
        Researcher: { icon: Search, color: "bg-purple-500", text: "text-purple-100" }
    }

    const { icon: Icon, color, text } = config[persona] || config.Aggregator

    return (
        <div className={cn("flex items-center justify-center p-2 rounded-full", color, className)}>
            <Icon className={cn("w-5 h-5", text)} />
        </div>
    )
}
