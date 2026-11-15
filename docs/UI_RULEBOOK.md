# Portfolio Platform --- UI Rulebook

**Purpose:** Mandatory product-wide UI, layout, component, styling, and
visual-quality standard\
**Applies to:** All current and future frontend pages, shared
components, and feature modules\
**Frontend context:** React + TypeScript + Vite\
**Styling standard:** CSS Modules + CSS custom properties\
**Themes:** Warm Ivory / Atlas Navy / Regal Gold (light); Refined
Midnight Teal / Pearl / Controlled Electric Lime (dark)

------------------------------------------------------------------------

## 1. Core Product UI Principle

Every page must help the user understand, assess, and act on their
financial information quickly.

Every page should answer:

1.  What am I looking at?
2.  What needs my attention?
3.  What can I do next?

Every visible element must have a purpose. If a section, sentence,
border, card, icon, color, or control does not improve comprehension,
decision-making, navigation, or task completion, remove it, reduce its
prominence, or move it to a more appropriate location.

The product must feel like a coherent financial workspace---not a
collection of unrelated dashboards, cards, and forms.

**Minimal does not mean empty.** The goal is high information value with
low visual noise. Do not remove useful financial context merely to make
a page look sparse.

## 2. Start With the User's Job

Before designing or modifying a page:

1.  Identify the primary job the user comes to the page to perform.
2.  Identify the most important information required for that job.
3.  List the primary action and the next most useful secondary actions.
4.  Establish a clear visual hierarchy between primary, supporting, and
    optional information.
5.  Keep frequent actions close to the content they affect.
6.  Move infrequent or destructive actions into compact menus or
    secondary controls.
7.  Remove generic product explanations and filler copy.
8.  Do not invent actions, metrics, or destinations that the product
    does not support.

A page must be organized around user tasks and information priority, not
around the number of components available to display.

## 3. Product-Wide Visual Direction

The interface must be:

-   Professional, calm, precise, and trustworthy.
-   Dense enough for financial information, without feeling crowded.
-   Consistent across dashboard, portfolio, account, and future
    analytics modules.
-   Restrained in its use of color, borders, shadows, animation, and
    decorative elements.
-   Clear about the distinction between actual data, estimates,
    unavailable data, and empty states.
-   Responsive without simply shrinking the desktop layout.

Avoid: - Generic SaaS dashboard patterns made from many identical
cards. - Excessive gradients, glowing borders, glass effects, and
decorative blobs. - Large hero sections that push useful financial
information below the fold. - Repeated explanatory subtitles under every
heading. - Oversized buttons, pills, and status badges. - Fake charts,
placeholder financial metrics, or fabricated activity.

## 4. Global Application Shell

Use one consistent application shell across authenticated pages.

### 4.1 Sidebar

1.  Use one shared sidebar implementation.
2.  Sidebar owns primary application navigation; do not duplicate the
    same route links in the top navbar.
3.  Keep navigation labels short and unambiguous.
4.  Active navigation must be clearly distinguishable without excessive
    color or decoration.
5.  Inactive navigation must remain readable.
6.  Keep icon size, label alignment, row height, and vertical rhythm
    consistent.
7.  Support a collapsed state only if it remains usable and does not
    obscure content.
8.  At intermediate widths, the sidebar must not overlap the page
    content.
9.  On mobile, use an intentional navigation pattern appropriate to the
    existing application; do not introduce duplicate navigation bars.

### 4.2 Top Navbar

1.  Keep the navbar height consistent across authenticated pages.
2.  Reserve it for global utilities, such as page-wide search when
    available, notifications when implemented, account/profile access,
    and the theme control.
3.  Do not place page-specific filters or actions in the global navbar.
4.  Group related utilities together.
5.  Keep the theme selector compact; it must not dominate the header.
6.  Avoid oversized pills, heavy shadows, and unnecessary separators.
7.  On mobile, show only essential global controls.

### 4.3 Main Content

1.  Use a consistent content container and responsive horizontal
    padding.
