# Skill Graph for Analogical Reasoning

Skill Graph for Analogical Reasoning is a graph-powered retrieval engine for `SKILL.md`-based skills.

Its core claim is simple:

- do not send the model a pile of top-similar skills
- choose one primary skill instead
- retrieve only complementary support
- keep similar skills separate from default prompt context

That is the project’s attempt to make skill retrieval feel closer to human-style analogical reasoning and `举一反三`.

## Core commands

```bash
grap-skill build --source ./skills-main --output ./.grap-skill
grap-skill query "edit a docx file with comments" --graph ./.grap-skill/graph.json
grap-skill look --graph ./.grap-skill/graph.json --output ./.grap-skill/graph-look.html
```

## Public versions

- the GitHub repository is the Python package + CLI source
- the ClawHub/OpenClaw skill bundle is prepared as a separate release asset
