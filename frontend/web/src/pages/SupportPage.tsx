/**
 * File: frontend/web/src/pages/SupportPage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 04 (BUILD)
 * Date: 2025-12-20
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * User Support & Documentation page providing centralized access to all
 * documentation guides, contact information, and external resources.
 *
 * Design References:
 * - Design Doc: docs/02-design/11-UI-UX-Design/Support-Page-Design.md
 * - Design Spec: docs/02-design/11-UI-UX-Design/FRONTEND-DESIGN-SPECIFICATION.md
 * - Documentation: USER-SUPPORT-OVERVIEW.md, docs/07-operate/03-User Support/
 *
 * Features:
 * - FR1: 11 documentation guides organized in 3 categories
 * - FR2: Contact information (taidt@mtsolution.com.vn, +84 939 116 006)
 * - FR3: External links (Framework, GitHub)
 * - FR4: Responsive design (mobile-first)
 * - FR5: WCAG 2.1 AA accessibility compliant
 *
 * Performance:
 * - Static data only (no API calls)
 * - Code split via React.lazy in App.tsx
 * - Target: FCP < 1s, LCP < 1.5s
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { 
  BookOpen, 
  ExternalLink, 
  Mail, 
  Phone, 
  Rocket,
  Settings,
  Wrench
} from 'lucide-react'

/**
 * Documentation item data structure
 */
interface DocItem {
  id: string
  title: string
  description: string
  path: string
  icon?: string
}

/**
 * Documentation category data structure
 */
interface DocCategory {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  docs: DocItem[]
}

/**
 * Static documentation data
 * Links to dedicated UI pages for better UX
 */
const DOCUMENTATION_CATEGORIES: DocCategory[] = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    description: 'Essential guides for new users',
    icon: <Rocket className="h-6 w-6" aria-hidden="true" />,
    docs: [
      {
        id: '01',
        title: 'Getting Started',
        description: '5-minute quick start guide',
        path: '/support/getting-started'
      },
      {
        id: '02',
        title: 'SDLC Framework Overview',
        description: 'Understanding SDLC 5.1.1 Framework',
        path: '/support/docs/02-SDLC-Framework-Overview.md'
      }
    ]
  },
  {
    id: 'using-platform',
    title: 'Using the Platform',
    description: 'Feature guides and workflows',
    icon: <Settings className="h-6 w-6" aria-hidden="true" />,
    docs: [
      {
        id: '03',
        title: 'Platform Features',
        description: 'Complete feature overview',
        path: '/support/docs/03-Platform-Features.md'
      },
      {
        id: '04',
        title: 'User Roles & Permissions',
        description: 'Access control and roles',
        path: '/support/docs/04-User-Roles-Permissions.md'
      },
      {
        id: '05',
        title: 'Common Tasks',
        description: 'Step-by-step how-to guides',
        path: '/support/docs/05-Common-Tasks.md'
      }
    ]
  },
  {
    id: 'help-troubleshooting',
    title: 'Help & Troubleshooting',
    description: 'Problem solving and support',
    icon: <Wrench className="h-6 w-6" aria-hidden="true" />,
    docs: [
      {
        id: '06',
        title: 'Troubleshooting',
        description: 'Common issues and solutions',
        path: '/support/docs/06-Troubleshooting.md'
      },
      {
        id: '07',
        title: 'FAQ',
        description: 'Frequently asked questions',
        path: '/support/docs/07-FAQ.md'
      },
      {
        id: '08',
        title: 'Best Practices',
        description: 'Optimization and guidelines',
        path: '/support/docs/08-Best-Practices.md'
      },
      {
        id: '09',
        title: 'Support Channels',
        description: 'Contact and support options',
        path: '/support/docs/09-Support-Channels.md'
      }
    ]
  }
]

/**
 * Statistics for hero section
 */
const STATS = [
  { label: 'Documentation Guides', value: '11', description: 'Comprehensive resources' },
  { label: 'Total Lines', value: '5,314', description: 'Detailed content' },
  { label: 'Categories', value: '3', description: 'Organized topics' }
]

/**
 * External resource links
 * Note: Repository access requires authorization
 */
const EXTERNAL_LINKS = [
  {
    title: 'SDLC Framework Documentation',
    description: 'Contact admin for Framework v5.1.1 access',
    url: '#',
    icon: <BookOpen className="h-4 w-4" aria-hidden="true" />
  }
]

/**
 * SupportPage Component
 * 
 * Displays user documentation organized in 3 categories with
 * contact information and external resource links.
 */
