# Rewrite Narrative

Rewrite an existing Reidar's Rapport narrative using the current narrative guide and reference docs.

## Arguments

$ARGUMENTS — A gameweek identifier. Parse the arguments string for:

**Gameweek** (required): one of:
- A number: `27`
- A prefixed number: `gw27`
- A full path: `docs/narratives/2025-26/1638989/gw27.md`

Default league: `1638989`. Default season: `2025-26`. Override by passing a full path.

Examples:
- `/rewrite-narrative 27` — rewrite GW27
- `/rewrite-narrative gw27`
- `/rewrite-narrative docs/narratives/2025-26/1638989/gw27.md`

## Instructions

You are rewriting an existing narrative markdown file. You are NOT calling the Anthropic API. You ARE the writer. Write in Reidar's voice.

### Step 1: Resolve the narrative file

Parse $ARGUMENTS to find the narrative markdown file:
- If it's a number or `gwN`, resolve to `docs/narratives/2025-26/1638989/gw{N}.md`
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
8. **Recent GW summaries**: the last 5 `gw{N}.md` files in `weekly_report/reidar_memory/{league_id}/{season}/gameweeks/` before the current gameweek

Also read the previous gameweek's narrative for continuity:
9. **Previous narrative**: `weekly_report/narratives/{league_id}/{season}/gw{N-1}.md` (if it exists)

### Step 3: Rewrite the narrative

Using all the context above, rewrite the narrative following the persona and narrative guide exactly. Key requirements:

- **The first line MUST be a `# ` heading** with a punchy, clickbait-style headline (NEVER "Reidars Rapport — Runde N")
- **The second line MUST be the image line**: `![Reidars Rapport](../../reidars_rapport_N.png)` — pick N from 1–5, and don't always pick the same one
- Write in Norwegian bokmål, in Reidar's voice
- Pick a shape from NARRATIVE_GUIDE.md's shape menu (Spalten unless the round calls for another) and stay inside that shape's word budget and device suggestions; markup for each device is in `weekly_report/DEVICE_PALETTE.md`
- Use the report JSON as the source of truth for all stats and facts
- Maintain continuity with the previous narrative and memory context
- Obey NARRATIVE_GUIDE.md's hard constraints exactly, then verify with `source .venv/bin/activate && python -m fpl.style_lint <file>` before showing the result

### Step 4: Save

1. Show the user the rewritten narrative and ask for approval before saving
2. Once approved, save the narrative to the original file path (overwriting the old version)

### Step 5: Inform the user

Tell the user they can preview the narrative at:
`docs/reidars_rapport.html?gw={N}` (the dynamic article page renders markdown client-side).
