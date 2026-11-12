import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/app/providers';
import { ThemeToggleProps } from './ThemeToggle.types';
import styles from './ThemeToggle.module.css';

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  className = '',
  showLabels = true,
}) => {
  const { theme, setTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div
      className={`${styles.segmentedGroup} ${className}`.trim()}
      role="group"
      aria-label="Color theme selector"
    >
      <button
        type="button"
        role="button"
        aria-pressed={!isDark}
        aria-label="Switch to light mode (Warm Ivory / Atlas Navy)"
        title="Light Mode: Warm Ivory / Atlas Navy (9.6)"
        onClick={() => setTheme('light')}
        className={`${styles.optionButton} ${!isDark ? styles.activeLight : ''}`}
      >
        <Sun className={!isDark ? styles.sunIcon : styles.mutedIcon} aria-hidden="true" />
        {showLabels && <span>Light</span>}
      </button>

      <button
        type="button"
        role="button"
        aria-pressed={isDark}
        aria-label="Switch to dark mode (Refined Midnight Teal)"
        title="Dark Mode: Refined Midnight Teal (9.7)"
        onClick={() => setTheme('dark')}
        className={`${styles.optionButton} ${isDark ? styles.activeDark : ''}`}
      >
        <Moon className={isDark ? styles.moonIcon : styles.mutedIcon} aria-hidden="true" />
        {showLabels && <span>Dark</span>}
      </button>
    </div>
  );
};

export const ThemeSwitcher = ThemeToggle;

