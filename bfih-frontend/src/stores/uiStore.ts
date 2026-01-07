// UI state management

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

type Theme = 'dark' | 'light';
type ModalType =
  | 'hypothesis-detail'
  | 'paradigm-detail'
  | 'evidence-detail'
  | 'bet-confirm'
  | 'help'
  | 'settings'
  | null;

interface UIState {
  // Theme
  theme: Theme;

  // Modals
  activeModal: ModalType;
  modalData: unknown;

  // Help/tooltips
  showTooltips: boolean;
  showBayesianHelp: boolean;

  // Animation preferences
  reducedMotion: boolean;

  // Sidebar
  sidebarCollapsed: boolean;

  // Loading states
  isLoading: boolean;
  loadingMessage: string | null;

  // Notifications
  notifications: Notification[];

  // Actions
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  openModal: (type: ModalType, data?: unknown) => void;
  closeModal: () => void;
  toggleTooltips: () => void;
  toggleBayesianHelp: () => void;
  setReducedMotion: (reduced: boolean) => void;
  toggleSidebar: () => void;
  setLoading: (loading: boolean, message?: string) => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message?: string;
  duration?: number; // ms, 0 for persistent
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        theme: 'dark',
        activeModal: null,
        modalData: null,
        showTooltips: true,
        showBayesianHelp: false,
        reducedMotion: false,
        sidebarCollapsed: false,
        isLoading: false,
        loadingMessage: null,
        notifications: [],

        // Actions
        setTheme: (theme) => {
          set({ theme });
          // Update document class for Tailwind dark mode
          if (theme === 'dark') {
            document.documentElement.classList.add('dark');
          } else {
            document.documentElement.classList.remove('dark');
          }
        },

        toggleTheme: () => {
          const { theme, setTheme } = get();
          setTheme(theme === 'dark' ? 'light' : 'dark');
        },

        openModal: (type, data) => {
          set({
            activeModal: type,
            modalData: data,
          });
        },

        closeModal: () => {
          set({
            activeModal: null,
            modalData: null,
          });
        },

        toggleTooltips: () => {
          set((state) => ({ showTooltips: !state.showTooltips }));
        },

        toggleBayesianHelp: () => {
          set((state) => ({ showBayesianHelp: !state.showBayesianHelp }));
        },

        setReducedMotion: (reduced) => {
          set({ reducedMotion: reduced });
        },

        toggleSidebar: () => {
          set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
        },

        setLoading: (loading, message) => {
          set({
            isLoading: loading,
            loadingMessage: message || null,
          });
        },

        addNotification: (notification) => {
          const id = `notif-${Date.now()}-${Math.random().toString(36).slice(2)}`;
          const newNotification: Notification = {
            ...notification,
            id,
            duration: notification.duration ?? 5000,
          };

          set((state) => ({
            notifications: [...state.notifications, newNotification],
          }));

          // Auto-remove after duration (if not persistent)
          if (newNotification.duration && newNotification.duration > 0) {
            setTimeout(() => {
              get().removeNotification(id);
            }, newNotification.duration);
          }
        },

        removeNotification: (id) => {
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          }));
        },

        clearNotifications: () => {
          set({ notifications: [] });
        },
      }),
      {
        name: 'bfih-ui-store',
        partialize: (state) => ({
          theme: state.theme,
          showTooltips: state.showTooltips,
          reducedMotion: state.reducedMotion,
          sidebarCollapsed: state.sidebarCollapsed,
        }),
        onRehydrateStorage: () => (state) => {
          // Apply theme on rehydration
          if (state?.theme === 'dark') {
            document.documentElement.classList.add('dark');
          }
        },
      }
    ),
    { name: 'UIStore' }
  )
);

// Initialize theme on load
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('bfih-ui-store');
  if (stored) {
    try {
      const { state } = JSON.parse(stored);
      if (state?.theme === 'dark') {
        document.documentElement.classList.add('dark');
      }
    } catch {
      // Default to dark
      document.documentElement.classList.add('dark');
    }
  } else {
    // Default to dark
    document.documentElement.classList.add('dark');
  }
}
