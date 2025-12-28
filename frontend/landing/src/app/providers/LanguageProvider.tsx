'use client';

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { NextIntlClientProvider } from 'next-intl';
import { Locale, defaultLocale, isValidLocale } from '@/lib/i18n';

const LOCALE_STORAGE_KEY = 'sdlc-locale';

interface LanguageContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function useLanguage(): LanguageContextType {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

interface LanguageProviderProps {
  children: ReactNode;
}

export function LanguageProvider({ children }: LanguageProviderProps) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);
  const [messages, setMessages] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadMessages = useCallback(async (loc: Locale) => {
    try {
      const msgs = await import(`@/messages/${loc}.json`);
      setMessages(msgs.default);
    } catch (error) {
      console.error(`Failed to load messages for locale ${loc}:`, error);
      if (loc !== defaultLocale) {
        const fallbackMsgs = await import(`@/messages/${defaultLocale}.json`);
        setMessages(fallbackMsgs.default);
      }
    }
  }, []);

  useEffect(() => {
    const initLocale = async () => {
      let initialLocale = defaultLocale;

      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem(LOCALE_STORAGE_KEY);
        if (stored && isValidLocale(stored)) {
          initialLocale = stored;
        }
      }

      setLocaleState(initialLocale);
      await loadMessages(initialLocale);
      setIsLoading(false);
    };

    initLocale();
  }, [loadMessages]);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale;
    }
  }, [locale]);

  const setLocale = useCallback(async (newLocale: Locale) => {
    if (!isValidLocale(newLocale)) {
      console.error(`Invalid locale: ${newLocale}`);
      return;
    }

    setLocaleState(newLocale);

    if (typeof window !== 'undefined') {
      localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
    }

    await loadMessages(newLocale);
  }, [loadMessages]);

  if (isLoading || !messages) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <LanguageContext.Provider value={{ locale, setLocale }}>
      <NextIntlClientProvider locale={locale} messages={messages}>
        {children}
      </NextIntlClientProvider>
    </LanguageContext.Provider>
  );
}
