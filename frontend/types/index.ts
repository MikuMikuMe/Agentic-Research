export interface Thread {
    id: string
    topic_title: string
    summary: string
    research_brief: string
    created_at: string
}

export interface Comment {
    id: string
    thread_id: string
    agent_persona: 'Aggregator' | 'Skeptic' | 'Hype' | 'Researcher'
    content: string
    created_at: string
}

export type AgentPersona = Comment['agent_persona']
