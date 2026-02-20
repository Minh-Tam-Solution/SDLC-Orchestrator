# TypeScript Style Guide - Frontend Development Standards

**Version**: 1.0.0
**Date**: November 13, 2025
**Status**: ACTIVE - MANDATORY ENFORCEMENT
**Authority**: Frontend Lead + CTO Approved
**Foundation**: TypeScript 5.0+, React 18+, ESLint, Prettier
**Framework**: SDLC 6.1.0

---

## 🎯 Purpose

This document defines the mandatory TypeScript coding standards for the SDLC Orchestrator frontend. All TypeScript/React code must follow these conventions to ensure type safety, consistency, and maintainability.

**Tech Stack**:
- TypeScript 5.0+ (strict mode enabled)
- React 18+ (with hooks, no class components)
- TanStack Query (data fetching + caching)
- Zustand (lightweight state management)
- Tailwind CSS (utility-first styling)
- Vitest + React Testing Library (testing)

---

## 📏 Code Formatting

### Automated Tools (REQUIRED)

All code must pass these automated tools before commit:

```bash
# Install development dependencies
npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install -D prettier eslint-config-prettier
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Format code (automatic)
npm run format

# Lint code (check for errors)
npm run lint

# Type check (strict mode)
npm run type-check

# Run tests with coverage
npm run test:coverage
```

**Pre-commit hook enforces these checks** - commits will be rejected if any tool fails.

---

### Prettier (Code Formatter)

```json
// .prettierrc.json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": false,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

**Line Length**: 100 characters (balance readability vs screen space)

**Example**:
```typescript
// ✅ GOOD - Prettier formatted
export const ProjectList: React.FC<ProjectListProps> = ({
  organizationId,
  onProjectClick,
}) => {
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ["projects", organizationId],
    queryFn: () => api.projects.list(organizationId),
    staleTime: 5 * 60 * 1000,
  });

  return <div className="grid grid-cols-3 gap-4">{/* ... */}</div>;
};

