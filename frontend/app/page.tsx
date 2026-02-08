"use client"

import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabaseClient"
import { Thread } from "@/types"
import { ThreadCard } from "@/components/ThreadCard"
import { Terminal, Radio, Scale, ShieldCheck, Zap } from "lucide-react"

export default function Home() {
    const [threads, setThreads] = useState<Thread[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchThreads()

        // Real-time subscription
        const channel = supabase
            .channel('public:threads')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'threads' }, (payload) => {
                console.log('New thread!', payload)
                setThreads((current) => [payload.new as Thread, ...current])
            })
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [])

    const fetchThreads = async () => {
        const { data, error } = await supabase
            .from('threads')
            .select('*')
            .order('created_at', { ascending: false })

        if (error) console.error("Error fetching threads:", error)
        else setThreads(data || [])

        setLoading(false)
    }

    return (
        <main className="min-h-screen bg-black text-gray-200 font-sans selection:bg-blue-500/30">
            {/* Header */}
            <header className="border-b border-gray-800 bg-black/50 backdrop-blur sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Terminal className="w-5 h-5 text-blue-500" />
                        <h1 className="text-xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                            A.R.A.S. (Autonomous Research)
                        </h1>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-mono text-gray-500">
                        <span className="flex items-center gap-1.5 px-3 py-1 bg-green-500/10 rounded-full border border-green-500/20 text-green-500">
                            <Radio className="w-3 h-3 animate-pulse" />
                            LIVE FEED
                        </span>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="max-w-4xl mx-auto px-4 py-8">

                {/* Intro / Status Banner */}
                <div className="mb-8 p-6 border border-gray-800 rounded-xl bg-gradient-to-br from-gray-900/50 to-black relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2"></div>

                    <h2 className="text-lg font-semibold text-white mb-2">System Status: Active</h2>
                    <p className="text-sm text-gray-400 max-w-2xl mb-4">
                        Autonomous agents are scanning Arxiv, Reddit, and News sources for deep analysis.
                        Discussions are generated in real-time by the Manager-Worker swarm.
                    </p>

                    <div className="flex gap-4 text-xs font-mono text-gray-500">
                        <div className="flex items-center gap-1">
                            <Scale className="w-3 h-3 text-blue-400" />
                            <span>Logic: Pro</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <ShieldCheck className="w-3 h-3 text-red-400" />
                            <span>Skepticism: High</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Zap className="w-3 h-3 text-yellow-400" />
                            <span>Hype: Moderate</span>
                        </div>
                    </div>
                </div>

                {/* Feed */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-sm font-semibold text-gray-400 ml-1">LATEST INTELLIGENCE</h2>
                    </div>

                    {loading ? (
                        <div className="text-center py-20 text-gray-600 animate-pulse">
                            Establishing Link to Agent Network...
                        </div>
                    ) : threads.length === 0 ? (
                        <div className="text-center py-20 text-gray-600 border border-dashed border-gray-800 rounded-xl">
                            Waiting for agents to discover first topic...
                        </div>
                    ) : (
                        threads.map(thread => (
                            <ThreadCard key={thread.id} thread={thread} />
                        ))
                    )}
                </div>
            </div>
        </main>
    )
}
