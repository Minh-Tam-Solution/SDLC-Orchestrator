"""
React Native Template - Cross-platform mobile app boilerplate

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 3: Build Phase - Template-Based Code Generation
- AI Governance Principle 4: Deterministic Intermediate Representations
- Methodology: Template Method pattern for mobile app scaffolding

Purpose:
React Native + Expo + TypeScript template for cross-platform mobile apps.
Generates production-ready mobile boilerplate with:
- Expo SDK 50+ (managed workflow)
- TypeScript (strict mode)
- Zustand (state management)
- React Navigation (routing)
- Async Storage (local persistence)
- Expo Auth Session (OAuth)
- Native Base / React Native Paper (UI components)

Related ADRs:
- ADR-022: IR-Based Codegen with 4-Gate Quality Pipeline
- ADR-040: App Builder Integration - Competitive Necessity

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
Status: ACTIVE
"""

from typing import List, Dict
from pathlib import Path
import json

from backend.app.schemas.codegen.template_blueprint import (
    TemplateBlueprint,
    TemplateType,
    Entity,
    APIRoute,
    Page,
    EntityField
)
from .base_template import BaseTemplate, GeneratedFile


class ReactNativeTemplate(BaseTemplate):
    """
    React Native + Expo Template for cross-platform mobile apps.

    Tech Stack:
    - Expo SDK 50+ (managed workflow)
    - React Native (latest)
    - TypeScript (strict mode)
    - Zustand (lightweight state management)
    - React Navigation v6 (stack, tab, drawer navigation)
    - Async Storage (local data persistence)
    - Expo Auth Session (OAuth with PKCE)
    - React Native Paper (Material Design UI)
    - Axios (HTTP client)
    - React Hook Form + Zod (forms + validation)

    Features:
    - Authentication (OAuth + local storage)
    - Navigation (Stack, Tab, Drawer)
    - State management (Zustand stores)
    - API integration (Axios with interceptors)
    - Local storage (Async Storage)
    - Form handling (React Hook Form)
    - UI components (React Native Paper)
    - Dark mode support
    """

    template_type = TemplateType.REACT_NATIVE
    template_name = "React Native + Expo"
    template_version = "1.0.0"

    default_tech_stack = [
        "react-native",
        "expo",
        "typescript",
        "zustand",
        "react-navigation",
        "async-storage",
        "expo-auth-session",
        "react-native-paper",
        "axios",
        "zod"
    ]

    required_env_vars = [
        "EXPO_PUBLIC_API_URL",
        "EXPO_PUBLIC_AUTH_CLIENT_ID",
        "EXPO_PUBLIC_AUTH_REDIRECT_URI"
    ]

    def get_file_structure(self, blueprint: TemplateBlueprint) -> Dict[str, str]:
        """Define React Native project structure"""
        return {
            "src/": "Source code root",
            "src/screens/": "Screen components",
            "src/components/": "Reusable components",
            "src/navigation/": "Navigation configuration",
            "src/stores/": "Zustand state stores",
            "src/services/": "API services and utilities",
            "src/types/": "TypeScript type definitions",
            "src/hooks/": "Custom React hooks",
            "src/utils/": "Utility functions",
            "src/theme/": "Theme configuration",
            "assets/": "Images, fonts, icons",
        }

    def generate_config_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate configuration files for React Native + Expo"""
        files = []

        # package.json
        package_json = {
            "name": blueprint.project_name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "main": "expo-router/entry",
            "scripts": {
                "start": "expo start",
                "android": "expo start --android",
                "ios": "expo start --ios",
                "web": "expo start --web",
                "lint": "eslint .",
                "type-check": "tsc --noEmit"
            },
            "dependencies": {
                "expo": "~50.0.0",
                "expo-status-bar": "~1.11.1",
                "react": "18.2.0",
                "react-native": "0.73.2",
                "@react-navigation/native": "^6.1.9",
                "@react-navigation/native-stack": "^6.9.17",
                "@react-navigation/bottom-tabs": "^6.5.11",
                "@react-navigation/drawer": "^6.6.6",
                "react-native-screens": "~3.29.0",
                "react-native-safe-area-context": "4.8.2",
                "zustand": "^4.4.7",
                "@react-native-async-storage/async-storage": "1.21.0",
                "expo-auth-session": "~5.4.0",
                "expo-crypto": "~12.8.0",
                "react-native-paper": "^5.11.6",
                "axios": "^1.6.5",
                "react-hook-form": "^7.49.3",
                "zod": "^3.22.4",
                "@hookform/resolvers": "^3.3.4",
                "expo-constants": "~15.4.5",
                "expo-linking": "~6.2.2",
                "expo-router": "~3.4.7",
                "expo-splash-screen": "~0.26.4",
                "date-fns": "^3.0.6"
            },
            "devDependencies": {
                "@babel/core": "^7.20.0",
                "@types/react": "~18.2.45",
                "@typescript-eslint/eslint-plugin": "^6.18.1",
                "@typescript-eslint/parser": "^6.18.1",
                "eslint": "^8.56.0",
                "eslint-config-universe": "^12.0.0",
                "typescript": "^5.3.3"
            },
            "private": True
        }

        files.append(GeneratedFile(
            path="package.json",
            content=json.dumps(package_json, indent=2),
            language="json"
        ))

        # tsconfig.json
        tsconfig = {
            "extends": "expo/tsconfig.base",
            "compilerOptions": {
                "strict": True,
                "paths": {
                    "@/*": ["./src/*"]
                }
            },
            "include": ["**/*.ts", "**/*.tsx", ".expo/types/**/*.ts", "expo-env.d.ts"]
        }

        files.append(GeneratedFile(
            path="tsconfig.json",
            content=json.dumps(tsconfig, indent=2),
            language="json"
        ))

        # app.json (Expo configuration)
        app_json = {
            "expo": {
                "name": blueprint.project_name,
                "slug": blueprint.project_name.lower().replace(" ", "-"),
                "version": "1.0.0",
                "orientation": "portrait",
                "icon": "./assets/icon.png",
                "userInterfaceStyle": "automatic",
                "splash": {
                    "image": "./assets/splash.png",
                    "resizeMode": "contain",
                    "backgroundColor": "#ffffff"
                },
                "assetBundlePatterns": ["**/*"],
                "ios": {
                    "supportsTablet": True,
                    "bundleIdentifier": f"com.{blueprint.project_name.lower().replace(' ', '')}"
                },
                "android": {
                    "adaptiveIcon": {
                        "foregroundImage": "./assets/adaptive-icon.png",
                        "backgroundColor": "#ffffff"
                    },
                    "package": f"com.{blueprint.project_name.lower().replace(' ', '')}"
                },
                "web": {
                    "favicon": "./assets/favicon.png"
                },
                "plugins": [
                    "expo-router"
                ],
                "experiments": {
                    "typedRoutes": True
                }
            }
        }

        files.append(GeneratedFile(
            path="app.json",
            content=json.dumps(app_json, indent=2),
            language="json"
        ))

        # .eslintrc.js
        eslintrc = """module.exports = {
  extends: ['universe/native'],
  rules: {
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
}
"""

        files.append(GeneratedFile(
            path=".eslintrc.js",
            content=eslintrc,
            language="javascript"
        ))

        # babel.config.js
        babel_config = """module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      'react-native-reanimated/plugin',
    ],
  };
};
"""

        files.append(GeneratedFile(
            path="babel.config.js",
            content=babel_config,
            language="javascript"
        ))

        return files

    def generate_entry_point(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate React Native app entry point and core files"""
        files = []

        # App.tsx (main entry point)
        app_tsx = f"""import {{ useEffect }} from 'react'
import {{ NavigationContainer }} from '@react-navigation/native'
import {{ PaperProvider }} from 'react-native-paper'
import {{ SafeAreaProvider }} from 'react-native-safe-area-context'
import * as SplashScreen from 'expo-splash-screen'
import {{ RootNavigator }} from './src/navigation/RootNavigator'
import {{ useAuthStore }} from './src/stores/authStore'
import {{ lightTheme, darkTheme }} from './src/theme'
import {{ useColorScheme }} from 'react-native'

SplashScreen.preventAutoHideAsync()

export default function App() {{
  const colorScheme = useColorScheme()
  const {{ isLoading, initialize }} = useAuthStore()

  useEffect(() => {{
    initialize().finally(() => {{
      SplashScreen.hideAsync()
    }})
  }}, [])

  if (isLoading) {{
    return null
  }}

  return (
    <SafeAreaProvider>
      <PaperProvider theme={{colorScheme === 'dark' ? darkTheme : lightTheme}}>
        <NavigationContainer>
          <RootNavigator />
        </NavigationContainer>
      </PaperProvider>
    </SafeAreaProvider>
  )
}}
"""

        files.append(GeneratedFile(
            path="App.tsx",
            content=app_tsx,
            language="typescriptreact"
        ))

        # Root Navigator
        root_navigator = """import React from 'react'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { useAuthStore } from '../stores/authStore'
import { AuthNavigator } from './AuthNavigator'
import { MainNavigator } from './MainNavigator'

const Stack = createNativeStackNavigator()

export function RootNavigator() {
  const { isAuthenticated } = useAuthStore()

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <Stack.Screen name="Main" component={MainNavigator} />
      ) : (
        <Stack.Screen name="Auth" component={AuthNavigator} />
      )}
    </Stack.Navigator>
  )
}
"""

        files.append(GeneratedFile(
            path="src/navigation/RootNavigator.tsx",
            content=root_navigator,
            language="typescriptreact"
        ))

        # Auth Navigator
        auth_navigator = """import React from 'react'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { LoginScreen } from '../screens/auth/LoginScreen'
import { RegisterScreen } from '../screens/auth/RegisterScreen'

const Stack = createNativeStackNavigator()

export function AuthNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen
        name="Login"
        component={LoginScreen}
        options={{ title: 'Sign In' }}
      />
      <Stack.Screen
        name="Register"
        component={RegisterScreen}
        options={{ title: 'Sign Up' }}
      />
    </Stack.Navigator>
  )
}
"""

        files.append(GeneratedFile(
            path="src/navigation/AuthNavigator.tsx",
            content=auth_navigator,
            language="typescriptreact"
        ))

        # Main Navigator (Bottom Tabs)
        main_navigator = """import React from 'react'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { HomeScreen } from '../screens/main/HomeScreen'
import { ProfileScreen } from '../screens/main/ProfileScreen'
import { Icon } from 'react-native-paper'

const Tab = createBottomTabNavigator()

export function MainNavigator() {
  return (
    <Tab.Navigator>
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon source="home" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon source="account" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  )
}
"""

        files.append(GeneratedFile(
            path="src/navigation/MainNavigator.tsx",
            content=main_navigator,
            language="typescriptreact"
        ))

        # Auth Store (Zustand)
        auth_store = f"""import {{ create }} from 'zustand'
import AsyncStorage from '@react-native-async-storage/async-storage'
import {{ api }} from '../services/api'

interface User {{
  id: string
  email: string
  name: string
}}

interface AuthStore {{
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
  initialize: () => Promise<void>
}}

export const useAuthStore = create<AuthStore>((set) => ({{
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {{
    try {{
      const response = await api.post('/auth/login', {{ email, password }})
      const {{ user, token }} = response.data

      await AsyncStorage.setItem('token', token)
      await AsyncStorage.setItem('user', JSON.stringify(user))

      set({{ user, token, isAuthenticated: true }})
    }} catch (error) {{
      console.error('Login error:', error)
      throw error
    }}
  }},

  register: async (email, password, name) => {{
    try {{
      const response = await api.post('/auth/register', {{ email, password, name }})
      const {{ user, token }} = response.data

      await AsyncStorage.setItem('token', token)
      await AsyncStorage.setItem('user', JSON.stringify(user))

      set({{ user, token, isAuthenticated: true }})
    }} catch (error) {{
      console.error('Register error:', error)
      throw error
    }}
  }},

  logout: async () => {{
    await AsyncStorage.removeItem('token')
    await AsyncStorage.removeItem('user')
    set({{ user: null, token: null, isAuthenticated: false }})
  }},

  initialize: async () => {{
    try {{
      const token = await AsyncStorage.getItem('token')
      const userStr = await AsyncStorage.getItem('user')

      if (token && userStr) {{
        const user = JSON.parse(userStr)
        set({{ user, token, isAuthenticated: true, isLoading: false }})
      }} else {{
        set({{ isLoading: false }})
      }}
    }} catch (error) {{
      console.error('Initialize error:', error)
      set({{ isLoading: false }})
    }}
  }},
}}))
"""

        files.append(GeneratedFile(
            path="src/stores/authStore.ts",
            content=auth_store,
            language="typescript"
        ))

        # API Service (Axios)
        api_service = """import axios from 'axios'
import AsyncStorage from '@react-native-async-storage/async-storage'
import Constants from 'expo-constants'

const API_URL = Constants.expoConfig?.extra?.apiUrl || process.env.EXPO_PUBLIC_API_URL

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await AsyncStorage.removeItem('token')
      await AsyncStorage.removeItem('user')
      // Navigate to login (handled by auth store)
    }
    return Promise.reject(error)
  }
)
"""

        files.append(GeneratedFile(
            path="src/services/api.ts",
            content=api_service,
            language="typescript"
        ))

        # Theme configuration
        theme_config = """import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper'

export const lightTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#6200EE',
    secondary: '#03DAC6',
  },
}

export const darkTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: '#BB86FC',
    secondary: '#03DAC6',
  },
}
"""

        files.append(GeneratedFile(
            path="src/theme/index.ts",
            content=theme_config,
            language="typescript"
        ))

        # Login Screen
        login_screen = """import React, { useState } from 'react'
import { View, StyleSheet } from 'react-native'
import { Button, TextInput, Text, Surface } from 'react-native-paper'
import { useAuthStore } from '../../stores/authStore'

export function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const { login } = useAuthStore()

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError('')

    try {
      await login(email, password)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <View style={styles.container}>
      <Surface style={styles.surface} elevation={1}>
        <Text variant="headlineMedium" style={styles.title}>
          Sign In
        </Text>

        <TextInput
          label="Email"
          value={email}
          onChangeText={setEmail}
          mode="outlined"
          keyboardType="email-address"
          autoCapitalize="none"
          style={styles.input}
        />

        <TextInput
          label="Password"
          value={password}
          onChangeText={setPassword}
          mode="outlined"
          secureTextEntry
          style={styles.input}
        />

        {error ? (
          <Text style={styles.error}>{error}</Text>
        ) : null}

        <Button
          mode="contained"
          onPress={handleLogin}
          loading={loading}
          disabled={loading}
          style={styles.button}
        >
          Sign In
        </Button>

        <Button
          mode="text"
          onPress={() => navigation.navigate('Register')}
          style={styles.button}
        >
          Don't have an account? Sign Up
        </Button>
      </Surface>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 16,
  },
  surface: {
    padding: 24,
    borderRadius: 8,
  },
  title: {
    marginBottom: 24,
    textAlign: 'center',
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 8,
  },
  error: {
    color: '#B00020',
    marginBottom: 8,
    textAlign: 'center',
  },
})
"""

        files.append(GeneratedFile(
            path="src/screens/auth/LoginScreen.tsx",
            content=login_screen,
            language="typescriptreact"
        ))

        # Home Screen
        home_screen = f"""import React from 'react'
import {{ View, StyleSheet, ScrollView }} from 'react-native'
import {{ Text, Card, Button }} from 'react-native-paper'
import {{ useAuthStore }} from '../../stores/authStore'

export function HomeScreen() {{
  const {{ user }} = useAuthStore()

  return (
    <ScrollView style={{styles.container}}>
      <View style={{styles.content}}>
        <Text variant="headlineMedium" style={{styles.title}}>
          Welcome, {{user?.name}}!
        </Text>

        <Card style={{styles.card}}>
          <Card.Content>
            <Text variant="titleLarge">{blueprint.project_name}</Text>
            <Text variant="bodyMedium" style={{styles.description}}>
              Your app is ready to go. Start building your features here.
            </Text>
          </Card.Content>
        </Card>

        <Card style={{styles.card}}>
          <Card.Content>
            <Text variant="titleMedium">Features</Text>
            <Text variant="bodyMedium">• Authentication with JWT</Text>
            <Text variant="bodyMedium">• Navigation with React Navigation</Text>
            <Text variant="bodyMedium">• State management with Zustand</Text>
            <Text variant="bodyMedium">• UI components with React Native Paper</Text>
          </Card.Content>
        </Card>
      </View>
    </ScrollView>
  )
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
  }},
  content: {{
    padding: 16,
  }},
  title: {{
    marginBottom: 16,
  }},
  card: {{
    marginBottom: 16,
  }},
  description: {{
    marginTop: 8,
  }},
}})
"""

        files.append(GeneratedFile(
            path="src/screens/main/HomeScreen.tsx",
            content=home_screen,
            language="typescriptreact"
        ))

        # Profile Screen
        profile_screen = """import React from 'react'
import { View, StyleSheet } from 'react-native'
import { Button, Text, Avatar, Surface } from 'react-native-paper'
import { useAuthStore } from '../../stores/authStore'

export function ProfileScreen() {
  const { user, logout } = useAuthStore()

  return (
    <View style={styles.container}>
      <Surface style={styles.surface} elevation={1}>
        <Avatar.Text
          size={80}
          label={user?.name?.substring(0, 2).toUpperCase() || 'U'}
          style={styles.avatar}
        />

        <Text variant="headlineSmall" style={styles.name}>
          {user?.name}
        </Text>

        <Text variant="bodyMedium" style={styles.email}>
          {user?.email}
        </Text>

        <Button
          mode="outlined"
          onPress={logout}
          style={styles.button}
        >
          Sign Out
        </Button>
      </Surface>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  surface: {
    padding: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  avatar: {
    marginBottom: 16,
  },
  name: {
    marginBottom: 8,
  },
  email: {
    marginBottom: 24,
    color: '#666',
  },
  button: {
    minWidth: 200,
  },
})
"""

        files.append(GeneratedFile(
            path="src/screens/main/ProfileScreen.tsx",
            content=profile_screen,
            language="typescriptreact"
        ))

        return files

    def generate_entity_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate TypeScript types for entities"""
        files = []

        for entity in blueprint.entities:
            # Generate TypeScript interface
            type_def = f"""// Generated type for {entity.name}

