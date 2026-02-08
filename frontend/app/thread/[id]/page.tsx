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
                <div className="space-y-8 relative">
                    {/* Connecting Line */}
                    <div className="absolute left-5 top-12 bottom-0 w-px bg-gradient-to-b from-gray-800 to-transparent -z-10"></div>

                    <h2 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-8 sticky top-16 bg-black/90 py-2 z-10 backdrop-blur w-fit pr-4">
                        Roundtable In Progress
                    </h2>

                    {comments.map((comment, i) => {
                        // Parse Role from content: "**[Role]** Content..."
                        const match = comment.content.match(/^\*\*\[(.*?)\]\*\*\s*(.*)/s)
                        const role = match ? match[1] : "Unknown"
                        const content = match ? match[2] : comment.content
                        const isSystem = role === "Manager" || role === "Host"

                        return (
                            <div key={comment.id} className={`flex gap-4 group ${isSystem ? 'opacity-75' : ''}`}>
                                <div className="flex-shrink-0 mt-1 relative">
                                    <AgentAvatar role={role} name={comment.agent_persona} />
                                </div>
                                <div className="flex-1 space-y-2">
                                    <div className="flex items-baseline gap-2">
                                        <span className="text-base font-bold text-gray-100">
                                            {comment.agent_persona}
                                        </span>
                                        <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
                                            {role}
                                        </span>
                                        <span className="text-xs text-gray-600 font-mono ml-auto">
                                            {new Date(comment.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>

                                    <div className={`prose prose-invert prose-sm max-w-none text-gray-300 p-4 rounded-xl border transition-all
                                        ${isSystem
                                            ? 'bg-transparent border-transparent italic text-gray-500 pl-0'
                                            : 'bg-gray-900/40 border-gray-800 hover:border-gray-700 hover:bg-gray-900/60 shadow-sm'
                                        }`}>
                                        <ReactMarkdown>{content}</ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
