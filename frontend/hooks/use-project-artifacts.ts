/**
 * Project-specific artifacts hook
 * Fetches and manages artifacts for a specific project
 */

import { useState, useEffect } from 'react';
import { artifactsService, ArtifactSummary, ProjectArtifact } from '@/lib/services/api/artifacts.service';

export interface UseProjectArtifactsReturn {
  artifacts: ProjectArtifact[];
  summary: ArtifactSummary | null;
  loading: boolean;
  error: string | null;
  progress: number;
  refresh: () => Promise<void>;
  generateArtifacts: () => Promise<void>;
  downloadArtifacts: () => Promise<void>;
}

export function useProjectArtifacts(projectId: string): UseProjectArtifactsReturn {
  const [summary, setSummary] = useState<ArtifactSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchArtifacts = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await artifactsService.getProjectArtifacts(projectId);

      if (response.success && response.data) {
        setSummary(response.data);
      } else {
        setError(response.error || 'Failed to fetch project artifacts');
      }
    } catch (err) {
      console.error('Error fetching project artifacts:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch project artifacts');
    } finally {
      setLoading(false);
    }
  };

  const generateArtifacts = async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);

      const response = await artifactsService.generateProjectArtifacts(projectId, {
        force_regenerate: false,
        include_source: true
      });

      if (response.success) {
        // Refresh artifacts after generation
        await fetchArtifacts();
      } else {
        setError(response.error || 'Failed to generate artifacts');
      }
    } catch (err) {
      console.error('Error generating artifacts:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate artifacts');
    } finally {
      setLoading(false);
    }
  };

  const downloadArtifacts = async () => {
    if (!projectId) return;

    try {
      setError(null);

      const response = await artifactsService.downloadProjectArtifacts(projectId);

      if (response.success && response.data) {
        // Create download link
        const url = window.URL.createObjectURL(response.data);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${projectId}-artifacts.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        setError(response.error || 'Failed to download artifacts');
      }
    } catch (err) {
      console.error('Error downloading artifacts:', err);
      setError(err instanceof Error ? err.message : 'Failed to download artifacts');
    }
  };

  useEffect(() => {
    if (projectId) {
      fetchArtifacts();

      // Refresh every 30 seconds for real-time updates
      const interval = setInterval(fetchArtifacts, 30000);
      return () => clearInterval(interval);
    }
  }, [projectId]);

  // Calculate progress based on completed artifacts
  const progress = summary ?
    summary.artifacts.length > 0
      ? (summary.artifacts.filter(a => a.status === 'completed').length / summary.artifacts.length) * 100
      : 0
    : 0;

  return {
    artifacts: summary?.artifacts || [],
    summary,
    loading,
    error,
    progress,
    refresh: fetchArtifacts,
    generateArtifacts,
    downloadArtifacts,
  };
}