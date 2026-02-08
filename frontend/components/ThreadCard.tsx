import { Thread } from "@/types"
import { formatDistanceToNow } from "date-fns"
import Link from "next/link"

interface ThreadCardProps {
    thread: Thread
}

export function ThreadCard({ thread }: ThreadCardProps) {
    return (
        <Link href={`/thread/${thread.id}`}>
            <div className="border border-gray-800 bg-gray-900/50 rounded-lg p-5 hover:bg-gray-900 transition-all cursor-pointer group shadow-lg hover:shadow-blue-500/10">
                <div className="flex justify-between items-start mb-3">
                    <h3 className="text-xl font-bold text-gray-100 group-hover:text-blue-400 transition-colors">
                        {thread.topic_title}
                    </h3>
                    <span className="text-xs text-gray-500 font-mono">
                        {formatDistanceToNow(new Date(thread.created_at), { addSuffix: true })}
                    </span>
                </div>
                <p className="text-gray-400 text-sm line-clamp-3 mb-4 leading-relaxed">
                    {thread.summary}
                </p>
                <div className="flex items-center gap-2 text-xs text-blue-300/60 font-mono">
                    <span className="px-2 py-1 bg-blue-500/10 rounded border border-blue-500/20">Analysis</span>
                    <span className="px-2 py-1 bg-purple-500/10 rounded border border-purple-500/20">Deep Research</span>
                </div>
            </div>
        </Link>
    )
}
