import { create } from 'zustand';

export interface Alert {
  id: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  stage?: string;
}

interface NotificationState {
  alerts: Alert[];
  addAlert: (alert: Alert) => void;
  dismissAlert: (alertId: string) => void;
  clearAlerts: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  alerts: [],
  addAlert: (alert) =>
    set((state) => ({
      alerts: [...state.alerts, alert],
    })),
  dismissAlert: (alertId) =>
    set((state) => ({
      alerts: state.alerts.filter((a) => a.id !== alertId),
    })),
  clearAlerts: () => set({ alerts: [] }),
}));
