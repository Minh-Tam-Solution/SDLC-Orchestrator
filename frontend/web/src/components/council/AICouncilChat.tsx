/**
 * File: frontend/web/src/components/council/AICouncilChat.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Main AI Council Chat component.
 * Slide-out sheet with chat interface for compliance recommendations.
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Bot, Send, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { CouncilToggle } from './CouncilToggle'
import { ChatMessage } from './ChatMessage'
import type {
  AICouncilChatProps,
  ChatMessage as ChatMessageType,
  CouncilRecommendRequest,
  CouncilRecommendResponse,
} from '@/types/council'

// Generate unique ID for messages
function generateId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

// Welcome message
const WELCOME_MESSAGE: ChatMessageType = {
  id: 'welcome',
  role: 'assistant',
  content: `Welcome! I'm your AI Compliance Assistant. I can help you with:

• Fixing compliance violations
• Understanding gate requirements
• Generating evidence templates
• Answering SDLC 4.9 questions

How can I help you today?`,
  timestamp: new Date(),
}

export function AICouncilChat({
  projectId,
  violationId,
  defaultCouncilMode = false,
  onRecommendationApplied,
  className,
}: AICouncilChatProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [councilMode, setCouncilMode] = useState(defaultCouncilMode)
  const [messages, setMessages] = useState<ChatMessageType[]>([WELCOME_MESSAGE])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [messages])

  // Focus textarea when sheet opens
  useEffect(() => {
    if (isOpen && textareaRef.current) {
      setTimeout(() => textareaRef.current?.focus(), 100)
    }
  }, [isOpen])

  // Send message to AI Council API
  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || isLoading) return

    // Add user message
    const userMessage: ChatMessageType = {
      id: generateId(),
      role: 'user',
      content: question.trim(),
      timestamp: new Date(),
    }

    // Add loading message
    const loadingMessage: ChatMessageType = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }

    setMessages((prev) => [...prev, userMessage, loadingMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Build request
      const request: CouncilRecommendRequest = {
        project_id: projectId,
        question: question.trim(),
        council_mode: councilMode,
      }

      if (violationId) {
        request.violation_id = violationId
      }

      // Call API (placeholder - will be replaced with actual API call)
      // In production, this would use useCouncilRecommend hook
      const response = await mockCouncilAPI(request)

      // Replace loading message with response
      const assistantMessage: ChatMessageType = {
        id: generateId(),
        role: 'assistant',
        content: response.recommendation,
        timestamp: new Date(),
        ...(response.council_deliberation ? { councilDeliberation: response.council_deliberation } : {}),
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingMessage.id ? assistantMessage : msg
        )
      )
    } catch (error) {
      // Replace loading message with error
      const errorMessage: ChatMessageType = {
        id: generateId(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        error: error instanceof Error ? error.message : 'Failed to get recommendation',
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingMessage.id ? errorMessage : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }, [projectId, violationId, councilMode, isLoading])

  // Handle form submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(inputValue)
  }

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(inputValue)
    }
  }

  // Clear chat history
  const handleClearChat = () => {
    setMessages([WELCOME_MESSAGE])
  }

  // Handle apply recommendation
  const handleApplyRecommendation = () => {
    const lastAssistantMessage = [...messages]
      .reverse()
      .find((m) => m.role === 'assistant' && m.content)

    if (lastAssistantMessage && onRecommendationApplied) {
      onRecommendationApplied(lastAssistantMessage.content)
    }
  }

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button
          variant="default"
          size="lg"
          className={cn('gap-2', className)}
        >
          <Bot className="h-5 w-5" />
          AI Assistant
        </Button>
      </SheetTrigger>

      <SheetContent
        side="right"
        className="w-full sm:w-[450px] sm:max-w-[450px] p-0 flex flex-col"
      >
        {/* Header */}
        <SheetHeader className="px-4 py-3 border-b">
          <div className="flex items-center justify-between">
            <SheetTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              AI Compliance Assistant
            </SheetTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClearChat}
              title="Clear chat"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>

          {/* Council Toggle */}
          <div className="mt-2">
            <CouncilToggle
              enabled={councilMode}
              onChange={setCouncilMode}
              disabled={isLoading}
            />
          </div>
        </SheetHeader>

        {/* Messages */}
        <ScrollArea ref={scrollAreaRef} className="flex-1 px-4">
          <div className="py-4 space-y-4">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                onApplyRecommendation={handleApplyRecommendation}
              />
            ))}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <form
          onSubmit={handleSubmit}
          className="border-t p-4 bg-background"
        >
          <div className="flex gap-2">
            <Textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about compliance..."
              disabled={isLoading}
              className="min-h-[60px] max-h-[120px] resize-none"
              aria-label="Chat input"
            />
            <Button
              type="submit"
              size="icon"
              disabled={!inputValue.trim() || isLoading}
              className="h-[60px] w-[60px]"
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </form>
      </SheetContent>
    </Sheet>
  )
}

