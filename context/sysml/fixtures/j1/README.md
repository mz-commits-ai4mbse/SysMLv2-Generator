# Phase-J J1 SYSIDE Syntax Fixtures

These files are deliberately small syntax experiments for ADR-021 J-09.

Reference baseline:

```text
SysML v2 Release:
ee25530ed24b8c93a0e3e4b8d5fbfaa5a8d8ffb4

Apollo 11:
6e9c93fe7d80c5ca3534bb14b10ab374a643ef2d
```

The SysML v2 Release repository is the syntax/language reference.
Apollo 11 remains non-normative.

## Manual SYSIDE validation

On 2026-08-13 all four J1 fixtures were opened and visualized in SYSIDE.
The reviewer reported no observed errors for:

- Use Case Definition
- Dependency
- Allocation
- Satisfaction

The evidence manifest records this as a manual SYSIDE validation pass.

This authorizes the corresponding **syntax constructs** for inclusion in the
Target Notation Profile.

It does **not** yet authorize IEM → SysML production generation. Production
generation permission remains false until J2 adds an explicit Generation Profile
mapping for the applicable IEM semantic.

This distinction preserves ADR-021:

```text
syntax evidence
→ Target Notation authorization
→ explicit Generation Profile mapping
→ production generation
```