2.  Align page content consistently with the shared shell.
3.  Use a consistent page-header pattern.
4.  Keep page-specific actions near the heading or section they affect.
5.  Do not let one narrow component create large unused space elsewhere
    in the layout.
6.  Avoid arbitrary maximum widths that make financial tables or
    dashboards unusable.

The sidebar, navbar, and main content should feel like one integrated
workspace. Prefer spacing and subtle surface contrast over hard divider
lines.

## 5. Page Layout and Information Hierarchy

Every page must have an intentional hierarchy.

Recommended page structure:

1.  Page title and concise context, only when context is useful.
2.  Primary page action(s).
3.  Primary information or task area.
4.  Supporting information.
5.  Secondary or historical information.

Rules:

-   Use one clear page-level heading.
-   Use section headings only for meaningful content groups.
-   Do not add generic subtext beneath every heading.
-   Put filters close to the list, table, or chart they control.
-   Put actions near the object they affect.
-   Group related metrics instead of scattering them across unrelated
    cards.
-   Use consistent alignment for headings, values, metadata, and
    actions.
-   Keep the most important content visible without unnecessary
    scrolling.
-   Do not create sections solely to fill empty space.

## 6. Space, Density, and Alignment

Use space as a structural tool.

1.  Use consistent page padding at each breakpoint.
2.  Use consistent internal padding for cards, panels, and controls.
3.  Keep sibling gaps consistent.
4.  Section gaps must be larger than card gaps; card gaps must be larger
    than internal row gaps.
5.  Compact sparse sections instead of stretching them to fill the
    viewport.
6.  Do not create large empty panels for future functionality.
7.  Use a deliberate density level appropriate to financial work.
8.  Align monetary values, percentages, dates, and other comparable
    values consistently.
9.  Avoid awkward wrapping and isolated controls.
10. Ensure flex and grid children can shrink correctly with
    `min-width: 0` where needed.

The interface should be information-efficient but never cramped. Do not
use density as an excuse for tiny text, insufficient click targets, or
crowded controls.

## 7. Cards, Panels, and Data Containers

A card or panel must have one clear purpose.

Recommended content order:

1.  Label or category.
2.  Main value or title.
3.  Supporting context.
4.  Relevant metadata.
5.  Actions.

Rules:

-   Do not wrap every element in a card.
-   Avoid nested cards unless the nested item is independently
    meaningful.
-   Use consistent padding, radius, and surface treatment.
-   Keep repeated cards structurally consistent.
-   Make the primary value visually dominant.
-   Keep supporting metadata compact.
-   Avoid oversized buttons that overpower the information.
-   Do not use full-width pills for ordinary metadata.
-   Do not make a card clickable unless it has a real destination or
    action.
-   If an entire card is interactive, provide hover, focus-visible, and
    keyboard behavior.

Use tables or compact rows when users need to compare multiple financial
records. Do not force tabular information into decorative cards.

## 8. Financial Information and Data Presentation

Financial interfaces require accuracy, traceability, and clear data
states.

### 8.1 Data clarity

1.  Distinguish actual, estimated, projected, and unavailable values.
2.  Never present mock or placeholder values as real financial data.
3.  Show currency and units where ambiguity is possible.
4.  Use consistent precision and rounding rules within comparable views.
5.  Align comparable numeric values consistently.
6.  Keep labels close to their values.
7.  Use clear date ranges and time context for performance information.
8.  Do not imply investment performance or returns where the underlying
    calculation or data does not exist.
9.  Do not visually overstate estimates or predictions.
10. Preserve enough context for users to understand what a metric
    represents.

### 8.2 Semantic financial colors

Maintain separate semantic tokens for: - Positive values. - Negative
values. - Neutral values. - Warning states. - Error states. -
Informational states.

Rules:

-   Brand accent colors must not automatically mean profit or loss.
-   Positive and negative states must remain distinguishable in both
    themes.
-   Do not rely on color alone; use signs, labels, icons, or other
    appropriate cues.