// Mock API for development - will be replaced with actual API call
async function mockCouncilAPI(
  request: CouncilRecommendRequest
): Promise<CouncilRecommendResponse> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 2000))

  // Mock response
  if (request.council_mode) {
    return {
      request_id: generateId(),
      recommendation: `To address your compliance question, here's my recommendation:

1. **Review the current gate requirements** - Check G2 (Design) gate criteria
2. **Gather required evidence** - Security review, architecture diagrams
3. **Submit for approval** - Use the Evidence Vault to upload documents

This recommendation is based on consensus from 3 AI providers.`,
      confidence_score: 92,
      council_mode: true,
      council_deliberation: {
        stage1_responses: [
          {
            provider: 'Claude',
            model: 'claude-3-5-sonnet',
            response: 'Based on SDLC 4.9 guidelines, the security review evidence should include threat modeling documentation, penetration test results, and security architecture review sign-off.',
            duration_ms: 450,
            confidence: 85,
          },
          {
            provider: 'OpenAI',
            model: 'gpt-4o',
            response: 'For G2 gate compliance, ensure you have architecture decision records (ADRs), security baseline assessment, and code review policies documented.',
            duration_ms: 380,
            confidence: 78,
          },
          {
            provider: 'Gemini',
            model: 'gemini-1.5-pro',
            response: 'The compliance requirements indicate you need design specifications, security controls mapping, and risk assessment documentation.',
            duration_ms: 420,
            confidence: 72,
          },
        ],
        stage2_rankings: [
          {
            ranker: 'Claude',
            rankings: ['Claude', 'OpenAI', 'Gemini'],
            reasoning: 'Most comprehensive coverage of security requirements',
          },
          {
            ranker: 'OpenAI',
            rankings: ['Claude', 'OpenAI', 'Gemini'],
            reasoning: 'Claude provides more actionable steps',
          },
          {
            ranker: 'Gemini',
            rankings: ['Claude', 'Gemini', 'OpenAI'],
            reasoning: 'Better alignment with SDLC 4.9 framework',
          },
        ],
        stage3_synthesis: {
          answer: 'Combined recommendation based on consensus',
          confidence: 92,
          reasoning: 'All 3 AIs agreed on the core approach: focus on security evidence, architecture documentation, and formal review processes. Claude\'s response was ranked highest for actionability.',
          suggested_action: 'Create a new evidence item of type "Security Review" and attach the signed security assessment document.',
        },
        total_duration_ms: 2300,
        total_cost_usd: 0.0045,
        providers_used: ['Claude', 'OpenAI', 'Gemini'],
      },
      total_duration_ms: 2300,
      total_cost_usd: 0.0045,
      providers_used: ['Claude', 'OpenAI', 'Gemini'],
    }
  }

  // Single LLM response
  return {
    request_id: generateId(),
    recommendation: `Here's my recommendation for your compliance question:

1. Check the current gate requirements in the Policy Library
2. Upload missing evidence to the Evidence Vault
3. Request gate evaluation when ready

Let me know if you need more specific guidance.`,
    confidence_score: 75,
    council_mode: false,
    total_duration_ms: 800,
    total_cost_usd: 0.0012,
    providers_used: ['Claude'],
  }
}

export default AICouncilChat
