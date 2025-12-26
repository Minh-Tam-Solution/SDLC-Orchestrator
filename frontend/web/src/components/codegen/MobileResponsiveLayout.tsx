/**
 * =========================================================================
 * MobileResponsiveLayout - Responsive Layout for App Builder
 * SDLC Orchestrator - Sprint 54 Day 5
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 * Authority: Frontend Team + CTO Approved
 *
 * Purpose:
 * - Provide responsive layout for code generation pages
 * - Handle mobile/tablet/desktop layouts
 * - Split view for file list and preview
 * - Collapsible panels for mobile
 * - Touch-friendly interactions
 *
 * References:
 * - docs/04-build/02-Sprint-Plans/CURRENT-SPRINT.md
 * =========================================================================
 */

import { useState, useCallback, ReactNode } from "react";
import {
  PanelLeft,
  PanelRight,
  X,
  Menu,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useIsMobile, useIsTablet } from "@/hooks/useMediaQuery";

// ============================================================================
// Types
// ============================================================================

interface MobileResponsiveLayoutProps {
  /** Left panel content (e.g., file list) */
  leftPanel: ReactNode;
  /** Main content (e.g., code preview) */
  mainContent: ReactNode;
  /** Right panel content (optional, e.g., properties) */
  rightPanel?: ReactNode;
  /** Left panel title */
  leftPanelTitle?: string;
  /** Right panel title */
  rightPanelTitle?: string;
  /** Default left panel width (desktop) */
  leftPanelWidth?: string;
  /** Default right panel width (desktop) */
  rightPanelWidth?: string;
  /** Show left panel by default on desktop */
  showLeftByDefault?: boolean;
  /** Show right panel by default on desktop */
  showRightByDefault?: boolean;
  /** Optional class name */
  className?: string;
}

// ============================================================================
// Mobile Panel Component
// ============================================================================

interface MobilePanelProps {
  children: ReactNode;
  title?: string;
  side: "left" | "right";
  open: boolean;
  onOpenChange: (open: boolean) => void;
  triggerIcon: ReactNode;
}

function MobilePanel({
  children,
  title,
  side,
  open,
  onOpenChange,
  triggerIcon,
}: MobilePanelProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className="h-9 w-9 flex-shrink-0"
        >
          {triggerIcon}
        </Button>
      </SheetTrigger>
      <SheetContent side={side} className="w-[85vw] sm:w-[350px] p-0">
        {title && (
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <span className="font-semibold">{title}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}
        <div className="h-full overflow-auto">{children}</div>
      </SheetContent>
    </Sheet>
  );
}

// ============================================================================
// Desktop Panel Component
// ============================================================================

interface DesktopPanelProps {
  children: ReactNode;
  title?: string;
  width: string;
  side: "left" | "right";
  collapsed: boolean;
  onToggle: () => void;
}