export default function SupportPage() {
  return (
    <DashboardLayout>
      <main id="main-content" className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Skip to main content link for accessibility */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md"
        >
          Skip to main content
        </a>

        {/* Hero Section */}
        <header className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <BookOpen className="h-8 w-8 text-primary" aria-hidden="true" />
            <h1 className="text-2xl sm:text-3xl font-bold">
              User Support & Documentation
            </h1>
          </div>
          <p className="text-base text-muted-foreground max-w-3xl">
            Comprehensive guides for <strong>SDLC Orchestrator</strong> - implementing{' '}
            <strong>SDLC 5.1.1 Enterprise Framework</strong> governance policy.
            Access documentation, contact support, and learn best practices.
          </p>
          <div className="mt-4">
            <Badge variant="secondary" className="text-xs">
              Framework v5.1.1
            </Badge>
          </div>
        </header>

        {/* Statistics Row */}
        <section aria-labelledby="stats-heading" className="mb-8">
          <h2 id="stats-heading" className="sr-only">
            Documentation Statistics
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {STATS.map((stat) => (
              <Card key={stat.label}>
                <CardHeader className="pb-2">
                  <CardDescription className="text-xs">
                    {stat.label}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">
                    {stat.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <Separator />

        {/* Documentation Categories */}
        <section aria-labelledby="categories-heading" className="mb-8">
          <h2 id="categories-heading" className="text-2xl font-semibold mb-6">
            Documentation Categories
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {DOCUMENTATION_CATEGORIES.map((category) => (
              <Card
                key={category.id}
                className="hover:shadow-lg transition-shadow"
              >
                <CardHeader>
                  <div className="flex items-center gap-3 mb-2">
                    <div className="text-primary">{category.icon}</div>
                    <CardTitle className="text-xl font-semibold">
                      {category.title}
                    </CardTitle>
                  </div>
                  <CardDescription className="text-sm">
                    {category.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3" role="list">
                    {category.docs.map((doc) => (
                      <li key={doc.id}>
                        <a
                          href={doc.path}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="group flex items-start gap-2 text-base font-medium text-primary hover:underline focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-sm"
                          aria-label={`Open ${doc.title} in new tab`}
                        >
                          <ExternalLink
                            className="h-4 w-4 mt-0.5 flex-shrink-0 opacity-60 group-hover:opacity-100"
                            aria-hidden="true"
                          />
                          <div>
                            <div>{doc.title}</div>
                            <div className="text-xs text-muted-foreground font-normal">
                              {doc.description}
                            </div>
                          </div>
                        </a>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        <Separator />

        {/* External Resources */}
        <nav aria-label="External Resources" className="mb-8">
          <h2 className="text-2xl font-semibold mb-6">Quick Links</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {EXTERNAL_LINKS.map((link) => (
              <Card key={link.title} className="hover:shadow-lg transition-shadow">
                <CardContent className="pt-6">
                  <a
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex items-start gap-3 focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-sm"
                    aria-label={`Open ${link.title} in new tab`}
                  >
                    <div className="text-primary mt-1">{link.icon}</div>
                    <div className="flex-1">
                      <h3 className="text-base font-medium group-hover:underline">
                        {link.title}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {link.description}
                      </p>
                    </div>
                    <ExternalLink
                      className="h-4 w-4 text-muted-foreground opacity-60 group-hover:opacity-100"
                      aria-hidden="true"
                    />
                  </a>
                </CardContent>
              </Card>
            ))}
          </div>
        </nav>

        <Separator />

        {/* Contact Section */}
        <footer aria-label="Contact Information" className="mb-8">
          <h2 className="text-2xl font-semibold mb-6">Contact Support</h2>
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Mr. Tai</CardTitle>
              <CardDescription>
                Author & Technical Support
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
                <a
                  href="mailto:taidt@mtsolution.com.vn"
                  className="text-base font-medium text-primary hover:underline focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-sm"
                  aria-label="Send email to author at taidt@mtsolution.com.vn"
                >
                  taidt@mtsolution.com.vn
                </a>
              </div>
              <div className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
                <a
                  href="tel:+84939116006"
                  className="text-base font-medium text-primary hover:underline focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-sm"
                  aria-label="Call author at +84 939 116 006"
                >
                  +84 939 116 006
                </a>
              </div>
              <Separator />
              <p className="text-sm text-muted-foreground">
                For bug reports and feature requests, please use our{' '}
                <a
                  href="https://github.com/Minh-Tam-Solution/SDLC-Orchestrator/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-sm"
                  aria-label="Open GitHub Issues in new tab"
                >
                  GitHub Issues
                </a>
                {' '}tracker.
              </p>
            </CardContent>
          </Card>
        </footer>

        {/* Footer note */}
        <div className="text-center text-xs text-muted-foreground mt-8">
          <p>Documentation v1.0 • Last updated: December 20, 2025</p>
        </div>
      </main>
    </DashboardLayout>
  )
}
