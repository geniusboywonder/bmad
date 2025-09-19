import { describe, it, expect, beforeEach } from 'vitest';
import { useNotificationStore, Alert } from './notification-store';

describe('useNotificationStore', () => {
  beforeEach(() => {
    useNotificationStore.getState().clearAlerts();
  });

  it('should have a correct initial state', () => {
    const { alerts } = useNotificationStore.getState();
    expect(alerts).toEqual([]);
  });

  it('should add an alert', () => {
    const newAlert: Alert = { id: '1', message: 'Test alert', priority: 'high' };
    useNotificationStore.getState().addAlert(newAlert);
    const { alerts } = useNotificationStore.getState();
    expect(alerts).toHaveLength(1);
    expect(alerts[0]).toEqual(newAlert);
  });

  it('should dismiss an alert', () => {
    const alert1: Alert = { id: '1', message: 'Test alert 1', priority: 'high' };
    const alert2: Alert = { id: '2', message: 'Test alert 2', priority: 'low' };
    useNotificationStore.getState().addAlert(alert1);
    useNotificationStore.getState().addAlert(alert2);

    useNotificationStore.getState().dismissAlert('1');

    const { alerts } = useNotificationStore.getState();
    expect(alerts).toHaveLength(1);
    expect(alerts[0]).toEqual(alert2);
  });
});
