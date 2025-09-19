"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function SidebarPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Enhanced Sidebar</h1>
        <p className="text-muted-foreground">
          This view showcases the enhanced sidebar with improved labels and specific alert badges.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Content Area</CardTitle>
        </CardHeader>
        <CardContent>
          <p>
            The enhanced sidebar is visible on the left. It is part of the layout for the entire UX Review Mockups section.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
