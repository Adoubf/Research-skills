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

The example project is intentionally small but complete:

```bash
uv run research-figure-tool validate-figure examples/minimal-figure-project
```

## Installation

Package the skill for distribution:

```bash
uv run research-figure-tool pack-skill research-figure --out dist
```

The command writes `dist/research-figure/` and `dist/research-figure.zip`. The package
includes `SKILL.md`, `scripts/`, `references/`, optional Codex metadata under `agents/`,
and `LICENSE`.

Install for Codex in a repository:

```bash
mkdir -p .agents/skills
cp -R dist/research-figure .agents/skills/research-figure
```

Install for Codex as a user skill:

```bash
mkdir -p "$HOME/.agents/skills"
cp -R dist/research-figure "$HOME/.agents/skills/research-figure"
```

For Claude Code or other tools that support standard `SKILL.md` skills, import
`dist/research-figure.zip` or copy `dist/research-figure/` into that tool's user skill
directory. After installation, run the bundled helper from the skill root:

```bash
python scripts/research_figure_tool.py validate-skill .
python scripts/research_figure_tool.py validate-figure <project-dir>
```
