"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

interface ScanContextValue {
  currentScanId: string | null;
  setCurrentScanId: (id: string | null) => void;
}

const ScanContext = createContext<ScanContextValue | undefined>(undefined);

const STORAGE_KEY = "jarvis.currentScanId";

export function ScanProvider({ children }: { children: ReactNode }) {
  const [currentScanId, setCurrentScanIdState] = useState<string | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored) setCurrentScanIdState(stored);
  }, []);

  function setCurrentScanId(id: string | null) {
    setCurrentScanIdState(id);
    if (id) {
      window.localStorage.setItem(STORAGE_KEY, id);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }

  return (
    <ScanContext.Provider value={{ currentScanId, setCurrentScanId }}>
      {children}
    </ScanContext.Provider>
  );
}

export function useScanContext(): ScanContextValue {
  const ctx = useContext(ScanContext);
  if (!ctx) throw new Error("useScanContext must be used within ScanProvider");
  return ctx;
}
