# J5 Relationship Rendering SYSIDE Fixture

The first J5 integration experiment exposed a real semantic integration issue:
`allocate` requires Feature endpoints, while the first J4 renderer emitted
ActionDefinition/PartDefinition elements. SYSIDE correctly rejected those
endpoints.

The corrected fixture uses individual SysML usages/features:

```text
part IME_000001 { ... }
part IME_000002 { ... }
action IME_000003 { ... }

dependency from IME_000001 to IME_000002;
allocate IME_000003 to IME_000002;
```

This matches the project meaning of an IEM element as an individual reviewed
engineering element rather than a reusable type declaration.

After the focused tests, open and visualize this one file in SYSIDE. The desired
result is:

- no `Expected Feature element` reference errors,
- the dependency is recognized,
- the allocation is recognized,
- the generated `part` and `action` elements are usages/features.

Unused-definition warnings should also disappear because the fixture no longer
creates standalone part/action definitions.

`satisfies` remains intentionally blocked and is handled separately after this
integration check.
