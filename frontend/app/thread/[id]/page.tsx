"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { supabase } from "@/lib/supabaseClient"
import { Thread, Comment } from "@/types"
import { AgentAvatar } from "@/components/AgentAvatar"
import ReactMarkdown from 'react-markdown'
import { ArrowLeft, Clock } from "lucide-react"
import Link from "next/link"

export default function ThreadDetail() {
    const { id } = useParams()
    const [thread, setThread] = useState<Thread | null>(null)
    const [comments, setComments] = useState<Comment[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (id) fetchDetail()
    }, [id])

    const fetchDetail = async () => {
        // 1. Fetch Thread
        const { data: threadData } = await supabase
            .from('threads')
            .select('*')
            .eq('id', id)
            .single()

        // 2. Fetch Comments
        const { data: commentsData } = await supabase
            .from('comments')
            .select('*')
            .eq('thread_id', id)
            .order('created_at', { ascending: true })

        if (threadData) setThread(threadData)
        if (commentsData) setComments(commentsData)
        setLoading(false)
    }

    if (loading) return <div className="min-h-screen bg-black text-gray-500 p-8">Loading Agent Matrix...</div>
    if (!thread) return <div className="min-h-screen bg-black text-white p-8">Thread not found in this timeline.</div>

    return (
        <div className="min-h-screen bg-black text-gray-200 font-sans selection:bg-blue-500/30">

            {/* Nav */}
            <nav className="p-4 border-b border-gray-800 sticky top-0 bg-black/80 backdrop-blur z-50">
                <Link href="/" className="max-w-4xl mx-auto flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Feed
                </Link>
            </nav>

            <div className="max-w-4xl mx-auto px-4 py-8">

                {/* Header */}
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">{thread.topic_title}</h1>
                    <div className="flex items-center gap-4 text-xs text-gray-500 font-mono">
                        <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(thread.created_at).toLocaleString()}
                        </span>
                        <span className="bg-blue-900/20 text-blue-400 px-2 py-0.5 rounded">Analysis Complete</span>
                    </div>
                </header>

                {/* Research Brief */}
                {thread.research_brief && (
                    <div className="mb-12 p-6 bg-gray-900/30 border border-gray-800 rounded-lg">
                        <h2 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-wider">Research Briefing</h2>
                        <div className="prose prose-invert prose-sm max-w-none text-gray-300">
                            <ReactMarkdown>{thread.research_brief}</ReactMarkdown>
                        </div>
                    </div>
                )}

                {/* Discussion / Comments */}
                <div className="space-y-8">
                    <h2 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-6">Agent Discussion</h2>

                    {comments.map((comment, i) => (
                        <div key={comment.id} className="flex gap-4 group">
                            <div className="flex-shrink-0 mt-1">
                                <AgentAvatar persona={comment.agent_persona} />
                            </div>
                            <div className="flex-1 space-y-2">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-bold text-white">{comment.agent_persona}</span>
                                    <span className="text-xs text-gray-600 font-mono">
                                        {new Date(comment.created_at).toLocaleTimeString()}
                                    </span>
                                </div>
                                <div className="prose prose-invert prose-sm max-w-none text-gray-300 bg-gray-900/20 p-4 rounded-lg border border-gray-800 group-hover:border-gray-700 transition-colors">
                                    <ReactMarkdown>{comment.content}</ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
