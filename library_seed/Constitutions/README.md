# library_seed/Constitutions

Mirror of `docs/governance/` at seed time — what `tools/seed_library.py`
(Lane A) installs to `LIBRARY\Constitutions\`. `docs/governance/` is the
source of truth; if these ever diverge, `docs/governance/` wins. Kept as
a mirror rather than a symlink because git tracks real files across
platforms (this repo runs on Windows in production).

Re-sync after any `docs/governance/` change:
```
cp docs/governance/*.md library_seed/Constitutions/
```
(excluding this README).