function DesktopPanel({
  children,
  title,
  width,
  side,
  collapsed,
  onToggle,
}: DesktopPanelProps) {
  if (collapsed) {
    return (
      <div className="flex flex-col items-center py-2 px-1 border-r bg-muted/30">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onToggle}
          title={`Show ${title || side} panel`}
        >
          {side === "left" ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <PanelRight className="h-4 w-4" />
          )}
        </Button>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex flex-col border-r bg-background",
        side === "right" && "border-l border-r-0"
      )}
      style={{ width, minWidth: "200px", maxWidth: "50%" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/30">
        <span className="text-sm font-medium truncate">{title}</span>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 flex-shrink-0"
          onClick={onToggle}
          title={`Collapse ${title || side} panel`}
        >
          {side === "left" ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <PanelRight className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function MobileResponsiveLayout({
  leftPanel,
  mainContent,
  rightPanel,
  leftPanelTitle = "Files",
  rightPanelTitle = "Properties",
  leftPanelWidth = "280px",
  rightPanelWidth = "300px",
  showLeftByDefault = true,
  showRightByDefault = false,
  className,
}: MobileResponsiveLayoutProps) {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();

  // Panel states
  const [leftOpen, setLeftOpen] = useState(false);
  const [rightOpen, setRightOpen] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(!showLeftByDefault);
  const [rightCollapsed, setRightCollapsed] = useState(!showRightByDefault);
  const [isFullScreen, setIsFullScreen] = useState(false);

  const toggleLeftPanel = useCallback(() => {
    setLeftCollapsed((prev) => !prev);
  }, []);

  const toggleRightPanel = useCallback(() => {
    setRightCollapsed((prev) => !prev);
  }, []);

  const toggleFullScreen = useCallback(() => {
    setIsFullScreen((prev) => !prev);
  }, []);

  // Mobile Layout
  if (isMobile) {
    return (
      <div className={cn("flex flex-col h-full", className)}>
        {/* Mobile header with panel toggles */}
        <div className="flex items-center gap-2 p-2 border-b bg-muted/30">
          <MobilePanel
            side="left"
            title={leftPanelTitle}
            open={leftOpen}
            onOpenChange={setLeftOpen}
            triggerIcon={<Menu className="h-4 w-4" />}
          >
            {leftPanel}
          </MobilePanel>

          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium truncate">Code Preview</span>
          </div>

          {rightPanel && (
            <MobilePanel
              side="right"
              title={rightPanelTitle}
              open={rightOpen}
              onOpenChange={setRightOpen}
              triggerIcon={<PanelRight className="h-4 w-4" />}
            >
              {rightPanel}
            </MobilePanel>
          )}
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-auto">{mainContent}</div>
      </div>
    );
  }

  // Tablet Layout (show left panel as drawer, right as panel)
  if (isTablet) {
    return (
      <div className={cn("flex h-full", className)}>
        {/* Left panel as sheet on tablet */}
        <Sheet open={leftOpen} onOpenChange={setLeftOpen}>
          <SheetContent side="left" className="w-[300px] p-0">
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <span className="font-semibold">{leftPanelTitle}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setLeftOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="h-full overflow-auto">{leftPanel}</div>
          </SheetContent>
        </Sheet>

        {/* Main area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Toolbar */}
          <div className="flex items-center gap-2 p-2 border-b bg-muted/30">
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setLeftOpen(true)}
            >
              <Menu className="h-4 w-4" />
            </Button>
            <span className="flex-1 text-sm font-medium">{leftPanelTitle}</span>
            {rightPanel && (
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={toggleRightPanel}
              >
                <PanelRight className="h-4 w-4" />
              </Button>
            )}
          </div>

          <div className="flex flex-1 overflow-hidden">
            {/* Main content */}
            <div className="flex-1 overflow-auto">{mainContent}</div>

            {/* Right panel */}
            {rightPanel && !rightCollapsed && (
              <DesktopPanel
                side="right"
                title={rightPanelTitle}
                width={rightPanelWidth}
                collapsed={false}
                onToggle={toggleRightPanel}
              >
                {rightPanel}
              </DesktopPanel>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Desktop Layout (full 3-column)
  if (isFullScreen) {
    return (
      <div className={cn("fixed inset-0 z-50 bg-background flex flex-col", className)}>
        <div className="flex items-center justify-between px-4 py-2 border-b">
          <span className="font-semibold">Code Generation</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={toggleFullScreen}
          >
            <Minimize2 className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex flex-1 overflow-hidden">
          {/* Left panel */}
          <DesktopPanel
            side="left"
            title={leftPanelTitle}
            width={leftPanelWidth}
            collapsed={leftCollapsed}
            onToggle={toggleLeftPanel}
          >
            {leftPanel}
          </DesktopPanel>

          {/* Main content */}
          <div className="flex-1 overflow-auto">{mainContent}</div>

          {/* Right panel */}
          {rightPanel && (
            <DesktopPanel
              side="right"
              title={rightPanelTitle}
              width={rightPanelWidth}
              collapsed={rightCollapsed}
              onToggle={toggleRightPanel}
            >
              {rightPanel}
            </DesktopPanel>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex h-full overflow-hidden", className)}>
      {/* Left panel */}
      <DesktopPanel
        side="left"
        title={leftPanelTitle}
        width={leftPanelWidth}
        collapsed={leftCollapsed}
        onToggle={toggleLeftPanel}
      >
        {leftPanel}
      </DesktopPanel>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Optional toolbar */}
        <div className="flex items-center justify-end gap-2 p-1 border-b bg-muted/20">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={toggleFullScreen}
            title="Full screen"
          >
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex-1 overflow-auto">{mainContent}</div>
      </div>

      {/* Right panel */}
      {rightPanel && (
        <DesktopPanel
          side="right"
          title={rightPanelTitle}
          width={rightPanelWidth}
          collapsed={rightCollapsed}
          onToggle={toggleRightPanel}
        >
          {rightPanel}
        </DesktopPanel>
      )}
    </div>
  );
}

export default MobileResponsiveLayout;
