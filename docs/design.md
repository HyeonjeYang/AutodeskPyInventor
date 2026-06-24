# Design

AutodeskPyInventor is an Inventor-safe geometry builder, not a FreeCAD clone and not a generic wrapper over every Inventor COM object.

The public API is millimeter-first. Recipes create a serializable `FeaturePlan` before any COM operation runs. The Inventor backend executes only known feature steps.

Supported first recipes:

- disk
- washer
- tube
- flanged tube

The planning layer exists so dry runs, unit tests, and CLI checks can run without Autodesk Inventor installed.