-   Neutral or unavailable values must not resemble gains or losses.
-   Red should be reserved for negative, destructive, or urgent meaning
    where appropriate.
-   Avoid competing semantic colors in the same viewport.

### 8.3 Tables and dense data

-   Use clear column headings.
-   Align numeric columns consistently, normally to the right.
-   Keep row heights compact but readable.
-   Use subtle separators rather than heavy grid borders.
-   Provide a clear hover or selected state when rows are interactive.
-   Prevent long names and metadata from forcing horizontal page
    overflow.
-   On small screens, choose a deliberate responsive table strategy:
    controlled horizontal scrolling, prioritized columns, or an
    alternate compact representation.
-   Never silently hide essential financial fields.

## 9. Theme and Color Rules

The application has two selected themes. Both must use the same semantic
token contract.

### 9.1 Light theme

**Name:** Warm Ivory / Atlas Navy / Regal Gold

Design direction: - Warm ivory page background. - Clean warm-white or
neutral surfaces. - Atlas Navy for primary brand and strong hierarchy. -
Regal Gold as a restrained accent. - Readable dark text and subtle
neutral borders.

Gold should be used sparingly for brand emphasis or meaningful
premium/value states. Do not use it as a default color for every button,
border, icon, or metric.

### 9.2 Dark theme

**Name:** Refined Midnight Teal / Pearl / Controlled Electric Lime

Design direction: - Midnight Teal foundation, not pure black. - Layered
dark teal surfaces. - Pearl primary text. - Muted secondary text. -
Electric Lime used as a controlled accent. - Subtle borders and
carefully managed elevation.

Lime must not become a large background color or the default color for
every active element.

### 9.3 Theme implementation rules

1.  Theme values must be centralized in theme token files.
2.  Components must consume semantic tokens, not theme-specific hex
    values.
3.  Both themes must implement the same semantic token contract.
4.  Theme switching must not require page-specific conditional styling.
5.  New components must work in both themes by default.
6.  Exact hex values and contrast checks must be documented in the
    design-token implementation.
7.  Do not add additional themes without an explicit product decision.

## 10. Styling Architecture --- Mandatory

### 10.1 CSS Modules are the component styling standard

Use CSS Modules for component-specific styling.

Naming convention:

`ComponentName.module.css`

Rules: - Keep a component's styles close to its implementation. - Use
locally scoped class names. - Prefer semantic class names such as
`.container`, `.header`, `.title`, `.actions`, and `.isActive`. - Keep
selectors simple and predictable. - Avoid broad element selectors unless
scoped beneath the component root. - Avoid styling unrelated components
from a module. - Avoid unnecessary cross-module dependencies. - Avoid
`!important` as a normal styling technique. - Remove obsolete selectors
and superseded rules when revising a component.

A typical component folder may contain:

``` text
PortfolioCard/
  PortfolioCard.tsx
  PortfolioCard.module.css
  PortfolioCard.types.ts
  PortfolioCard.test.tsx
  index.ts
```

Do not create files that add no meaningful separation. Small components
may use a simpler structure.

### 10.2 Global CSS is deliberately limited

Global styles may contain only: - CSS reset/normalization. - Font-face
declarations and base typography. - Design-token definitions. - Theme
selectors. - Document-level defaults. - Accessibility utilities that
genuinely need global scope. - Necessary third-party library overrides,
isolated and documented.

Do not place feature layouts or ordinary component styles in global
stylesheets.

### 10.3 CSS custom properties and token layers

Use this hierarchy:

**Primitive tokens → Semantic tokens → Component tokens → CSS Modules**

-   Primitive tokens define palette values and raw design scales.
-   Semantic tokens define meaning, such as background, surface, text,
    border, focus, and positive/negative.
-   Component tokens define shared component-level decisions where
    required.
-   CSS Modules consume semantic and component tokens.

Avoid duplicating the same value in multiple feature modules.

### 10.4 SCSS

Do not introduce SCSS or Sass. Use standard CSS and CSS Modules.

### 10.5 Tailwind

CSS Modules are the primary styling convention.

