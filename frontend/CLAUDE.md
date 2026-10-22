# Frontend Agent Instructions

Read the root `CLAUDE.md` first. This file adds the frontend rules.

## Structure

    src/
      lib/api.ts          the only place that calls the backend
      modules/modules.ts  the list of product modules shown on the home page
      modules/<module>/   one folder per module, owned by that module's owner
      index.css           Tailwind import and the design tokens
      test/setup.ts       test setup

- Module folders use the kebab-case ids from `modules.ts` (`procedure-map`, not `procedureMap`).
- A component shared by two or more modules goes in `src/components/`, and only once
  a second module actually needs it.

## API boundary

- All backend calls go through `src/lib/api.ts` or module API files built on its helpers.
  Do not call `fetch` from components.
- The backend URL comes from `VITE_API_BASE_URL` (see `.env.example`).
- Response types mirror the backend contracts in `docs/team.md`.

## Styling

- Tailwind utilities mapped onto the tokens in `src/index.css`
  (`bg-surface`, `text-muted`, `text-accent`, `font-display`, ...).
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
