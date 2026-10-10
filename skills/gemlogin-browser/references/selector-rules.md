# Selector rules

Use live DOM evidence, not copied selectors from old workflow JSON.

1. Prefer `data-testid`, `aria-label`, semantic roles, `name`, `placeholder`, and stable `data-*` attributes.
2. Use `contains(., 'text')` for nested text; `contains(text(), ...)` often misses React descendants.
3. Scope selectors to the visible dialog, card, or form when the page has duplicate controls.
4. Reject selectors with zero or multiple matches unless the artifact explicitly records the ambiguity and index.
5. Treat generated React ids and volatile CSS classes as fallback evidence only.
6. After navigation or modal changes, recapture and re-verify selectors.
