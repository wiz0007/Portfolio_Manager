# Enterprise Modular Styling Architecture & Design System

**Project:** Portfolio Management & Financial Intelligence Platform  
**Architecture:** CSS Modules + CSS Custom Properties (Native CSS, zero preprocessors)  
**Supported Themes:** Warm Ivory Light (`data-theme="light"`) / Refined Midnight Teal Dark (`data-theme="dark"`)

---

## 1. Overview & Architectural Principles

The styling infrastructure establishes a scalable, modular design system providing a single source of truth for design tokens while keeping component presentation strictly isolated within CSS Modules.

### Core Principles
1. **Global Tokens, Isolated Components**: All shared visual decisions (colors, typography, spacing, elevations, transitions) are declared as CSS Custom Properties in `src/design-system/tokens/`. Components consume these variables inside their own locally scoped `*.module.css` files.
2. **Zero Preprocessors**: Standard CSS supported natively by the Vite toolchain. No SCSS/Sass dependencies.
3. **No Global Collisions**: CSS Modules ensure classes are uniquely hashed during build time (e.g. `_button_1x8q2_1`), avoiding class name collisions.
4. **Co-located Artifacts**: Each component lives in its own dedicated folder containing its code, styles, types, and unit tests.
5. **Two Production Themes**:
   - **Light Theme (`light`)**: Warm Ivory background (`#FAF8F5`), Atlas Navy brand structure (`#0F243A`), and Regal Gold accents (`#C59B27`).
   - **Dark Theme (`dark`)**: Refined Midnight Teal background (`#05151A`), Luminous Pearl foreground (`#F3FAF8`), and Electric Lime accents (`#84CC16`).

---

## 2. Directory Structure

```text
frontend/src/
├── app/
│   ├── providers/
│   │   ├── ThemeProvider.tsx      # Global theme context, persistence & DOM attribute binding
│   │   └── index.ts
│   └── layouts/
│
├── design-system/
│   ├── tokens/
│   │   ├── primitives.css         # Raw palette definitions (Warm Ivory, Atlas, Teal, Lime)
│   │   ├── semantic.css           # Purpose tokens (--color-bg-app, --color-surface-card, etc.)
│   │   ├── components.css         # Component-mapped tokens (--btn-*, --input-*, --card-*)
│   │   ├── typography.css         # Font scales, weights, line-heights, monospace stacks
│   │   ├── spacing.css            # Base 8px scale & density tokens (compact/comfortable)
│   │   ├── elevation.css          # Shadows, border widths, radius scale & z-index layers
│   │   └── motion.css             # Durations, easings, transitions & prefers-reduced-motion
│   │
│   ├── themes/
│   │   ├── light.css              # [data-theme="light"] definitions (Warm Ivory / Atlas)
│   │   └── dark.css               # :root / [data-theme="dark"] definitions (Refined Teal)
│   │
│   ├── components/                # Reusable design system primitives & layout modules
│   │   ├── Button/
│   │   ├── IconButton/
│   │   ├── Input/
│   │   ├── Label/
│   │   ├── Card/
│   │   ├── Badge/
│   │   ├── Divider/
│   │   ├── Table/
│   │   ├── Container/
│   │   ├── Stack/
│   │   ├── Grid/
│   │   ├── PageHeader/
│   │   ├── Dialog/
│   │   ├── MetricDisplay/         # Monospace tabular financial values & trend indicators
│   │   ├── StatusIndicator/       # System health dots with pulse animation
│   │   ├── EmptyState/
│   │   ├── LoadingState/
│   │   ├── ErrorState/
│   │   └── ThemeToggle/           # Segmented Light / Dark theme toggle
│   │
│   └── index.ts                   # Master design system entry point
│
└── styles/
    ├── reset.css                  # Modern element box-sizing and tag reset
    ├── accessibility.css          # Focus-visible rings, .sr-only screen-reader utilities
    ├── globals.css                # Master stylesheet importing tokens, themes & resets
    └── index.css                  # Vite entry importing globals.css
```

---

## 3. Component Folder Standard

Every reusable component must follow this uniform structure:

```text
ComponentName/
├── ComponentName.tsx          # Component implementation
├── ComponentName.module.css   # Locally scoped styles consuming CSS custom properties
├── ComponentName.types.ts     # TypeScript interface contracts
├── ComponentName.test.tsx     # Vitest / React Testing Library unit tests
└── index.ts                   # Public component export
```

### Example: Consuming Tokens in a CSS Module

```css
/* Button.module.css */
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-family-sans);
  font-weight: var(--btn-font-weight);
  border-radius: var(--btn-radius);
  padding: 0 var(--btn-padding-x-md);
  height: var(--btn-height-md);
  transition: var(--transition-colors);
}

.variantPrimary {
  background-color: var(--color-brand-primary);
  color: var(--color-text-inverse);
}

.variantPrimary:hover:not(:disabled) {
  background-color: var(--color-brand-primary-hover);
}

.button:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
```

---

## 4. Theme Implementation & Switching

### Root HTML Attribute
The active theme is attached to the document root element:
```html
<html data-theme="dark">  <!-- or data-theme="light" -->
```

### Persistence
The active theme is automatically stored in browser `localStorage` under:
`portfolio-app-theme`

### Using the Theme Context in React
```tsx
import { useTheme } from '@/app/providers';

const MyComponent = () => {
  const { theme, isDark, setTheme, toggleTheme } = useTheme();

  return (
    <button onClick={toggleTheme}>
      Current theme: {theme} ({isDark ? 'Dark' : 'Light'})
    </button>
  );
};
```

---

## 5. Financial Application Requirements

Dense financial tables and numerical cards use specialized design tokens:
- **Tabular Monospace Digits**: Font stack `--font-family-mono` with `font-variant-numeric: tabular-nums` ensures columns of currencies and stock prices align vertically.
- **Semantic Financial Indicators**:
  - Positive (+ gains): `--color-positive` (`#10B981` / `#0D7A53`), background `--color-positive-subtle`.
  - Negative (- losses): `--color-negative` (`#F43F5E` / `#C23434`), background `--color-negative-subtle`.
  - Neutral / Unchanged: `--color-neutral` (`#648682` / `#64748B`), background `--color-neutral-subtle`.
- **Chart Tokens**: Dedicated `--chart-color-1` through `--chart-color-5`, `--chart-grid`, and `--chart-tooltip-bg` for charting libraries.

---

## 6. How to Add a New Component

1. Create a directory under `src/design-system/components/<ComponentName>/`.
2. Define props in `<ComponentName>.types.ts`.
3. Create styles in `<ComponentName>.module.css` using tokens (`var(--color-...)`, `var(--space-...)`, etc.).
4. Implement component in `<ComponentName>.tsx` using `forwardRef` and exporting `displayName`.
5. Write unit tests in `<ComponentName>.test.tsx`.
6. Export in `index.ts` and re-export from `src/design-system/index.ts`.

---

## 7. Accessibility Standards (WCAG 2.2 AA)

- **Visible Keyboard Focus**: Globally enforced via `:focus-visible` with `--color-focus-ring` (Cyan in Dark, Gold in Light).
- **Reduced Motion**: Automatically respected through `--motion-*` tokens and `prefers-reduced-motion: reduce` overrides in `motion.css`.
- **Screen Reader Support**: `.sr-only` utility available in `accessibility.css` for non-visual assistive descriptions.
- **High Contrast Mode**: Supported via `@media (forced-colors: active)` in `accessibility.css`.

