# Claims register schema

The claims register is **data** (`claims.yaml` at the repo root), decoupled from
the engine that evaluates it. Its shape is governed by a machine-readable schema in
`src/quran_analysis/claims/schema.py`. That Pydantic v2 model is the **single source
of truth**; the committed `src/quran_analysis/claims/claims.schema.json` is a derived
JSON Schema generated from it.

Both the research task (which authors `claims.yaml`) and the claim-runner (which
loads and evaluates it) build against this schema, so it is authored slightly ahead
of strict need: every field a researched entry will require is already present.

## Models

- **`Claim`** — one quantifiable claim about the Arabic text of the Quran.
- **`ClaimsRegister`** — `{claims: [Claim, ...]}`; enforces that all `id`s are unique.

Both set `model_config = ConfigDict(extra="forbid")`: an unknown or typo'd key (e.g.
`asserted` instead of `asserted_value`) raises a `ValidationError` rather than being
silently dropped, catching authoring mistakes early.

## `Claim` fields

| field | type | required | notes |
|---|---|---|---|
| `id` | `str` | yes | unique slug, pattern `^[a-z0-9][a-z0-9_-]*$` (lowercase, digits, `_`, `-`; starts alphanumeric) |
| `description` | `str` | yes | short human description; non-empty |
| `source` | `str` | yes | citation / where the claim circulates; non-empty |
| `asserted_value` | `int \| str` | yes | exact asserted quantity. See convention below |
| `operational_definition` | `str` | yes | **self-contained**: states this claim's own basmala + diacritic handling and which forms/roots/lemmas count; non-empty |
| `expected_result` | `str` | yes | expected outcome if the claim is true (e.g. `count == 365`, `count(life) == count(death)`) |
| `requires_morphology` | `bool` | no (default `False`) | flags claims needing root/lemma analysis; drives the optional morphology task and the runner |
| `ambiguity_note` | `str \| None` | no (default `None`) | set when the counting convention is undisclosed/non-deterministic; the runner resolves such claims to `ambiguous` rather than forcing a verdict |
| `rederivation_note` | `str \| None` | no (default `None`) | evidence the assertion was re-derived from the Arabic text (research sources are treated as untrusted) |
| `tags` | `list[str]` | no (default `[]`) | optional categorisation (pair-count / constant / letter-freq / abjad / positional); convenience only, not load-bearing |

### `asserted_value` convention

- Use an **`int`** for numeric claims — `365`, `12`, `19`.
- Use a **`str`** for symbolic claims — e.g. `"equal"` for a pair-equality claim. The
  runner interprets the symbolic value together with `expected_result`.
- **`float` is rejected** (counts are integers — keeps verdicts deterministic).
- **`bool` is rejected** even though Python's `bool` subclasses `int`: a YAML
  `true`/`false` is caught by a `mode="before"` field validator so it cannot be
  silently coerced to `1`/`0`.

## Loading

`load_register(path=DEFAULT_REGISTER_PATH) -> ClaimsRegister` reads the YAML
(`yaml.safe_load`) and validates it into models. `DEFAULT_REGISTER_PATH` is the
repo-root `claims.yaml`. The `path` override is the hook later tasks use to load a
small synthetic register fixture in tests. The claim-runner reuses this function —
it is the only entry point for turning the YAML register into validated models.

## Adding a claim

1. Add an entry to `claims.yaml` with all required fields, a self-contained
   `operational_definition`, and (if relevant) `requires_morphology`,
   `ambiguity_note`, `rederivation_note`, `tags`.
2. Run `make test` — `load_register()` validates the file; `extra="forbid"`,
   uniqueness and field constraints catch mistakes.

`extra="forbid"` is the intended open/closed flow: if a future ticket needs a new
field, add it to the model **and regenerate the JSON Schema** (below).

## Regenerating the JSON Schema

The committed `claims.schema.json` is generated from the model; a drift-guard test
(`test_committed_json_schema_matches_model`) fails if they diverge. Regenerate with:

```bash
uv run python -c "import json, quran_analysis.claims.schema as s; \
    print(json.dumps(s.json_schema(), indent=2, ensure_ascii=False))" \
    > src/quran_analysis/claims/claims.schema.json
```
