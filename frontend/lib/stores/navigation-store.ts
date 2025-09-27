/**
 * Navigation Store - View State Management
 * Manages transitions between dashboard and project workspace views
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

export type ViewType = 'dashboard' | 'project-workspace';

export interface BreadcrumbItem {
  label: string;
  path?: string;
}

export interface NavigationState {
  currentView: ViewType;
  selectedProjectId: string | null;
  previousView: ViewType | null;
  breadcrumb: BreadcrumbItem[];
  isTransitioning: boolean;
}

export interface NavigationActions {
  navigateToProject: (projectId: string) => void;
  navigateToDashboard: () => void;
  goBack: () => void;
  setBreadcrumb: (breadcrumb: BreadcrumbItem[]) => void;
  setTransitioning: (isTransitioning: boolean) => void;
  reset: () => void;
}

const initialState: NavigationState = {
  currentView: 'dashboard',
  selectedProjectId: null,
  previousView: null,
  breadcrumb: [{ label: 'Projects' }],
  isTransitioning: false,
};

export const useNavigationStore = create<NavigationState & NavigationActions>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    navigateToProject: (projectId: string) => {
      const { currentView } = get();

      set({ isTransitioning: true });

      setTimeout(() => {
        set({
          previousView: currentView,
          currentView: 'project-workspace',
          selectedProjectId: projectId,
          breadcrumb: [
            { label: 'Projects', path: '/' },
            { label: 'Workspace' }
          ],
          isTransitioning: false,
        });
      }, 150); // Small delay for smooth transition
    },

    navigateToDashboard: () => {
      set({ isTransitioning: true });

      setTimeout(() => {
        set({
          previousView: 'project-workspace',
          currentView: 'dashboard',
          selectedProjectId: null,
          breadcrumb: [{ label: 'Projects' }],
          isTransitioning: false,
        });
      }, 150);
    },

    goBack: () => {
      const { previousView, currentView } = get();

      if (previousView) {
        set({ isTransitioning: true });

        setTimeout(() => {
          set({
            currentView: previousView,
            selectedProjectId: previousView === 'dashboard' ? null : get().selectedProjectId,
            previousView: currentView,
            breadcrumb: previousView === 'dashboard'
              ? [{ label: 'Projects' }]
              : [
                  { label: 'Projects', path: '/' },
                  { label: 'Workspace' }
                ],
            isTransitioning: false,
          });
        }, 150);
      }
    },

    setBreadcrumb: (breadcrumb: BreadcrumbItem[]) => {
      set({ breadcrumb });
    },

    setTransitioning: (isTransitioning: boolean) => {
      set({ isTransitioning });
    },

    reset: () => {
      set(initialState);
    },
  }))
);

// Export selectors for optimized re-renders
export const navigationStoreSelectors = {
  currentView: (state: NavigationState & NavigationActions) => state.currentView,
  selectedProjectId: (state: NavigationState & NavigationActions) => state.selectedProjectId,
  breadcrumb: (state: NavigationState & NavigationActions) => state.breadcrumb,
  isTransitioning: (state: NavigationState & NavigationActions) => state.isTransitioning,
  canGoBack: (state: NavigationState & NavigationActions) => state.previousView !== null,
};

// Auto-connect navigation to project store
if (typeof window !== 'undefined') {
  // Subscribe to view changes for debugging
  const unsubscribe = useNavigationStore.subscribe(
    (state) => state.currentView,
    (currentView) => {
      console.log(`[NavigationStore] View changed to: ${currentView}`);
    }
  );
}