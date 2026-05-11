# grap-skill README

This directory packages the local `grap-skill` prototype as a standard skill bundle.

## What This Skill Is For

Use `grap-skill` when you want to:

- scan a directory of existing skills
- build or refresh a local skill graph
- query the graph for the best matching primary skill
- inspect which skills are connected to a given skill
- visualize the whole skill graph

## Important Behavior

- `build` is the only command that scans `SKILL.md` files and updates the graph
- `query`, `look`, `inspect`, and `stats` are read-only
- query must not silently rebuild the graph

## Prerequisite

Install the local project first from the repository root:

```bash
python -m pip install -e .
```

After that, the CLI command becomes available:

```bash
grap-skill
```

If this is used through the skill interface, the three main entry patterns should be treated as:

```text
/grap-skill build
/grap-skill query
/grap-skill look
```

## Basic Workflow

### 1. Build The Graph

Scan a skill directory and write `graph.json`:

```bash
grap-skill build --source ./skills-main --output ./.grap-skill
```

You can also point to a different skill directory:

```bash
grap-skill build --source ./skills --output ./.grap-skill
```

### 2. Query The Graph

Ask for the primary skill and related skills for a task:

```bash
grap-skill query "fill in a PDF form" --graph ./.grap-skill/graph.json
```

```bash
grap-skill query "create a technical spec decision doc" --graph ./.grap-skill/graph.json
```

```bash
grap-skill query "edit a docx file with comments" --graph ./.grap-skill/graph.json
```

### 3. Look At The Whole Graph

Render a whole-graph HTML visualization:

```bash
grap-skill look --graph ./.grap-skill/graph.json --output ./.grap-skill/graph-look.html
```

The generated page now supports two static graph views:

- `Similarity`: shows which skills are textually/structurally close
- `Complementarity`: shows a build-time proxy for "useful together without excessive redundancy"

### 4. Inspect A Skill Node

Look at a skill and its neighbors:

```bash
grap-skill inspect docx --graph ./.grap-skill/graph.json
```

### 5. Show Graph Stats

```bash
grap-skill stats --graph ./.grap-skill/graph.json
```

## Output Meaning

### Query status

`grap-skill query` may return:

- `ok`: a primary skill was selected
- `ambiguous`: top candidates are too close
- `no_primary_skill`: confidence is too low
- `no_match`: no runnable skill matched

### Result fields

- `primary_skill`: the single best skill for the task
- `supporting_skills`: complementary neighbors worth adding as supporting context
- `fallback_skills`: weaker alternatives, only for fallback
- `similar_skills`: nearby skills worth browsing, but usually not worth sending to the model context

## Suggested Usage Rule

Follow this pattern:

1. Run `build` after adding or changing skills
2. Run `query` for user tasks
3. Run `look` when you want the whole network visualized
4. Run `inspect` when debugging a single skill's neighbors
5. Run `stats` to quickly verify graph size and relation counts

## Release Targets

This repository also prepares two publish-oriented variants:

- a ClawHub upload folder that can be used as a plugin/marketplace release scaffold
- a gist-oriented markdown writeup for public explanation and sharing

These two release variants cross-reference each other so the public docs and the installable package stay connected.

If you publish publicly, also recommend:

- the GitHub/Python package version for users who want the full local CLI
- the ClawHub skill/package version for users who prefer skill installation flow

## Files In This Skill Bundle

- `SKILL.md`: behavior instructions for the skill system
- `README.md`: human-oriented usage guide
- `reference.md`: current prototype details and output interpretation
