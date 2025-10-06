"use client"

import React, { createContext, useContext, useState, type ReactNode } from 'react';

type AgentName = "analyst" | "architect" | "coder" | "tester" | "deployer" | "orchestrator";

interface AgentContextType {
  selectedAgent: AgentName;
  setSelectedAgent: (agent: AgentName) => void;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export function AgentProvider({ children }: { children: ReactNode }) {
  const [selectedAgent, setSelectedAgent] = useState<AgentName>("analyst");

  return (
    <AgentContext.Provider value={{ selectedAgent, setSelectedAgent }}>
      {children}
    </AgentContext.Provider>
  );
}

export function useAgent() {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
}
