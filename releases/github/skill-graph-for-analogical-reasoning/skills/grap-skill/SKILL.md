---
name: grap-skill
description: Build and query a graph over AgentSkills-compatible skill folders. Use this when the user wants to scan skills from disk, build or refresh a skill graph, retrieve a primary skill plus related skills for a task, or visualize the whole skill network.
---

# Grap Skill

This skill wraps the local `grap-skill` prototype in this repository.

The primary interaction surface should be treated as:

- `/grap-skill build`
- `/grap-skill query`
- `/grap-skill look`

Use it for two clearly separated phases:

1. **Offline graph build/update**
2. **Online graph query/inspection**

## Core Rule

- `grap-skill build` is the only command that may scan `SKILL.md` files and update the graph.
- `grap-skill query`, `grap-skill look`, `inspect`, and `stats` are read-only and must only use an existing `graph.json`.
- Do not silently rebuild the graph during query.

## When To Use

Use this skill when the user wants to:

- build a skill graph from an existing skill directory
- refresh a previously built graph after skills changed
- find the best matching skill for a task
- inspect related skills around a specific skill
- understand how local skills connect as a network
- visualize the whole skill graph

## Expected Inputs

Before running commands, determine:

- the skill source directory to scan
- the graph output path
- whether the user wants build, query, look, inspect, or stats

If the user does not give a source path for `build`, prefer common local locations such as:

- `./skills`
- `./skills-main`
- `<workspace>/skills`

If multiple plausible directories exist, ask which one to use.

## Local Setup

If the CLI is not installed yet, install the repository in editable mode from the project root:

```bash
python -m pip install -e .
```

## Main Commands

### `/grap-skill build`

```bash
grap-skill build --source <skills_dir> --output <graph_dir>
```

Example:

```bash
grap-skill build --source ./skills-main --output ./.grap-skill
```

### `/grap-skill query`

```bash
grap-skill query "<task text>" --graph <graph_json_path>
```

Example:

```bash
grap-skill query "fill in a PDF form" --graph ./.grap-skill/graph.json
```

### `/grap-skill look`

Render the whole graph as an HTML visualization:

```bash
grap-skill look --graph <graph_json_path> --output <html_path>
```

Example:

```bash
grap-skill look --graph ./.grap-skill/graph.json --output ./.grap-skill/graph-look.html
```

### Secondary Commands

### Inspect A Skill Node

```bash
grap-skill inspect <skill_id> --graph <graph_json_path>
```

Example:

```bash
grap-skill inspect docx --graph ./.grap-skill/graph.json
```

### Show Graph Stats

```bash
grap-skill stats --graph <graph_json_path>
```

## How To Respond

When using this skill:

- clearly state whether you are building, querying, or visualizing
- show the source path and graph path you used
- summarize the primary skill and related skills in plain language
- summarize the primary skill and any supporting skills in plain language
- mention if the result is `ok`, `ambiguous`, or `no_primary_skill`

For `/grap-skill look`:

- generate the HTML file explicitly
- report the output path
- describe the view as a whole-graph visualization, not as a rebuild step

For query results:

- treat `primary_skill` as the execution center
- treat `supporting_skills` as the only context that should normally supplement the primary skill
- treat `fallback_skills` as fallback options only
- treat `similar_skills` as graph exploration output, not default prompt context

## Query Semantics

The query algorithm is intentionally conservative:

- It first picks one `primary_skill`
- It does **not** then attach the most similar skills by default
- It only promotes neighbors into `supporting_skills` if they add complementary value
- It penalizes neighbors that are too redundant with the primary skill

Interpret the outputs as:

- `primary_skill`: the best execution center for the task
- `supporting_skills`: complementary skills that add missing coverage, execution detail, or constraints
- `fallback_skills`: substitutes to consider only if the primary path fails
- `similar_skills`: nearby skills useful for browsing the graph, but usually not worth sending to the model context

## Constraints

- This prototype currently builds a weakly supervised graph from `SKILL.md` alone.
- Strong relations such as prerequisite/composition are not guaranteed.
- If the graph quality looks weak, recommend rebuilding after improving skill descriptions or triggers rather than inventing hidden relations.

## Reference

See `reference.md` for the current prototype behavior and result interpretation.

## Cross Reference

If you are preparing a public release package:

- ClawHub-oriented packaging lives in the repository release assets
- GitHub/Python package users should be pointed to the main repository
- Long-form public writeup can also point to: `https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`
