/**
 * File: frontend/web/src/pages/DocumentationViewerPage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 04 (BUILD)
 * Date: 2025-12-20
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Documentation viewer page for rendering user support markdown files.
 * Similar to SOPDetailPage markdown rendering approach.
 */

import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { ArrowLeft, Download, BookOpen } from 'lucide-react'
import apiClient from '@/api/client'

/**
 * Markdown renderer component (simple approach from SOPDetailPage)
 */
function MarkdownContent({ content }: { content: string }) {
  const renderMarkdown = (md: string) => {
    return md.split('\n').map((line, index) => {
      if (line.startsWith('# ')) {
        return (
          <h1 key={index} className="text-2xl font-bold mt-6 mb-4">
            {line.slice(2)}
          </h1>
        )
      }
      if (line.startsWith('## ')) {
        return (
          <h2 key={index} className="text-xl font-semibold mt-5 mb-3 border-b pb-2">
            {line.slice(3)}
          </h2>
        )
      }
      if (line.startsWith('### ')) {
        return (
          <h3 key={index} className="text-lg font-medium mt-4 mb-2">
            {line.slice(4)}
          </h3>
        )
      }
      if (line.startsWith('#### ')) {
        return (
          <h4 key={index} className="text-base font-medium mt-3 mb-2">
            {line.slice(5)}
          </h4>
        )
      }
      if (line.startsWith('- ')) {
        return (
          <li key={index} className="ml-6 list-disc my-1">
            {line.slice(2)}
          </li>
        )
      }
      if (line.match(/^\d+\.\s/)) {
        return (
          <li key={index} className="ml-6 list-decimal my-1">
            {line.replace(/^\d+\.\s/, '')}
          </li>
        )
      }
      if (line.startsWith('- [ ]')) {
        return (
          <div key={index} className="ml-6 flex items-center gap-2 my-1">
            <input type="checkbox" className="rounded" disabled />
            <span>{line.slice(6)}</span>
          </div>
        )
      }
      if (line.startsWith('- [x]')) {
        return (
          <div key={index} className="ml-6 flex items-center gap-2 my-1">
            <input type="checkbox" className="rounded" checked disabled />
            <span className="line-through text-muted-foreground">{line.slice(6)}</span>
          </div>
        )
      }
      if (line.includes('**')) {
        const parts = line.split(/\*\*(.*?)\*\*/g)
        return (
          <p key={index} className="my-2">
            {parts.map((part, i) => (i % 2 === 1 ? <strong key={i}>{part}</strong> : part))}
          </p>
        )
      }
      if (line.startsWith('|')) {
        const cells = line.split('|').filter((c) => c.trim())
        if (line.includes('---')) return null
        return (
          <tr key={index} className="border-b">
            {cells.map((cell, i) => (
              <td key={i} className="px-3 py-2 text-sm">
                {cell.trim()}
              </td>
            ))}
          </tr>
        )
      }
      if (line.startsWith('```')) {
        return (
          <div key={index} className="bg-muted p-3 rounded-md font-mono text-sm my-2">
            {line.slice(3)}
          </div>
        )
      }
      if (!line.trim()) {
        return <div key={index} className="h-2" />
      }
      return (
        <p key={index} className="my-2 leading-relaxed">
          {line}
        </p>
      )
    })
  }

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">{renderMarkdown(content)}</div>
  )
}

/**
 * Documentation viewer page
 */
export default function DocumentationViewerPage() {
  const { filename } = useParams<{ filename: string }>()

  // Fetch documentation content
  const { data: content, isLoading, error } = useQuery<string>({
    queryKey: ['documentation', filename],
    queryFn: async () => {
      const response = await apiClient.get(`/docs/user-support/${filename}`, {
        responseType: 'text'
      })
      return response.data
    },
    enabled: !!filename
  })

  // Download handler
  const handleDownload = () => {
    if (!content || !filename) return
    
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Get document title from filename
  const getTitle = () => {
    if (!filename) return 'Documentation'
    return filename.replace('.md', '').replace(/-/g, ' ')
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/support">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Support
              </Button>
            </Link>
            <div className="flex items-center gap-3">
              <BookOpen className="h-6 w-6 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">{getTitle()}</h1>
                <Badge variant="secondary" className="mt-1">
                  User Documentation
                </Badge>
              </div>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={handleDownload} disabled={!content}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>

        {/* Content */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  SDLC Orchestrator User Support
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="flex flex-col items-center gap-4">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                  <p className="text-sm text-muted-foreground">Loading documentation...</p>
                </div>
              </div>
            )}

            {error && (
              <div className="text-center py-12">
                <p className="text-red-600 mb-2">Failed to load documentation</p>
                <p className="text-sm text-muted-foreground">
                  {error instanceof Error ? error.message : 'Unknown error occurred'}
                </p>
              </div>
            )}

            {content && !isLoading && !error && (
              <div className="markdown-content">
                <MarkdownContent content={content} />
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
