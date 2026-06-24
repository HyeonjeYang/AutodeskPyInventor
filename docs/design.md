# Design

AutodeskPyInventor is an Inventor-safe geometry builder.

It is not a FreeCAD clone, an MCP server, or a generic wrapper over every Inventor COM object.
The library builds a `FeaturePlan` first, validates it, and only then executes it through a narrow
Inventor backend.

## Plan model

Core operations:

- `OuterCylinder`
- `DeferredCenterBore`
- `ApplyDeferredBores`

The flanged tube recipe orders operations as:

1. outer body cylinder
2. outer flange cylinder
3. deferred center bore
4. apply deferred bores

That ordering avoids repeated through-all cuts after each annulus.

## Execution model

The public API uses millimeters. Inventor length values are converted to centimeters only inside
the backend.

The backend supports only planned operations from this package. Arbitrary Inventor COM automation is
outside the v0.1 scope.
