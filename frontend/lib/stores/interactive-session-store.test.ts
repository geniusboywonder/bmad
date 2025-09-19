import { describe, it, expect, beforeEach } from 'vitest';
import { useInteractiveSessionStore, RequirementQuestion } from './interactive-session-store';

describe('useInteractiveSessionStore', () => {
  beforeEach(() => {
    useInteractiveSessionStore.getState().clearSession();
  });

  it('should have a correct initial state', () => {
    const { questions, answers, isAwaitingApproval } = useInteractiveSessionStore.getState();
    expect(questions).toEqual([]);
    expect(answers).toEqual({});
    expect(isAwaitingApproval).toBe(false);
  });

  it('should set questions and clear answers', () => {
    const newQuestions: RequirementQuestion[] = [
      { id: '1', text: 'What is your name?' },
    ];
    // First, set some answer
    useInteractiveSessionStore.getState().updateAnswer('old', 'old answer');

    useInteractiveSessionStore.getState().setQuestions(newQuestions);
    const { questions, answers } = useInteractiveSessionStore.getState();
    expect(questions).toEqual(newQuestions);
    expect(answers).toEqual({});
  });

  it('should update an answer', () => {
    useInteractiveSessionStore.getState().updateAnswer('1', 'My name is Jules');
    const { answers } = useInteractiveSessionStore.getState();
    expect(answers['1']).toBe('My name is Jules');
  });

  it('should set awaiting approval status', () => {
    useInteractiveSessionStore.getState().setAwaitingApproval(true);
    const { isAwaitingApproval } = useInteractiveSessionStore.getState();
    expect(isAwaitingApproval).toBe(true);
  });

  it('should clear the session', () => {
    const newQuestions: RequirementQuestion[] = [
      { id: '1', text: 'What is your name?' },
    ];
    useInteractiveSessionStore.getState().setQuestions(newQuestions);
    useInteractiveSessionStore.getState().updateAnswer('1', 'My name is Jules');
    useInteractiveSessionStore.getState().setAwaitingApproval(true);

    useInteractiveSessionStore.getState().clearSession();

    const { questions, answers, isAwaitingApproval } = useInteractiveSessionStore.getState();
    expect(questions).toEqual([]);
    expect(answers).toEqual({});
    expect(isAwaitingApproval).toBe(false);
  });
});
