import { useState, useEffect } from 'react'

export interface Artifact {
  id: string
  name: string
  agent: string
  status: 'pending' | 'wip' | 'completed' | 'error'
  createdAt: string
  size: number
  content?: string
}

export function useArtifacts() {
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchArtifacts = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/artifacts')
      if (!response.ok) {
        throw new Error(`Failed to fetch artifacts: ${response.statusText}`)
      }
      const data = await response.json()
      setArtifacts(data.artifacts || [])
      setError(null)
    } catch (err) {
      console.error('Error fetching artifacts:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch artifacts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchArtifacts()
    // Refresh every 5 seconds to show real-time updates
    const interval = setInterval(fetchArtifacts, 5000)
    return () => clearInterval(interval)
  }, [])

  return {
    artifacts,
    loading,
    error,
    refresh: fetchArtifacts
  }
}

export async function getArtifactContent(artifactId: string): Promise<string> {
  const response = await fetch(`http://localhost:8000/api/artifacts/${artifactId}`)
  if (!response.ok) {
    throw new Error(`Failed to fetch artifact content: ${response.statusText}`)
  }
  const data = await response.json()
  return data.content
}