/**
 * Simple Toast Hook
 * Basic toast notification functionality
 */

import { useState, useCallback } from 'react';

export interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
  duration?: number;
}

interface ToastState {
  toasts: Toast[];
}

const toastState: ToastState = {
  toasts: [],
};

const listeners: Array<(state: ToastState) => void> = [];

function emitChange() {
  listeners.forEach(listener => listener(toastState));
}

export function useToast() {
  const [, forceUpdate] = useState({});

  const toast = useCallback(({ title, description, variant = 'default', duration = 5000 }: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = { id, title, description, variant, duration };

    toastState.toasts.push(newToast);
    emitChange();

    // Auto-remove toast after duration
    if (duration > 0) {
      setTimeout(() => {
        toastState.toasts = toastState.toasts.filter(t => t.id !== id);
        emitChange();
      }, duration);
    }

    // Show browser notification for destructive toasts
    if (variant === 'destructive' && 'Notification' in window) {
      if (Notification.permission === 'granted') {
        new Notification(title, { body: description });
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
          if (permission === 'granted') {
            new Notification(title, { body: description });
          }
        });
      }
    }

    // Console logging for development
    console.log(`[Toast] ${variant === 'destructive' ? 'ERROR' : 'INFO'}: ${title}${description ? ` - ${description}` : ''}`);
  }, []);

  const dismiss = useCallback((toastId: string) => {
    toastState.toasts = toastState.toasts.filter(t => t.id !== toastId);
    emitChange();
  }, []);

  // Subscribe to toast state changes
  useState(() => {
    const listener = () => forceUpdate({});
    listeners.push(listener);
    return () => {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  });

  return {
    toast,
    dismiss,
    toasts: toastState.toasts,
  };
}