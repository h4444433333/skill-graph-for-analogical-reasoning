# Grap Skill Reference

## Current Prototype

The local prototype lives in:

- `src/auto_grap_skill/core.py`
- `src/auto_grap_skill/cli.py`

The installed CLI command is:

```bash
grap-skill
```

## Build Behavior

`grap-skill build` currently:

- recursively scans for `SKILL.md` and `skill.md`
- parses frontmatter and markdown body
- extracts:
  - name
  - description
  - headings
  - trigger-like lines
  - code/tool references
  - basic runtime requirements
- builds a graph with weak relations such as:
  - `similar`
  - `tool_affinity`
  - `constraint_affinity`
  - `substitute`

The graph is written to:

```text
<output_dir>/graph.json
```

## Look Behavior

`grap-skill look`:

- reads an existing `graph.json`
- generates a standalone HTML visualization
- does not rebuild or mutate the graph

The default HTML output path is:

```text
.grap-skill/graph-look.html
```

## Query Behavior

`grap-skill query` returns one of these statuses:

- `ok`: a primary skill was selected
- `ambiguous`: top candidates were too close
- `no_primary_skill`: confidence was too low
- `no_match`: nothing runnable matched

## Result Interpretation

### `primary_skill`

- the single best skill for the task
- should be treated as the center of execution

### `supporting_skills`

- neighbors pulled from the built graph because they add complementary value
- should be treated as the default supporting context
- should stay sparse rather than repeating the primary skill

### `similar_skills`

- nearby nodes in the graph that remain relevant
- useful for graph browsing or fallback reasoning
- should not automatically be added to the LLM context

### `fallback_skills`

- weaker alternatives
- should not replace the primary skill unless fallback is needed

## Supporting Selection Logic

The prototype intentionally avoids sending the "most similar" skills as default context.

For each neighbor of the primary skill, it computes:

- `task_relevance`
- `complementarity`
- `execution_support`
- `redundancy_with_primary`

Then it derives a `support_score`:

```text
support_score =
  0.30 * task_relevance
  + 0.30 * complementarity
  + 0.25 * execution_support
  - 0.25 * redundancy_with_primary
```

Only neighbors with enough complementarity and low enough redundancy are promoted into `supporting_skills`.

## Important Constraint

Do not use `query` as a hidden rebuild step.

If the graph is missing or stale:

- tell the user
- run `grap-skill build` explicitly
- then query again