// ❌ BAD - Inconsistent formatting
export const ProjectList: React.FC<ProjectListProps> = ({ organizationId, onProjectClick }) => {
  const { data: projects, isLoading, error } = useQuery({queryKey: ['projects', organizationId], queryFn: () => api.projects.list(organizationId)});
  return <div className='grid grid-cols-3 gap-4'>{/* ... */}</div>
}
```

---

### ESLint (Linter)

```json
// .eslintrc.json
{
  "parser": "@typescript-eslint/parser",
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/explicit-function-return-type": "warn",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/no-explicit-any": "error",
    "react/react-in-jsx-scope": "off",
    "react/prop-types": "off",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

---

## 🔤 Naming Conventions

### Variables and Functions

```typescript
// ✅ GOOD - camelCase for variables and functions
const userId = "550e8400-e29b-41d4-a716-446655440000";
const accessToken = createAccessToken(userId);

function getCurrentUser(token: string): User {
  return decodeToken(token);
}

// Arrow functions (preferred for React components)
const handleSubmit = (event: React.FormEvent): void => {
  event.preventDefault();
};

// ❌ BAD - PascalCase or snake_case
const UserId = "550e8400-e29b-41d4-a716-446655440000";
const access_token = createAccessToken(userId);

function GetCurrentUser(token: string): User {
  return decodeToken(token);
}
```

---

### React Components

```typescript
// ✅ GOOD - PascalCase for components
export const ProjectCard: React.FC<ProjectCardProps> = ({ project }) => {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="text-lg font-semibold">{project.name}</h3>
    </div>
  );
};

export function UserProfile({ user }: UserProfileProps): JSX.Element {
  return <div>{user.fullName}</div>;
}

// ❌ BAD - camelCase or snake_case for components
export const projectCard = ({ project }) => {
  return <div>{project.name}</div>;
};

export function user_profile({ user }) {
  return <div>{user.fullName}</div>;
}
```

---

### Interfaces and Types

```typescript
// ✅ GOOD - PascalCase, descriptive names
interface User {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
}

type ProjectStatus = "active" | "archived" | "pending";

interface ProjectCardProps {
  project: Project;
  onClick: (projectId: string) => void;
}

// ❌ BAD - Prefixing with I, T, or lowercase
interface IUser {  // Don't prefix with I
  id: string;
}

type TProjectStatus = "active" | "archived";  // Don't prefix with T

interface projectCardProps {  // Should be PascalCase
  project: Project;
}
```

---

### Constants and Enums

```typescript
// ✅ GOOD - UPPER_CASE for constants
const MAX_UPLOAD_SIZE = 100 * 1024 * 1024; // 100MB
const API_BASE_URL = "http://localhost:8000/api/v1";
const DEFAULT_PAGE_SIZE = 50;

// Enums - PascalCase for name, UPPER_CASE for values
enum UserRole {
  DEVELOPER = "developer",
  QA = "qa",
  DEVOPS = "devops",
  PM = "pm",
  TECH_LEAD = "tl",
  ENG_MANAGER = "em",
  CTO = "cto",
}

// ❌ BAD - camelCase for constants
const maxUploadSize = 100 * 1024 * 1024;
const apiBaseUrl = "http://localhost:8000";

enum userRole {  // Should be PascalCase
  developer = "developer",  // Should be UPPER_CASE
}
```

---

## 📝 Type Annotations (MANDATORY)

**100% type coverage required** - `any` is banned except in rare, documented cases.

### Function Types

```typescript
// ✅ GOOD - Explicit parameter and return types
function calculateProgress(completed: number, total: number): number {
  return Math.round((completed / total) * 100);
}

const fetchProjects = async (orgId: string): Promise<Project[]> => {
  const response = await fetch(`/api/v1/projects?org=${orgId}`);
  return response.json();
};

// Higher-order functions
const withAuth = (
  Component: React.ComponentType<any>
): React.FC<any> => {
  return (props) => {
    const { user } = useAuth();
    if (!user) return <LoginPage />;
    return <Component {...props} />;
  };
};

// ❌ BAD - Missing types, using any
function calculateProgress(completed, total) {  // No types
  return Math.round((completed / total) * 100);
}

const fetchProjects = async (orgId: any): Promise<any> => {  // any banned
  const response = await fetch(`/api/v1/projects?org=${orgId}`);
  return response.json();
};
```

---

### React Component Props

```typescript
// ✅ GOOD - Interface for props, explicit types
interface ProjectListProps {
  organizationId: string;
  onProjectClick: (projectId: string) => void;
  filters?: ProjectFilters;
}

export const ProjectList: React.FC<ProjectListProps> = ({
  organizationId,
  onProjectClick,
  filters = {},
}) => {
  // Component implementation
};

// With children
interface LayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children, sidebar }) => {
  return (
    <div className="flex">
      {sidebar && <aside>{sidebar}</aside>}
      <main>{children}</main>
    </div>
  );
};

// ❌ BAD - No prop types, using any
export const ProjectList = ({ organizationId, onProjectClick, filters }: any) => {
  // No type safety
};

export const Layout = (props) => {  // No prop types
  return <div>{props.children}</div>;
};
```

---

### Type Guards

```typescript
// ✅ GOOD - Type guards for runtime type checking
interface User {
  id: string;
  email: string;
}

interface ApiKey {
  id: string;
  key: string;
}

function isUser(auth: User | ApiKey): auth is User {
  return "email" in auth;
}

// Usage
function greet(auth: User | ApiKey): string {
  if (isUser(auth)) {
    return `Hello, ${auth.email}`;  // TypeScript knows auth is User
  }
  return "Hello, API user";
}

// ❌ BAD - Using type assertions without validation
function greet(auth: User | ApiKey): string {
  return `Hello, ${(auth as User).email}`;  // Unsafe! May crash
}
```

---

## ⚛️ React Best Practices

### Hooks Usage

```typescript
// ✅ GOOD - Proper hook usage
export const ProjectDashboard: React.FC = () => {
  // State hooks
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Data fetching (TanStack Query)
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: api.projects.list,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Effects
  useEffect(() => {
    document.title = `Projects - SDLC Orchestrator`;
    return () => {
      document.title = "SDLC Orchestrator";
    };
  }, []);

  // Event handlers
  const handleProjectClick = useCallback(
    (projectId: string) => {
      const project = projects?.find((p) => p.id === projectId);
      setSelectedProject(project || null);
      setIsModalOpen(true);
    },
    [projects]
  );

  // Render
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert error={error} />;

  return (
    <div>
      <ProjectList projects={projects || []} onClick={handleProjectClick} />
      {isModalOpen && selectedProject && (
        <ProjectModal project={selectedProject} onClose={() => setIsModalOpen(false)} />
      )}
    </div>
  );
};

// ❌ BAD - Violates rules of hooks
export const ProjectDashboard = () => {
  const [projects, setProjects] = useState([]);

  // ❌ Conditional hook (violates rules of hooks)
  if (projects.length === 0) {
    useEffect(() => {
      fetchProjects();
    }, []);
  }

  // ❌ Hook in callback
  const handleClick = () => {
    const [count, setCount] = useState(0);  // Can't use hooks here
  };
};
```

---

### Custom Hooks

```typescript
// ✅ GOOD - Reusable custom hook with types
interface UseAuthReturn {
  user: User | null;
  isLoading: boolean;
  error: Error | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem("accessToken");
        if (!token) {
          setIsLoading(false);
          return;
        }

        const currentUser = await api.auth.me(token);
        setUser(currentUser);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      const { user, accessToken } = await api.auth.login(email, password);
      localStorage.setItem("accessToken", accessToken);
      setUser(user);
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("accessToken");
    setUser(null);
  }, []);

  return { user, isLoading, error, login, logout };
}

// Usage
const { user, login, logout } = useAuth();
```

---

### Component Composition

```typescript
// ✅ GOOD - Small, composable components
interface ButtonProps {
  variant: "primary" | "secondary" | "danger";
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant,
  children,
  onClick,
  disabled = false,
}) => {
  const baseStyles = "px-4 py-2 rounded-md font-medium transition-colors";
  const variantStyles = {
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    secondary: "bg-gray-200 text-gray-900 hover:bg-gray-300",
    danger: "bg-red-600 text-white hover:bg-red-700",
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${
        disabled ? "opacity-50 cursor-not-allowed" : ""
      }`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

// Composition
export const DeleteProjectButton: React.FC<{ projectId: string }> = ({ projectId }) => {
  const deleteMutation = useMutation({
    mutationFn: () => api.projects.delete(projectId),
  });

  return (
    <Button
      variant="danger"
      onClick={() => deleteMutation.mutate()}
      disabled={deleteMutation.isLoading}
    >
      {deleteMutation.isLoading ? "Deleting..." : "Delete Project"}
    </Button>
  );
};

// ❌ BAD - Monolithic component
export const ProjectCard = ({ project }) => {
  // 300+ lines of mixed concerns (UI, logic, styling, API calls)
};
```

---

## 🧪 Testing Standards

### Component Testing (React Testing Library)

```typescript
// tests/ProjectList.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ProjectList } from "./ProjectList";

// ✅ GOOD - Descriptive test names, user-centric queries
describe("ProjectList", () => {
  it("displays loading spinner while fetching projects", () => {
    render(<ProjectList organizationId="org-123" onProjectClick={vi.fn()} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("displays error message when fetch fails", async () => {
    // Mock API error
    vi.spyOn(api.projects, "list").mockRejectedValue(new Error("Network error"));

    render(<ProjectList organizationId="org-123" onProjectClick={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it("displays project cards when fetch succeeds", async () => {
    // Mock API success
    const mockProjects = [
      { id: "proj-1", name: "SDLC Orchestrator" },
      { id: "proj-2", name: "NQH Bot" },
    ];
    vi.spyOn(api.projects, "list").mockResolvedValue(mockProjects);

    render(<ProjectList organizationId="org-123" onProjectClick={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("SDLC Orchestrator")).toBeInTheDocument();
      expect(screen.getByText("NQH Bot")).toBeInTheDocument();
    });
  });

  it("calls onProjectClick when project card is clicked", async () => {
    const mockProjects = [{ id: "proj-1", name: "SDLC Orchestrator" }];
    vi.spyOn(api.projects, "list").mockResolvedValue(mockProjects);

    const handleClick = vi.fn();
    render(<ProjectList organizationId="org-123" onProjectClick={handleClick} />);

    await waitFor(() => {
      expect(screen.getByText("SDLC Orchestrator")).toBeInTheDocument();
    });

    const user = userEvent.setup();
    await user.click(screen.getByText("SDLC Orchestrator"));

    expect(handleClick).toHaveBeenCalledWith("proj-1");
  });
});

// ❌ BAD - Implementation details, no user perspective
describe("ProjectList", () => {
  it("works", () => {
    const { container } = render(<ProjectList />);
    expect(container.querySelector(".project-card")).toBeTruthy();  // Implementation detail
  });
});
```

---

### Hook Testing

```typescript
// tests/useAuth.test.ts
import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { useAuth } from "./useAuth";

describe("useAuth", () => {
  it("checks for existing session on mount", async () => {
    const mockUser = { id: "user-123", email: "test@example.com" };
    vi.spyOn(api.auth, "me").mockResolvedValue(mockUser);
    localStorage.setItem("accessToken", "fake-token");

    const { result } = renderHook(() => useAuth());

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
      expect(result.current.user).toEqual(mockUser);
    });
  });

  it("logs in user successfully", async () => {
    const mockResponse = {
      user: { id: "user-123", email: "test@example.com" },
      accessToken: "new-token",
    };
    vi.spyOn(api.auth, "login").mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.login("test@example.com", "password123");

    expect(result.current.user).toEqual(mockResponse.user);
    expect(localStorage.getItem("accessToken")).toBe("new-token");
  });
});
```

---

## 🎨 Tailwind CSS Conventions

```typescript
// ✅ GOOD - Consistent Tailwind usage
export const Card: React.FC<CardProps> = ({ children, variant = "default" }) => {
  const variants = {
    default: "bg-white border-gray-200",
    primary: "bg-blue-50 border-blue-200",
    danger: "bg-red-50 border-red-200",
  };

  return (
    <div className={`rounded-lg border p-4 shadow-sm ${variants[variant]}`}>
      {children}
    </div>
  );
};

// Responsive design
export const Grid: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {children}
    </div>
  );
};

// ❌ BAD - Inline styles, inconsistent classes
export const Card = ({ children }) => {
  return (
    <div style={{ padding: "16px", borderRadius: "8px" }}>  {/* Use Tailwind */}
      {children}
    </div>
  );
};
```

---

## 🔒 Error Handling

```typescript
// ✅ GOOD - Comprehensive error handling
interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error("Error caught by boundary:", error, errorInfo);
    // Log to error tracking service (Sentry, etc.)
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="rounded-lg border border-red-200 bg-red-50 p-6">
            <h2 className="text-xl font-semibold text-red-900">
              Something went wrong
            </h2>
            <p className="mt-2 text-red-700">{this.state.error?.message}</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## 🔗 References

### Internal References

- [Zero Mock Policy](./Zero-Mock-Policy.md) - No placeholder code allowed
- [Code Review Guidelines](../02-Code-Review/Code-Review-Guidelines.md) - PR review process
- [Testing Architecture](../03-Testing-Strategy/Testing-Architecture.md) - Test coverage targets

### External References

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [ESLint TypeScript Rules](https://typescript-eslint.io/rules/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Airbnb React Style Guide](https://github.com/airbnb/javascript/tree/master/react)

---

**Last Updated**: November 13, 2025
**Owner**: Frontend Lead + CTO
**Status**: ✅ ACTIVE - MANDATORY ENFORCEMENT
**Next Review**: Sprint retrospectives (weekly)
