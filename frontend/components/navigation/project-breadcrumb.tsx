"use client"

import { Button } from "@/components/ui/button"
import { ChevronRight, Home } from "lucide-react"
import { cn } from "@/lib/utils"
import { useNavigationStore, BreadcrumbItem } from "@/lib/stores/navigation-store"

interface ProjectBreadcrumbProps {
  className?: string;
}

export function ProjectBreadcrumb({ className }: ProjectBreadcrumbProps) {
  const { breadcrumb, navigateToDashboard } = useNavigationStore();

  const handleNavigateToPath = (item: BreadcrumbItem) => {
    if (item.path === '/') {
      navigateToDashboard();
    }
    // Add other navigation paths as needed
  };

  if (breadcrumb.length <= 1) {
    return null; // Don't show breadcrumb for single items
  }

  return (
    <nav className={cn("flex items-center space-x-1 text-sm text-muted-foreground", className)}>
      <Button
        variant="ghost"
        size="sm"
        onClick={navigateToDashboard}
        className="h-auto p-1 text-muted-foreground hover:text-foreground"
      >
        <Home className="w-4 h-4" />
      </Button>

      {breadcrumb.map((item, index) => (
        <div key={index} className="flex items-center space-x-1">
          <ChevronRight className="w-4 h-4" />
          {item.path ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleNavigateToPath(item)}
              className="h-auto p-1 text-muted-foreground hover:text-foreground"
            >
              {item.label}
            </Button>
          ) : (
            <span className={cn(
              "px-1 py-0.5",
              index === breadcrumb.length - 1 && "text-foreground font-medium"
            )}>
              {item.label}
            </span>
          )}
        </div>
      ))}
    </nav>
  );
}