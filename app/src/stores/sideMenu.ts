import { create } from "zustand";

interface SideMenuState {
  isOpen: boolean;
  toggleSideMenu: () => void;
  openSideMenu: () => void;
  closeSideMenu: () => void;
}

export const useSideMenuStore = create<SideMenuState>((set) => ({
  isOpen: true,
  toggleSideMenu: () => set((state) => ({ isOpen: !state.isOpen })),
  openSideMenu: () => set({ isOpen: true }),
  closeSideMenu: () => set({ isOpen: false }),
}));
