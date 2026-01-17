---
applyTo: "front-analysis-app/**"
---

# React & Tailwind Implementation Rules

## 1. Technical Stack (Reference)

- **Runtime**: React 19 / Vite 7.2.7
- **Package Manager**: `pnpm`
- **Style**: Tailwind CSS 4 / Radix UI / `cn` utility (clsx + tailwind-merge)
- **Forms**: React Hook Form + Zod + useActionState

## 2. Naming Conventions

| Category             | Convention                 | Example                             |
| :------------------- | :------------------------- | :---------------------------------- |
| **Components**       | PascalCase                 | `InputText.tsx`, `AnalysisForm.tsx` |
| **Types/Interfaces** | PascalCase + `Type` suffix | `UserDataType`, `FormInputType`     |
| **Functions**        | camelCase                  | `calculateStatistics.ts`            |
| **Constants**        | SCREAMING_SNAKE_CASE       | `API_TIMEOUT_MS`                    |
| **Files (non-JSX)**  | camelCase                  | `useAuth.ts`, `apiClient.ts`        |

## 3. Component & JSX Rules

- **Component Type**: Functional components only. No class components.
- **Exports**: Named exports only. No default exports.
- **Props**: Always define with TypeScript `type`.
- **Logic Separation**: Extract complex logic from JSX into hooks or helper functions.
- **Conditionals**:
  - Use ternary operators for simple inline logic (< 10 lines).
  - Use logical `&&` or separate functions for complex rendering.
- **Lists**: Always provide a unique `key` prop when using `.map()`.

## 4. Directory Structure (Atomic Design)

- `src/components/atoms/`: Smallest UI elements (Button, Input). No logic.
- `src/components/molecules/`: Combinations of atoms. Minimal logic.
- `src/components/organisms/`: Complex UI blocks. Business logic & State allowed.
- `src/components/templates/`: Page layouts.
- `src/types/`: Type definitions (`commonTypes.ts`, `apiTypes.ts`).
- `src/function/`: Business logic and API calls.
- `src/common/`: Constants and style constants.

## 5. i18n Rule

- **Usage**: No hardcoded Japanese strings in JSX.
- **Key**: Always use `t("Key.Name")` from `react-i18next`.
- **Interpolation**: Use `t("Key", { var: value })` for dynamic values.

## 6. Styling with `cn`

- Always use the `cn()` utility when merging Tailwind classes or handling conditional styles.
- Example: `className={cn("base-style", isError && "border-red-500", className)}`
