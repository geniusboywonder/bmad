"use client"

import { AlertTriangle, RotateCw } from "lucide-react"
import { Button } from "./ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"

interface ErrorFallbackProps {
  error: Error
  onReset: () => void
}

export function ErrorFallback({ error, onReset }: ErrorFallbackProps) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="w-full max-w-lg text-center shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center justify-center gap-2 text-xl text-destructive">
            <AlertTriangle className="w-6 h-6" />
            Something went wrong
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">
            An unexpected error occurred in the application. You can try to recover by clicking the button below.
          </p>
          <pre className="text-left text-sm bg-muted p-4 rounded-md overflow-x-auto my-4">
            <code>{error.message}</code>
          </pre>
          <Button onClick={onReset}>
            <RotateCw className="w-4 h-4 mr-2" />
            Try again
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
