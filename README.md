# Research-skills

Multi-skill repository for research workflows.

## Skills

- `research-figure/`: create, reproduce, revise, and QA publication-grade scientific figures.

## Development

Use `uv` for Python commands:

```bash
uv run research-figure-tool validate-skill research-figure
uv run research-figure-tool validate-figure <project-dir>
uv run research-figure-tool pack-skill research-figure --out dist
```

The exported `dist/research-figure/` directory is the portable skill package for Codex,
Claude Code, and other agents that support the standard `SKILL.md` skill layout.
