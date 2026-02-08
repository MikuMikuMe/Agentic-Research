"use client"

import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabaseClient"
import { Thread } from "@/types"
import { ThreadCard } from "@/components/ThreadCard"
import { Sparkles, Terminal } from "lucide-react"

export default function Home() {
    const [threads, setThreads] = useState<Thread[]>([])
    const [loading, setLoading] = useState(true)
    const [researchTopic, setResearchTopic] = useState("")
    const [triggering, setTriggering] = useState(false)

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

    const handleResearch = async () => {
        if (!researchTopic) return
        setTriggering(true)
        try {
            const res = await fetch(`/api/research`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: researchTopic })
            })
            const data = await res.json()
            if (data.status === 'success') {
                alert("Research Complete! Thread created.")
                setResearchTopic("")
            } else {
                alert(`Research status: ${data.status} - ${data.message}`)
            }
        } catch (e) {
            console.error(e)
            alert("Failed to trigger research")
        }
        setTriggering(false)
    }

    return (
        <main className="min-h-screen bg-black text-gray-200 font-sans selection:bg-blue-500/30">
            {/* Header */}
            <header className="border-b border-gray-800 bg-black/50 backdrop-blur sticky top-0 z-50">
                <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Terminal className="w-5 h-5 text-blue-500" />
                        <h1 className="text-xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                            Agentic Research
                        </h1>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-mono text-gray-500">
                        <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            Agents Online
                        </span>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="max-w-4xl mx-auto px-4 py-8">

                {/* Research Trigger (For Demo) */}
                <div className="mb-8 p-4 border border-gray-800 rounded-xl bg-gray-900/30">
                    <label className="block text-xs font-mono text-gray-500 mb-2">TRIGGER NEW RESEARCH (DEBUG)</label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={researchTopic}
                            onChange={(e) => setResearchTopic(e.target.value)}
                            placeholder="Enter a topic (e.g. 'Reasoning Models in 2024')"
                            className="flex-1 bg-black border border-gray-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                        />
                        <button
                            onClick={handleResearch}
                            disabled={triggering}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {triggering ? <Sparkles className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                            {triggering ? "Researching..." : "Ignite"}
                        </button>
                    </div>
                </div>

                {/* Feed */}
                <div className="space-y-4">
                    <h2 className="text-sm font-semibold text-gray-400 mb-4 ml-1">LATEST DISCUSSIONS</h2>
                    {loading ? (
                        <div className="text-center py-20 text-gray-600 animate-pulse">
                            Connectng to Agent Swarm...
                        </div>
                    ) : threads.length === 0 ? (
                        <div className="text-center py-20 text-gray-600">
                            No discussions yet. Trigger one above.
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
