# Rewrite Narrative

Rewrite an existing Reidar's Rapport narrative using the current narrative guide and reference docs.

## Arguments

$ARGUMENTS — A gameweek identifier, plus optional flags. Parse the arguments string for:

**Gameweek** (required): one of:
- A number: `27`
- A prefixed number: `gw27`
- A full path: `weekly_report/narratives/1638989/2025-26/gw27.md`

**Flags** (optional):
- `--render-html` — Also render the HTML article page after saving

Default league: `1638989`. Default season: `2025-26`. Override by passing a full path.

Examples:
- `/rewrite-narrative 27` — rewrite GW27, save markdown only
- `/rewrite-narrative gw27 --render-html` — rewrite GW27 and render HTML
- `/rewrite-narrative weekly_report/narratives/1638989/2025-26/gw27.md --render-html`

## Instructions

You are rewriting an existing narrative markdown file. You are NOT calling the Anthropic API. You ARE the writer. Write in Reidar's voice.

### Step 1: Resolve the narrative file

Parse $ARGUMENTS to find the narrative markdown file:
- If it's a number or `gwN`, resolve to `weekly_report/narratives/1638989/2025-26/gw{N}.md`
- If it's a full path, use it directly
- Confirm the file exists before proceeding. If not found, tell the user and stop.

Extract the gameweek number, league ID, and season from the resolved path.

### Step 2: Read all reference context

Read ALL of these files — they form the system prompt for narrative generation:

1. **Persona**: `weekly_report/REIDAR_PERSONA.md`
2. **Narrative guide**: `weekly_report/NARRATIVE_GUIDE.md`
3. **Examples**: `weekly_report/REIDAR_EXAMPLES.md`
4. **The existing narrative** being rewritten
5. **The report JSON**: `weekly_report/reports/{league_id}/{season}/gw{N}.json` — this is the structured gameweek data the narrative is based on. If it doesn't exist, warn the user but continue (rewrite based on the existing narrative content).

Read memory context files if they exist:
6. **Manager profiles**: all `.md` files in `weekly_report/reidar_memory/{league_id}/{season}/managers/`
7. **Season arc**: `weekly_report/reidar_memory/{league_id}/{season}/season_arc.md`
8. **Recent GW summaries**: the last 5 `gw{N}.md` files in `weekly_report/reidar_memory/{league_id}/{season}/gw_summaries/` before the current gameweek

Also read the previous gameweek's narrative for continuity:
9. **Previous narrative**: `weekly_report/narratives/{league_id}/{season}/gw{N-1}.md` (if it exists)

### Step 3: Rewrite the narrative

Using all the context above, rewrite the narrative following the persona and narrative guide exactly. Key requirements:

- **The first line MUST be a `# ` heading** with a punchy, clickbait-style headline (NEVER "Reidars Rapport — Runde N")
- **The second line MUST be the image line**: `![Reidars Rapport](../../reidars_rapport_2.png)`
- Write in Norwegian bokmål, in Reidar's voice
- Follow all formatting rules from NARRATIVE_GUIDE.md: subheadings, bold, short standalone lines, pull quotes (`>`), section dividers (`---`), short lists where natural
- Use the report JSON as the source of truth for all stats and facts
- Maintain continuity with the previous narrative and memory context
- Target 400-700 words

### Step 4: Save

1. Show the user the rewritten narrative and ask for approval before saving
2. Once approved, save the narrative to the original file path (overwriting the old version)

### Step 5: Render HTML (only if `--render-html` flag is present)

If `--render-html` was passed in the arguments:

1. Activate the venv and run:

```python
from fpl.narrative_html_renderer import NarrativeHTMLRenderer
from pathlib import Path

md = Path('{narrative_path}').read_text(encoding='utf-8')
renderer = NarrativeHTMLRenderer()
path = renderer.render(md, '{league_id}', '{league_name}', '{season}', {event_id})
print(f'Rendered: {path}')
```

Get the league name from the report JSON (`result["meta"]["league_name"]`), or fall back to "Sinkaberg administrasjon" for league 1638989.

2. Tell the user the HTML file path so they can preview it in a browser.

If `--render-html` was NOT passed, skip this step entirely.
