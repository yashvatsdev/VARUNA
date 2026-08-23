# ADR-0001 — Package layout: `packages/varuna_*` as one distribution

**Status:** Accepted · **Date:** 24 Aug 2026 · **Deciders:** architecture

## Context

The v2 target structure specifies `packages/contracts/`, `packages/netra/`,
`packages/alerts/`, and so on. Taken literally with `package-dir = {"" = "packages"}`,
that yields top-level importable modules named `contracts`, `netra`, `domain`, `alerts`,
`missions`. Several of these are generic enough to collide with third-party
distributions on `sys.path`, and `domain` and `contracts` in particular are common names.

Separately, making each `packages/*` a genuinely independent installable distribution
would require one `pyproject.toml` per package plus inter-package version pinning — real
overhead for a four-person team shipping in seven days, with no benefit while everything
is deployed as a single unit.

## Decision

One distribution, `varuna-grid`, with source root `packages/` and each package named
`varuna_<module>`:

```
packages/varuna_contracts/   → import varuna_contracts
packages/varuna_netra/       → import varuna_netra
```

`pyproject.toml` sets `package-dir = {"" = "packages"}` and discovers `varuna_*`.

## Consequences

**Positive**
- No top-level namespace collisions; `varuna_` prefix makes provenance obvious in tracebacks.
- One `pip install -e .` installs everything; no inter-package version matrix.
- Module boundaries are still enforced — by the dependency rules in
  `LLM_IMPLEMENTATION_GUIDE.md` §7 and by import-linting, not by packaging.

**Negative**
- Package boundaries are a convention rather than a hard packaging constraint. A developer
  *can* import across a forbidden edge; CI must catch it.
- Splitting a package out later means a rename.

**Mitigation**
- The dependency graph is documented and should be enforced by an import-cycle check in CI.
- `varuna_contracts` depends on nothing, which is the boundary that actually matters.

## Rejected alternatives

1. **Literal `packages/contracts/`** — namespace collision risk on generic names.
2. **Independent distributions per package** — version-pinning overhead with no deployment benefit at this scale.
3. **Flat `src/varuna/`** — loses the visible module boundary the architecture depends on.
4. **Keep v1 `src/`** — does not express the v2 package structure at all.