-   Do not add new Tailwind-based component styling.
-   Existing Tailwind classes may remain during a controlled migration.
-   Do not maintain the same component's styling in both Tailwind and a
    CSS Module.
-   Inspect the existing Tailwind version, configuration, and actual
    usage before removing it.
-   Remove Tailwind dependencies/configuration only after confirming
    that no required usage remains and the project still builds.

Do not perform a risky all-at-once migration.

## 11. Design Tokens and Global Standards

The design system must centrally define the following token families:

### Color

-   Primitive palette values.
-   Background and surface levels.
-   Text hierarchy.
-   Borders and dividers.
-   Brand and interactive colors.
-   Focus states.
-   Semantic statuses.
-   Chart colors.

### Typography

-   Font families.
-   Font sizes and scale.
-   Font weights.
-   Line heights.
-   Letter spacing.
-   Heading, body, label, caption, and numeric styles.

### Spacing

-   Page padding.
-   Section gaps.
-   Component gaps.
-   Control padding.
-   Table density.
-   Form spacing.

### Shape and borders

-   Radius scale.
-   Border widths.
-   Border styles.
-   Focus outline dimensions.

### Elevation

-   Surface levels.
-   Card elevation.
-   Dropdown and popover elevation.
-   Modal elevation.
-   Theme-appropriate shadow treatment.

### Motion

-   Transition durations.
-   Easing curves.
-   Dropdown and dialog motion.
-   Loading feedback.
-   Reduced-motion behavior.

### Layout

-   Application shell dimensions.
-   Sidebar and header sizing.
-   Content containers.
-   Breakpoints.
-   Grid conventions.

Use a consistent scale. Avoid creating arbitrary one-off tokens for
values that are not reusable.

## 12. Component Standards

Shared components must be reusable, accessible, theme-aware, and
independent of individual feature modules.

The shared component layer should include components as they are needed,
such as:

-   Button and IconButton.
-   Input, Textarea, Select.
-   Checkbox, Radio, Switch.
-   Label and Badge.
-   Card and Panel.
-   Table and DataRow.
-   Dialog and Dropdown.
-   Popover and Tooltip.
-   Toast/notification.
-   EmptyState, LoadingState, and ErrorState.
-   StatusIndicator and MetricDisplay.

Component rules:

1.  Define clear variants and sizes only where there is a real use case.
2.  Define all applicable interaction states.
3.  Use design tokens.
4.  Support keyboard interaction.
5.  Provide accessible names and labels.
6.  Avoid feature-specific business logic in generic UI components.
7.  Avoid building duplicate versions of an existing shared component.
8.  Do not create an abstraction before at least a real reusable need is
    established.

## 13. Forms and Controls

-   Group related fields.
-   Use clear labels; placeholders must not replace labels.
-   Keep validation messages near the relevant field.
-   Distinguish required, optional, disabled, read-only, invalid, and
    loading states.
-   Preserve entered values when validation fails where appropriate.
-   Keep form actions in predictable locations.
-   Make destructive actions clear but visually secondary to the primary
    action.
-   Ensure controls remain usable on mobile.
-   Do not use color as the only error indicator.

## 14. Empty, Loading, Error, and Success States

Every data-driven page and component must account for its real states.

### Empty

-   Use a short title and one useful explanation.
-   Offer an action only when the user can advance the state from that
    location.
-   Do not use oversized blank panels.
-   Do not show fake sample records as if they belong to the user.

### Loading

-   Use a proportionate loading indicator or skeleton when it improves
    perceived continuity.
-   Avoid unnecessary full-page loading states for small background
    updates.
-   Preserve existing data during background refetch where appropriate.

### Error

-   Explain what failed in user-understandable language.
-   Provide a retry action when retry is meaningful.
-   Do not show duplicate error banners for the same failure.
-   Do not disguise failed requests as empty data.

### Success

-   Confirm meaningful completed actions.
-   Avoid unnecessary celebratory effects for routine financial
    operations.
-   Keep confirmation feedback concise.

## 15. Navigation and Clickability

