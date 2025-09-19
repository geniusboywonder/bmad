"use client"

import { useWebSocket } from "../hooks/use-websocket"
import { Badge } from "./ui/badge"

import { Wifi, WifiOff, AlertTriangle } from "lucide-react"

export function ConnectionStatus() {
  const { connectionStatus } = useWebSocket(false) // Don't auto-connect from status component

  const getStatusInfo = () => {
    if (connectionStatus.connected) {
      return {
        color: "text-green-500",
        icon: <Wifi className="w-4 h-4" />,
        text: "Connected",
      }
    }
    if (connectionStatus.reconnecting) {
      return {
        color: "text-yellow-500",
        icon: <WifiOff className="w-4 h-4 animate-pulse" />,
        text: "Connecting...",
      }
    }
    if (connectionStatus.error) {
        return {
            color: "text-red-500",
            icon: <AlertTriangle className="w-4 h-4" />,
            text: "Error",
        }
    }
    return {
      color: "text-red-500",
      icon: <WifiOff className="w-4 h-4" />,
      text: "Disconnected",
    }
  }

  const { color, icon, text } = getStatusInfo()

  return (
    <div className={`flex items-center gap-2 text-xs ${color}`}>
      {icon}
      <span className="font-medium">{text}</span>
      {connectionStatus.lastConnected && (
        <span className="text-xs text-muted-foreground">
          Last: {connectionStatus.lastConnected.toLocaleTimeString()}
        </span>
      )}
    </div>
  )
}
