import { useState, useEffect } from 'react'

export interface Activity {
  id: string
  time: string
  actor: string
  action: string
  type: 'completed' | 'approved' | 'waiting' | 'error'
  artifact_id?: string
}

export function useActivities() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchActivities = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/activities')
      if (!response.ok) {
        throw new Error(`Failed to fetch activities: ${response.statusText}`)
      }
      const data = await response.json()
      setActivities(data.activities || [])
      setError(null)
    } catch (err) {
      console.error('Error fetching activities:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch activities')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchActivities()
    // Refresh every 10 seconds to show real-time updates
    const interval = setInterval(fetchActivities, 10000)
    return () => clearInterval(interval)
  }, [])

  return {
    activities,
    loading,
    error,
    refresh: fetchActivities
  }
}