1.  Use links for navigation and buttons for actions.
2.  Make a summary metric clickable only when a real destination exists.
3.  Do not imply clickability through hover styling when no action
    exists.
4.  Interactive cards must support keyboard navigation and visible
    focus.
5.  Icon-only actions require accessible labels.
6.  Keep filters next to the data they affect.
7.  Keep page-level primary actions near the page heading.
8.  Place destructive actions in appropriate secondary controls and
    require confirmation when the action warrants it.

## 16. Responsive and Mobile Rules

Design for narrow mobile, standard mobile, tablet, desktop, and wide
desktop.

Mandatory viewport checks:

-   320px.
-   360px.
-   390px--430px.
-   768px.
-   1024px.
-   1366px.
-   1920px.

Rules:

1.  Never allow page-level horizontal overflow.
2.  Do not use static grid minimum widths that exceed the available
    viewport.
3.  Use responsive grid definitions that can shrink below the preferred
    card width.
4.  Add `min-width: 0` to flex/grid children where content must be
    allowed to shrink.
5.  Long titles, account names, and metadata must wrap or truncate
    intentionally.
6.  Badges and actions must not clip against viewport edges.
7.  Horizontal tab rails may scroll within their own container but must
    not cause page overflow.
8.  Switch to a one-column layout when two columns become cramped.
9.  Do not simply squeeze desktop tables and navigation into mobile.
10. Ensure sticky headers, dialogs, and bottom controls do not cover
    essential content.
11. Test intermediate widths, including when browser DevTools is open.
12. Mobile must feel intentionally designed, not merely compressed.

Example of a safer responsive grid:

``` css
.grid {
  display: grid;
  grid-template-columns: repeat(
    auto-fill,
    minmax(min(100%, 18rem), 1fr)
  );
  gap: var(--space-4);
  width: 100%;
  min-width: 0;
}
```

For horizontally scrolling tab rails:

``` css
.tabRail {
  width: 100%;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: none;
}
```

## 17. Accessibility

Target WCAG 2.2 AA for applicable UI.

Requirements: - Sufficient text and interface contrast. - Visible
`:focus-visible` states. - Keyboard-operable controls and navigation. -
Accessible labels and names. - Logical heading hierarchy. - Appropriate
semantics. - Reduced-motion support. - Adequate interactive target
sizes. - No color-only communication of financial meaning. - Zoom and
text resizing must not make core functionality unusable.

Check contrast against the actual surface on which a token is used, in
both themes.

## 18. Charts and Future Analytics

Prepare a consistent visualization style without inventing analytics
functionality.

Chart styling must define: - Plot and container surfaces. - Axis
labels. - Grid lines. - Legends. - Tooltips. - Series colors. - Positive
and negative series. - Hover and selection states.

Rules: - Charts must remain legible in both themes. - Avoid excessive
colors. - Use a considered categorical palette. - Do not use the brand
accent as the only way to distinguish series. - Keep legends and labels
concise. - Do not display mock chart data as real user data.

## 19. Internationalization and Content Resilience

Design components to tolerate: - Longer names and labels. - Different
currency symbols and formats. - Different date formats. - Larger text
settings. - Future right-to-left layouts where required.

Do not hardcode assumptions that every value, label, or currency has the
same length.

Use locale-aware formatting at the application/data presentation layer;
styling must not break when formatted content becomes longer.

## 20. Minimalization Process for Every Page

Follow this sequence when creating or redesigning a page:

1.  Inventory all visible elements.
2.  Identify the page's primary user job.
3.  Classify elements as primary, secondary, supporting, or removable.
4.  Remove duplicate navigation and repeated labels.
5.  Remove generic explanatory copy.
6.  Group related metrics and data.
7.  Put filters and actions near the content they affect.
8.  Make useful summaries navigable only when a real destination exists.
9.  Compact empty states.
10. Normalize spacing, alignment, and density.
11. Reduce unnecessary borders, shadows, colors, and decoration.
12. Check financial value formatting and semantic meaning.
13. Design the mobile layout deliberately.
14. Check loading, empty, error, and success states.
15. Remove stale CSS selectors, dead JSX, and obsolete component states.
16. Run the relevant build, lint, and test checks.
17. Inspect the rendered result rather than relying only on source-code
    review.

