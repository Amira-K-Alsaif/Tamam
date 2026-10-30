# Frontend Agent Instructions

Read the root `CLAUDE.md` first. This file adds the frontend rules.

## Structure

    src/
      App.tsx             routes: one per module, inside the app shell
      lib/api.ts          the only place that calls the backend
      lib/mockEmployee.ts the signed-in employee until auth lands
      components/         shared components (shell, buttons, cards, badges, ...)
      pages/HomePage.tsx  the home page
      modules/modules.ts  the module list: menu, routes, and home page cards
      modules/<module>/   one folder per module, owned by that module's owner
      index.css           Tailwind import and the design tokens
      test/setup.ts       test setup

- Module folders use the kebab-case ids from `modules.ts` (`org-map`, not `orgMap`).
- Each module's page starts as `modules/<module>/<Name>Page.tsx` rendering
  `ModuleStarter`. Its owner replaces that with the real screen.
- Components used inside one module stay in that module's folder. A component moves to
  `src/components/` only once a second module needs it.

## Shared components

Use these before writing your own. Changing one affects every module, so say so in the PR.

| Component | Use it for |
|---|---|
| `AppShell` | The side menu and page frame. Every route renders inside it. |
| `PageHeader` | The title, description, and actions at the top of every page. |
| `Card` | A surface that groups related content, with an optional title and action. |
| `Button`, `ButtonLink` | `primary` for the main action, `secondary` for the rest, `ai` for actions the assistant performs. |
| `StatusBadge` | `done`, `in-progress`, `missing`, `failed`, with an optional custom label. |
| `ProgressBar` | Any percentage: onboarding progress, readiness, skill level. |
| `Diamond` | The brand marker: list bullets and completed steps. |

## API boundary

- All backend calls go through `src/lib/api.ts` or module API files built on its helpers.
  Do not call `fetch` from components.
- The backend URL comes from `VITE_API_BASE_URL` (see `.env.example`).
- Response types mirror the backend contracts in `docs/team.md`.

## Styling

- Tailwind utilities mapped onto the tokens in `src/index.css`
  (`bg-surface`, `text-muted`, `text-mint`, `border-line`, `font-display`, ...).
- The app is dark: `night` is the page, `sidebar` and `sunken` sit below it, `surface` and
  `raised` sit above it. Mint is the primary accent, blue the secondary.
- `bg-aurora` (the mint-to-blue gradient) is only for AI moments: the assistant, `ai`
  buttons, and completion. Do not use it as decoration.
- No raw hex colors or arbitrary values in components. Add a token instead, and explain it
  in the pull request.
- No other CSS or component framework (no MUI, Bootstrap, Chakra, Ant Design).
- Icons come only from `lucide-react`. Decorative icons get `aria-hidden`.

## RTL and Arabic

- `index.html` sets `lang="ar" dir="rtl"`. Do not override it per page.
- Use logical utilities: `ms-*`, `me-*`, `ps-*`, `pe-*`, `start-*`, `end-*`, `text-start`.
- Do not reverse flex rows manually to "fix" RTL.
- Directional icons (arrows, chevrons) must point the right way in RTL.
- All copy is Arabic. Keep it short and clear.

## States

Every screen that loads data handles loading, empty, error, and success.
AI features also show a processing state while an answer streams or generates.
Error messages say what to do next, in Arabic.

## Accessibility

- Semantic elements (`button`, `nav`, `main`, headings in order).
- Every form control has a label. Keyboard focus is visible.
- Do not rely on color alone to show state.

## React and TypeScript

- Function components and hooks only.
- No `any`. Type API responses explicitly.
- Keep components small; move non-rendering logic into hooks or `lib/`.

## Tests

- Vitest + Testing Library. Test what the user sees (text, roles), not implementation details.
- Stub `fetch` in tests; never call a real backend.

Commands:

    npm ci
    npm run dev
    npm run lint && npm test && npm run build
