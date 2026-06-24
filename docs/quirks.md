# Inventor COM Quirks

Inventor COM automation is stateful and Windows-only.

Current avoidance rules:

- Generate a `FeaturePlan` before touching COM.
- Create base solids before center bores.
- Defer bores until after joined flange geometry exists.
- Use millimeters in public APIs and convert to centimeters only inside the backend.
- Copy user-provided part templates before passing them to Inventor.
- Keep the backend limited to supported high-level feature steps.
