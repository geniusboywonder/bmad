"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import Link from "next/link"
import { ArrowRight } from "lucide-react"

const mockupPages = [
  {
    href: "/bot-army-ux-review/dashboard",
    title: "Redesigned Dashboard",
    description: "The main dashboard with the new layout, including the HITL alert bar and side-by-side process/chat view.",
  },
  {
    href: "/bot-army-ux-review/chat-interface",
    title: "Enhanced Chat Interface",
    description: "A detailed view of the resizable chat interface with collapsible messages and overlays.",
  },
  {
    href: "/bot-army-ux-review/process-summary",
    title: "Enhanced Process Summary",
    description: "A detailed view of the simplified process summary with expandable cards and parallel workflows.",
  },
  {
    href: "/bot-army-ux-review/sidebar",
    title: "Enhanced Sidebar",
    description: "A view of the application using the new sidebar with improved labels and alert badges.",
  },
]

export default function UXReviewHomePage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold">BotArmy UX Review Mockups</h1>
        <p className="text-muted-foreground">
          This section contains high-fidelity mockups for the suggestions in the UX review document.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {mockupPages.map((page) => (
          <Link href={page.href} key={page.href}>
            <Card className="h-full hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  {page.title}
                  <ArrowRight className="w-5 h-5 text-muted-foreground" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{page.description}</CardDescription>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
