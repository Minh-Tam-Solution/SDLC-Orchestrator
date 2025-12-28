'use client';

import { useTranslations } from 'next-intl';
import { useLanguage } from '@/app/providers/LanguageProvider';
import { locales, localeFlags, localeNames, Locale } from '@/lib/i18n';

interface LanguageToggleProps {
  className?: string;
}

export function LanguageToggle({ className = '' }: LanguageToggleProps) {
  const { locale, setLocale } = useLanguage();
  const t = useTranslations('i18n');

  const handleToggle = () => {
    const currentIndex = locales.indexOf(locale);
    const nextIndex = (currentIndex + 1) % locales.length;
    setLocale(locales[nextIndex]);
  };

  return (
    <button
      onClick={handleToggle}
      className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground ${className}`}
      aria-label={t('toggle.ariaLabel', { current: localeNames[locale] })}
      title={t('toggle.title', { next: localeNames[locales[(locales.indexOf(locale) + 1) % locales.length]] })}
    >
      <span className="text-base">{localeFlags[locale]}</span>
      <span className="hidden sm:inline">{locale.toUpperCase()}</span>
    </button>
  );
}

interface LanguageDropdownProps {
  className?: string;
}

export function LanguageDropdown({ className = '' }: LanguageDropdownProps) {
  const { locale, setLocale } = useLanguage();
  const t = useTranslations('i18n');

  return (
    <div className={`relative inline-block ${className}`}>
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
        className="appearance-none rounded-md border border-input bg-background px-3 py-1.5 pr-8 text-sm font-medium transition-colors hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring"
        aria-label={t('dropdown.ariaLabel')}
      >
        {locales.map((loc) => (
          <option key={loc} value={loc}>
            {localeFlags[loc]} {localeNames[loc]}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
        <svg
          className="h-4 w-4 text-muted-foreground"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </div>
    </div>
  );
}
