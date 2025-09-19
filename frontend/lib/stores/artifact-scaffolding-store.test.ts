import { describe, it, expect, beforeEach } from 'vitest';
import { useArtifactScaffoldingStore, ScaffoldedArtifact } from './artifact-scaffolding-store';

describe('useArtifactScaffoldingStore', () => {
  beforeEach(() => {
    // Reset the store's state before each test
    useArtifactScaffoldingStore.getState().clearArtifacts();
  });

  it('should have a correct initial state', () => {
    const { artifacts } = useArtifactScaffoldingStore.getState();
    expect(artifacts).toEqual({});
  });

  it('should set artifacts', () => {
    const newArtifacts: ScaffoldedArtifact[] = [
      { id: '1', name: 'test.txt', stage: 'test', status: 'completed', progress: 100, session_id: 's1' },
    ];
    useArtifactScaffoldingStore.getState().setArtifacts(newArtifacts);
    const { artifacts } = useArtifactScaffoldingStore.getState();
    expect(Object.values(artifacts)).toHaveLength(1);
    expect(artifacts['1']).toEqual(newArtifacts[0]);
  });

  it('should create a scaffolded artifact', () => {
    const artifact: ScaffoldedArtifact = { id: '1', name: 'test.txt', stage: 'test', status: 'scaffolded', progress: 0, session_id: 's1' };
    useArtifactScaffoldingStore.getState().createScaffold(artifact);
    const { artifacts } = useArtifactScaffoldingStore.getState();
    expect(artifacts['1']).toEqual({
      ...artifact,
      status: 'scaffolded',
      progress: 0,
    });
  });

  it('should update artifact progress', () => {
    const artifact: ScaffoldedArtifact = { id: '1', name: 'test.txt', stage: 'test', status: 'scaffolded', progress: 0, session_id: 's1' };
    useArtifactScaffoldingStore.getState().setArtifacts([artifact]);
    useArtifactScaffoldingStore.getState().updateProgress('1', 50);
    const { artifacts } = useArtifactScaffoldingStore.getState();
    expect(artifacts['1'].progress).toBe(50);
    expect(artifacts['1'].status).toBe('in_progress');
  });

  it('should update artifact status to completed when progress is 100', () => {
    const artifact: ScaffoldedArtifact = { id: '1', name: 'test.txt', stage: 'test', status: 'in_progress', progress: 50, session_id: 's1' };
    useArtifactScaffoldingStore.getState().setArtifacts([artifact]);
    useArtifactScaffoldingStore.getState().updateProgress('1', 100);
    const { artifacts } = useArtifactScaffoldingStore.getState();
    expect(artifacts['1'].progress).toBe(100);
    expect(artifacts['1'].status).toBe('completed');
  });

  it('should update artifact status directly', () => {
    const artifact: ScaffoldedArtifact = { id: '1', name: 'test.txt', stage: 'test', status: 'in_progress', progress: 50, session_id: 's1' };
    useArtifactScaffoldingStore.getState().setArtifacts([artifact]);
    useArtifactScaffoldingStore.getState().updateStatus('1', 'error');
    const { artifacts } = useArtifactScaffoldingStore.getState();
    expect(artifacts['1'].status).toBe('error');
  });

  it('should clear all artifacts', () => {
    const artifact: ScaffoldedArtifact = { id: '1', name: 'test.txt', stage: 'test', status: 'completed', progress: 100, session_id: 's1' };
    useArtifactScaffoldingStore.getState().setArtifacts([artifact]);
    useArtifactScaffoldingStore.getState().clearArtifacts();
    const { artifacts } = useArtifactScaffoldingStore.getState();
    expect(Object.values(artifacts)).toHaveLength(0);
  });
});
