'use client';

import { createContext, useContext } from 'react';

const SidebarContext = createContext<{
  openSidebar: () => void;
} | null>(null);

export const SidebarProvider = SidebarContext.Provider;

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};