## 21. Quality Gates

A page is not complete until all applicable checks pass:

1.  The page has a clear purpose and hierarchy.
2.  The most visually prominent element deserves that attention.
3.  Every section provides useful information or an action.
4.  No generic filler copy remains.
5.  Empty states are compact and truthful.
6.  Main actions are easy to find.
7.  Secondary actions do not dominate.
8.  Colors encode brand, hierarchy, or meaning---not decoration alone.
9.  Borders and shadows are restrained.
10. Shared shell patterns are consistent.
11. Both themes render correctly.
12. All required viewport sizes are checked.
13. There is no unintended horizontal overflow.
14. Long content does not clip.
15. Loading and error states are handled correctly.
16. No stale selectors, duplicate overridden rules, or unused component
    states remain.
17. Build and targeted tests pass.
18. Lint results are reported accurately, distinguishing changed-file
    failures from existing repository-wide issues.
19. The rendered page has been visually inspected.

## 22. Rules for AI Coding Agents and Contributors

1.  Read the existing code and relevant project documentation before
    changing UI.
2.  Inspect existing shared components and tokens before creating new
    ones.
3.  Follow this rulebook for every page and component.
4.  Keep changes scoped to the requested page, shared components, and
    shell elements genuinely required.
5.  Do not introduce a parallel design system.
6.  Do not introduce SCSS.
7.  Use CSS Modules for component-specific styles.
8.  Use semantic design tokens; do not scatter palette hex values across
    components.
9.  Do not duplicate a shared component inside a feature module.
10. Do not leave obsolete CSS, hidden prototype elements, dead imports,
    or unused props after a redesign.
11. Do not claim a visual change is complete without inspecting the
    rendered result.
12. Do not claim tests passed unless they were actually run and passed.
13. Do not fabricate financial data or functionality to make a page look
    populated.
14. Preserve existing business logic, API contracts, and data behavior
    unless the task explicitly requires changing them.
15. Prefer small, reviewable, feature-scoped changes.
16. Document any necessary deviation from this rulebook and explain why
    it is justified.

## 23. Design Review Questions

Ask during every UI review:

1.  What can the user understand or do in five seconds?
2.  What is the most important information on this page?
3.  Is that information receiving the correct visual priority?
4.  Is any text explaining something obvious?
5.  Are there borders where spacing or surface contrast would be enough?
6.  Are colors communicating meaning or adding noise?
7.  Can users distinguish actual, estimated, and unavailable data?
8.  Does the page work with empty, loading, and error data states?
9.  Does it work with long names, large values, and different
    currencies?
10. Does it work at 320px and intermediate viewport widths?
11. Does mobile feel intentionally designed?
12. Does the page look consistent in both selected themes?
13. Are all interactive elements genuinely actionable and accessible?
14. Has stale code from earlier design iterations been removed?

## 24. Project-Level Styling Governance

-   This rulebook is the baseline for new UI work and redesigns.
-   Changes to global tokens must be reviewed for impact on both themes
    and all shared components.
-   Shared component changes must be checked against their existing
    consumers.
-   Feature modules may extend composition but must not redefine global
    design decisions.
-   New tokens must have a clear reusable purpose.
-   New shared components must include documented variants, states, and
    accessibility expectations.
-   Theme changes must be verified across representative pages, not just
    the page where the change was made.
-   If a rule must be broken for a genuine product requirement, document
    the exception rather than silently creating a competing convention.

------------------------------------------------------------------------

## Final Principle

**The design system owns consistency. CSS Modules own component
isolation. Feature modules own page-specific composition. The UI
rulebook owns the product-wide experience.**

Every page should be minimal without becoming empty, information-dense
without becoming crowded, visually consistent without becoming
repetitive, and usable across both themes and all supported screen
sizes.

