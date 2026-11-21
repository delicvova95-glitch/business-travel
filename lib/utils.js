// Минимальная реализация cn (как в shadcn/ui, но без зависимостей) —
// нужна компоненту для объединения CSS-классов.
export function cn(...inputs) {
  return inputs.filter(Boolean).join(" ");
}