export interface {entity.name} {{
  id: string
"""

            for field in entity.fields:
                ts_type = self._map_field_type_to_typescript(field.type)
                optional = "?" if not field.required else ""
                type_def += f"  {field.name}{optional}: {ts_type}\n"

            type_def += "  createdAt: string\n"
            type_def += "  updatedAt: string\n"
            type_def += "}\n"

            files.append(GeneratedFile(
                path=f"src/types/{entity.name.lower()}.ts",
                content=type_def,
                language="typescript"
            ))

            # Generate Zustand store for entity
            store_code = self._generate_entity_store(entity)
            files.append(GeneratedFile(
                path=f"src/stores/{entity.name.lower()}Store.ts",
                content=store_code,
                language="typescript"
            ))

        return files

    def generate_page_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """Generate screen components for each page"""
        files = []

        for page in blueprint.pages:
            screen_code = self._generate_screen_component(page, blueprint)
            files.append(GeneratedFile(
                path=f"src/screens/main/{page.name}Screen.tsx",
                content=screen_code,
                language="typescriptreact"
            ))

        return files

    def _map_field_type_to_typescript(self, field_type: str) -> str:
        """Map blueprint field type to TypeScript type"""
        type_map = {
            "string": "string",
            "integer": "number",
            "boolean": "boolean",
            "date": "string",  # ISO date string
            "float": "number",
            "json": "any",
        }
        return type_map.get(field_type.lower(), "string")

    def _generate_entity_store(self, entity: Entity) -> str:
        """Generate Zustand store for an entity"""
        entity_lower = entity.name.lower()

        return f"""import {{ create }} from 'zustand'
import {{ api }} from '../services/api'
import {{ {entity.name} }} from '../types/{entity_lower}'

interface {entity.name}Store {{
  items: {entity.name}[]
  loading: boolean
  error: string | null
  fetchAll: () => Promise<void>
  fetchOne: (id: string) => Promise<{entity.name} | null>
  create: (data: Partial<{entity.name}>) => Promise<{entity.name}>
  update: (id: string, data: Partial<{entity.name}>) => Promise<{entity.name}>
  delete: (id: string) => Promise<void>
}}

export const use{entity.name}Store = create<{entity.name}Store>((set, get) => ({{
  items: [],
  loading: false,
  error: null,

  fetchAll: async () => {{
    set({{ loading: true, error: null }})
    try {{
      const response = await api.get('/{entity_lower}')
      set({{ items: response.data, loading: false }})
    }} catch (error: any) {{
      set({{ error: error.message, loading: false }})
      throw error
    }}
  }},

  fetchOne: async (id) => {{
    set({{ loading: true, error: null }})
    try {{
      const response = await api.get(`/{entity_lower}/${{id}}`)
      set({{ loading: false }})
      return response.data
    }} catch (error: any) {{
      set({{ error: error.message, loading: false }})
      return null
    }}
  }},

  create: async (data) => {{
    set({{ loading: true, error: null }})
    try {{
      const response = await api.post('/{entity_lower}', data)
      const newItem = response.data
      set({{ items: [...get().items, newItem], loading: false }})
      return newItem
    }} catch (error: any) {{
      set({{ error: error.message, loading: false }})
      throw error
    }}
  }},

  update: async (id, data) => {{
    set({{ loading: true, error: null }})
    try {{
      const response = await api.put(`/{entity_lower}/${{id}}`, data)
      const updatedItem = response.data
      set({{
        items: get().items.map((item) => item.id === id ? updatedItem : item),
        loading: false,
      }})
      return updatedItem
    }} catch (error: any) {{
      set({{ error: error.message, loading: false }})
      throw error
    }}
  }},

  delete: async (id) => {{
    set({{ loading: true, error: null }})
    try {{
      await api.delete(`/{entity_lower}/${{id}}`)
      set({{
        items: get().items.filter((item) => item.id !== id),
        loading: false,
      }})
    }} catch (error: any) {{
      set({{ error: error.message, loading: false }})
      throw error
    }}
  }},
}}))
"""

    def _generate_screen_component(self, page: Page, blueprint: TemplateBlueprint) -> str:
        """Generate React Native screen component"""
        return f"""import React from 'react'
import {{ View, StyleSheet, ScrollView }} from 'react-native'
import {{ Text, Card }} from 'react-native-paper'

export function {page.name}Screen() {{
  return (
    <ScrollView style={{styles.container}}>
      <View style={{styles.content}}>
        <Text variant="headlineMedium" style={{styles.title}}>
          {page.name}
        </Text>

        <Card style={{styles.card}}>
          <Card.Content>
            <Text variant="bodyMedium">
              {page.name} screen for {blueprint.project_name}
            </Text>
          </Card.Content>
        </Card>
      </View>
    </ScrollView>
  )
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
  }},
  content: {{
    padding: 16,
  }},
  title: {{
    marginBottom: 16,
  }},
  card: {{
    marginBottom: 16,
  }},
}})
"""

    def get_smoke_test_command(self) -> str:
        """Get smoke test command for React Native"""
        return "npx expo doctor"
