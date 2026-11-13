import React, { createContext, useContext, useEffect, useState } from 'react';

export type Theme = 'dark' | 'light';

export interface ThemeContextValue {
  theme: Theme;
  isDark: boolean;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

export const THEME_STORAGE_KEY = 'portfolio-app-theme';
export const DEFAULT_THEME: Theme = 'dark';

export const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
}

export const normalizeTheme = (raw: string | null | undefined): Theme => {
  if (!raw) return DEFAULT_THEME;
  if (raw === 'light' || raw === 'theme-ivory-atlas' || raw === 'theme-ivory-emerald') {
    return 'light';
  }
  return 'dark';
};

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = DEFAULT_THEME,
}) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (stored) {
        return normalizeTheme(stored);
      }
    } catch {
      // LocalStorage access might fail in restricted sandboxes
    }
    return defaultTheme;
  });

  const isDark = theme === 'dark';

  useEffect(() => {
    try {
      const root = document.documentElement;
      root.setAttribute('data-theme', theme);
      root.setAttribute('data-appearance', theme);
      root.style.colorScheme = theme;

      if (document.body) {
        document.body.setAttribute('data-theme', theme);
        document.body.setAttribute('data-appearance', theme);
      }

      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Ignore storage errors
    }
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(normalizeTheme(newTheme));
  };

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const contextValue: ThemeContextValue = {
    theme,
    isDark,
    setTheme,
    toggleTheme,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

const fallbackContextValue: ThemeContextValue = {
  theme: DEFAULT_THEME,
  isDark: DEFAULT_THEME === 'dark',
  setTheme: () => {},
  toggleTheme: () => {},
};

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    return fallbackContextValue;
  }
  return context;
}

