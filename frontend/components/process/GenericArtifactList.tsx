"use client"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, Download, Share2, AlertTriangle } from "lucide-react"
import { useHITLStore } from "@/lib/stores/hitl-store"
import { useEffect, useState } from "react"
import type { Artifact } from "@/lib/types"

interface GenericArtifactListProps {
  artifacts?: Artifact[]
}

export function GenericArtifactList({ artifacts = [] }: GenericArtifactListProps) {
  const { requests, navigateToRequest } = useHITLStore()
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  const getArtifactHITLRequests = (artifactId: string) => {
    if (!isClient) return []
    return requests.filter(req => 
      req.status === 'pending' && 
      req.context?.artifactId === artifactId
    )
  }

  const handleHITLClick = (artifactId: string) => {
    const hitlRequests = getArtifactHITLRequests(artifactId)
    if (hitlRequests.length > 0) {
      navigateToRequest(hitlRequests[0].id)
    }
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle>Process Artifacts</CardTitle>
        <CardDescription>
            A list of all artifacts generated during the process.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {artifacts && artifacts.length > 0 ? (
            <Table>
            <TableHeader>
                <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Modified</TableHead>
                <TableHead className="text-right">Actions</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {artifacts.map((artifact) => {
                  const hitlRequests = getArtifactHITLRequests(artifact.id)
                  const hasHITL = hitlRequests.length > 0
                  
                  return (
                    <TableRow key={artifact.id}>
                        <TableCell className="font-medium flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            {artifact.name}
                        </TableCell>
                        <TableCell>{artifact.type}</TableCell>
                        <TableCell>
                            <div className="flex items-center gap-2">
                              {hasHITL ? (
                                <Badge
                                  variant="destructive"
                                  className="animate-pulse cursor-pointer"
                                  onClick={() => handleHITLClick(artifact.id)}
                                  title="Click to resolve HITL request"
                                >
                                  <AlertTriangle className="w-3 h-3 mr-1" />
                                  HITL ({hitlRequests.length})
                                </Badge>
                              ) : (
                                <Badge variant={artifact.status === 'final' ? 'default' : 'outline'}>
                                    {artifact.status}
                                </Badge>
                              )}
                            </div>
                        </TableCell>
                        <TableCell>{artifact.updatedAt}</TableCell>
                        <TableCell className="text-right">
                            <Button variant="ghost" size="icon">
                                <Download className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon">
                                <Share2 className="h-4 w-4" />
                            </Button>
                        </TableCell>
                    </TableRow>
                  )
                })}
            </TableBody>
            </Table>
        ) : (
            <div className="text-center text-muted-foreground py-8">
                <p>No artifacts have been generated yet.</p>
            </div>
        )}
      </CardContent>
    </Card>
  )
}
