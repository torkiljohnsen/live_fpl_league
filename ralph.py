"""ralph.py - Autonomous development loop using Claude Code.

Runs Claude Code in a loop, completing one PRD task per iteration.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

SCRIPT_DIR = Path(__file__).resolve().parent
PRD_DIR = SCRIPT_DIR / ".claude/prds"
DEFAULT_PRD = PRD_DIR / "prd.md"
PROMPT_FILE = SCRIPT_DIR / ".claude/prds/CLAUDE.md"
LOG_DIR = SCRIPT_DIR / ".claude/logs"

DEFAULT_ITERATIONS = 14
MAX_STALLS = 2
PAUSE_SECONDS = 2


# ── PRD text resolution ─────────────────────────────────────


WORKTREE_DIR = SCRIPT_DIR / ".claude/worktrees"


def _git_show(ref: str, rel_path: str) -> str | None:
    """Read a file from a git ref. Returns content or None."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{rel_path}"],
            capture_output=True, text=True, check=True,
            cwd=SCRIPT_DIR, encoding="utf-8",
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return None


def _git_ls_tree(ref: str, directory: str) -> list[str]:
    """List files under a directory in a git ref."""
    try:
        result = subprocess.run(
            ["git", "ls-tree", "--name-only", ref, f"{directory}/"],
            capture_output=True, text=True, check=True,
            cwd=SCRIPT_DIR, encoding="utf-8",
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []


def _read_prd_texts(prd: Path) -> list[str]:
    """Return text content of all task files from the best available source.

    Priority order:
    1. Worktree (agent is actively working)
    2. Feature branch — local then origin (agent committed but may not have pushed)
    3. Local file on current branch (fallback)
    """
    prd_dir = ".claude/prds"
    stem = prd.stem

    # 1. Try worktree
    wt_dir = WORKTREE_DIR / stem / ".claude" / "prds"
    if wt_dir.exists():
        phase_files = sorted(wt_dir.glob(f"{stem}-phase-*.md"))
        if phase_files:
            return [f.read_text(encoding="utf-8") for f in phase_files]
        wt_prd = wt_dir / prd.name
        if wt_prd.exists():
            return [wt_prd.read_text(encoding="utf-8")]

    # 2. Try feature branch (local first, then origin)
    for branch in [f"feature/{stem}", f"origin/feature/{stem}"]:
        files = _git_ls_tree(branch, prd_dir)
        if not files:
            continue
        phase_pattern = f"{stem}-phase-"
        phase_files = sorted(f for f in files if phase_pattern in Path(f).name)
        if phase_files:
            texts: list[str] = []
            for pf in phase_files:
                text = _git_show(branch, pf)
                if text:
                    texts.append(text)
            if texts:
                return texts
        # No phase files, try main PRD
        text = _git_show(branch, f"{prd_dir}/{prd.name}")
        if text:
            return [text]

    # 3. Fall back to local files
    phase_files = sorted(prd.parent.glob(f"{stem}-phase-*.md"))
    if phase_files:
        return [f.read_text(encoding="utf-8") for f in phase_files]
    if prd.exists():
        return [prd.read_text(encoding="utf-8")]
    # PRD files deleted by agent on final task — treat as all done
    return []


# ── PRD parsing ──────────────────────────────────────────────


def count_tasks(prd: Path) -> tuple[int, int]:
    """Return (total, done) task counts across all task files."""
    total = done = 0
    for text in _read_prd_texts(prd):
        total += len(re.findall(r'^\s+"passes":', text, re.MULTILINE))
        done += len(re.findall(r'^\s+"passes": true', text, re.MULTILINE))
    return total, done


def next_task_title(prd: Path) -> str | None:
    """Return the title of the first incomplete task across all task files."""
    for text in _read_prd_texts(prd):
        last_title = None
        for line in text.splitlines():
            if '"title"' in line and (m := re.search(r'"title":\s*"([^"]+)"', line)):
                last_title = m.group(1)
            if '"passes": false' in line and last_title:
                return last_title
    return None


def get_prd_title(prd: Path) -> str:
    """Return the first H1 heading from the PRD, or the filename stem."""
    texts = _read_prd_texts(prd)
    if texts:
        for line in texts[0].splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return prd.stem


# ── Signal detection ─────────────────────────────────────────


class Signal(Enum):
    DONE = "done"      # All PRD tasks already passed
    COMPLETE = "complete"  # Current task finished successfully
    STUCK = "stuck"    # Agent hit a blocker
    NONE = "none"      # No signal emitted


def parse_signal(output: str) -> tuple[Signal, str]:
    """Parse agent output for control signals. Returns (signal, detail)."""
    if "<promise>DONE</promise>" in output:
        return Signal.DONE, ""
    if "<promise>COMPLETE</promise>" in output:
        return Signal.COMPLETE, ""
    if m := re.search(r"<promise>STUCK:\s*([^<]+)", output):
        return Signal.STUCK, m.group(1).strip()
    return Signal.NONE, ""


# ── Display ──────────────────────────────────────────────────


def format_duration(seconds: float) -> str:
    """Format seconds as 'Xm Ys' or 'Xs'."""
    minutes, secs = divmod(int(seconds), 60)
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _show_session_summary(session_start: float, tasks_completed: int) -> None:
    """Print a session summary panel with duration and tasks completed."""
    duration = format_duration(time.time() - session_start)
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold]Duration[/]", duration)
    table.add_row("[bold]Tasks completed[/]", str(tasks_completed))
    console.print(Panel(table, title="Session Summary", border_style="cyan"))


def progress_bar(done: int, total: int) -> str:
    """Text progress bar: ████████░░░░ 8/14."""
    if total == 0:
        return "[dim]no tasks[/]"
    filled = int(20 * done / total)
    return f"[green]{'█' * filled}{'░' * (20 - filled)}[/] {done}/{total}"


def show_status(prd: Path) -> None:
    total, done = count_tasks(prd)
    title = next_task_title(prd)
    prd_title = get_prd_title(prd)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold]PRD[/]", f"[dim]{prd.name}[/]")
    table.add_row("[bold]Progress[/]", progress_bar(done, total))
    if title:
        table.add_row("[bold]Next task[/]", f"[yellow]{title}[/]")
    else:
        table.add_row("[bold]Status[/]", "[green]All tasks complete![/]")

    console.print(Panel(table, title=prd_title, border_style="cyan"))


def show_config(branch: str, prd: Path, done: int, total: int, max_iter: int) -> None:
    prd_title = get_prd_title(prd)
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold]Branch[/]", f"[red]{branch}[/]")
    table.add_row("[bold]PRD[/]", f"[dim]{prd.name}[/]")
    table.add_row("[bold]Progress[/]", progress_bar(done, total))
    table.add_row("[bold]Iterations[/]", str(max_iter))
    console.print()
    console.print(Panel(table, title=prd_title, border_style="cyan"))
    console.print()


# ── External commands ────────────────────────────────────────


def get_branch() -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def run_claude(prompt: str) -> str:
    """Run claude CLI with stream-json, printing text deltas in real time."""
    process = subprocess.Popen(
        [
            "claude", "-p", prompt,
            "--output-format", "stream-json",
            "--include-partial-messages",
            "--verbose",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    chunks: list[str] = []
    stdout = process.stdout
    assert stdout is not None
    try:
        for raw_line in stdout:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            # Extract text deltas from streaming events
            if event.get("type") == "stream_event":
                delta = event.get("event", {}).get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        console.print(text, end="", highlight=False, markup=False)
                        chunks.append(text)
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        raise
    # Print trailing newline if we output anything
    if chunks:
        console.print()
    return "".join(chunks)


# ── Loop ─────────────────────────────────────────────────────


def _signal_style(signal: Signal) -> str:
    """Return a Rich-styled string for a signal value."""
    match signal:
        case Signal.COMPLETE | Signal.DONE:
            return f"[green]{signal.value}[/]"
        case Signal.STUCK:
            return f"[red]{signal.value}[/]"
        case Signal.NONE:
            return f"[yellow]{signal.value}[/]"
        case _:
            return signal.value


def run_loop(prd: Path, max_iterations: int) -> None:
    """Execute the main agent loop."""
    prompt = PROMPT_FILE.read_text(encoding="utf-8").replace("<prd-name>", prd.stem)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stall_count = 0
    session_start = time.time()
    tasks_completed = 0

    try:
        for i in range(1, max_iterations + 1):
            console.rule(f"[bold cyan]Iteration {i}/{max_iterations}[/]")
            total, done_before = count_tasks(prd)
            console.print(progress_bar(done_before, total))

            # Capture next task title before the agent runs (it marks it done)
            task_title = next_task_title(prd)

            if task_title:
                console.print(f"[bold]Next task:[/] [yellow]{task_title}[/]")
            console.print(f"[dim]Started at {datetime.now().strftime('%H:%M:%S')}[/]")
            console.print()

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            log_file = LOG_DIR / f"iteration-{i}-{timestamp}.log"
            iter_start = time.time()

            output = run_claude(prompt)
            log_file.write_text(output, encoding="utf-8")

            iter_duration = format_duration(time.time() - iter_start)
            signal, detail = parse_signal(output)

            console.print()
            console.print(f"[bold]Iteration completed in {iter_duration}[/]")
            console.print(f"Signal: {_signal_style(signal)}")
            console.print(f"[dim]Log: {log_file}[/]")

            # Fetch latest refs so progress check reads from feature branch
            subprocess.run(
                ["git", "fetch", "origin", "--quiet"],
                capture_output=True, cwd=SCRIPT_DIR,
            )

            match signal:
                case Signal.DONE:
                    console.print("\n[green]All tasks already complete![/]")
                    _show_session_summary(session_start, tasks_completed)
                    return

                case Signal.STUCK:
                    console.print(f"\n[red][ERROR][/] Agent is stuck: {detail}")
                    _show_session_summary(session_start, tasks_completed)
                    sys.exit(1)

                case Signal.COMPLETE:
                    total, done = count_tasks(prd)
                    tasks_completed += 1
                    if total == 0:
                        # PRD files deleted by agent — all tasks were completed
                        console.print("\n[green]All tasks complete! (PRD cleaned up)[/]")
                        _show_session_summary(session_start, tasks_completed)
                        return
                    console.print(progress_bar(done, total))
                    if done >= total:
                        console.print(f"\n[green]All {total} tasks complete![/]")
                        _show_session_summary(session_start, tasks_completed)
                        return
                    stall_count = 0
                    console.print(f"[dim]Next action: continuing to iteration {i + 1}[/]")

                case Signal.NONE:
                    total, done = count_tasks(prd)
                    if done > done_before:
                        tasks_completed += done - done_before
                    if done >= total > 0:
                        console.print(f"\n[green]All {total} tasks complete![/]")
                        _show_session_summary(session_start, tasks_completed)
                        return
                    if done <= done_before:
                        stall_count += 1
                        console.print(f"[yellow][WARN][/] No signal and no progress (stall {stall_count}/{MAX_STALLS})")
                        if stall_count >= MAX_STALLS:
                            console.print(f"[red][ERROR][/] Stalled {MAX_STALLS} consecutive iterations. Stopping.")
                            _show_session_summary(session_start, tasks_completed)
                            sys.exit(1)
                    else:
                        stall_count = 0
                    console.print(f"[dim]Next action: continuing to iteration {i + 1}[/]")

            if i < max_iterations:
                elapsed = format_duration(time.time() - session_start)
                console.print(f"\n[dim]Session: {elapsed} elapsed, {tasks_completed} task(s) completed[/]")
                console.rule(style="dim")
                for remaining in range(PAUSE_SECONDS, 0, -1):
                    console.print(f"[dim]Next iteration in {remaining}s...[/]", end="\r")
                    time.sleep(1)
                console.print(" " * 40, end="\r")  # clear countdown line

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/]")
        _show_session_summary(session_start, tasks_completed)
        return

    total, done = count_tasks(prd)
    console.print(
        f"\n[yellow]Reached {max_iterations} iterations ({done}/{total} tasks done). Run again to continue.[/]"
    )
    _show_session_summary(session_start, tasks_completed)


# ── PRD listing ─────────────────────────────────────────────


def list_prds() -> list[Path]:
    """Find top-level PRD files (excludes phase files, activity logs, and AGENTS.md)."""
    if not PRD_DIR.exists():
        return []
    results: list[Path] = []
    for p in PRD_DIR.glob("*.md"):
        if p.name in ("CLAUDE.md", "lessons.md") or p.name.endswith("-activity.md"):
            continue
        # Exclude phase files: {stem}-phase-{label}.md where {stem}.md exists
        m = re.match(r"^(.+)-phase-.+\.md$", p.name)
        if m and (PRD_DIR / f"{m.group(1)}.md").exists():
            continue
        results.append(p)
    return sorted(results)


def show_prd_list() -> None:
    """Display available PRDs with task progress."""
    prds = list_prds()
    if not prds:
        console.print(f"[yellow]No PRD files found in {PRD_DIR.relative_to(SCRIPT_DIR)}[/]")
        return

    table = Table(title="Available PRDs", show_lines=True)
    table.add_column("File", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Progress", justify="center")
    table.add_column("Next Task", style="yellow")

    for prd in prds:
        total, done = count_tasks(prd)
        prd_title = get_prd_title(prd)
        title = next_task_title(prd)
        table.add_row(
            prd.name,
            prd_title,
            progress_bar(done, total),
            title or "[green]Complete[/]",
        )

    console.print(table)


# ── PATH fix ────────────────────────────────────────────────


def ensure_uv_in_path() -> None:
    """Ensure uv is discoverable by child processes (claude).

    On some environments (e.g. Windows Git Bash), uv may be in PATH for the
    current shell but not inherited by subprocesses. Explicitly add its
    directory to PATH so `claude` and its internal Bash tool can find it.
    """
    uv_path = shutil.which("uv")
    if uv_path:
        uv_dir = str(Path(uv_path).resolve().parent)
        current_path = os.environ.get("PATH", "")
        if uv_dir not in current_path:
            os.environ["PATH"] = uv_dir + os.pathsep + current_path


# ── CLI ──────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Autonomous development loop using Claude Code. Completes one PRD task per iteration.",
        epilog="""examples:
  python ralph.py                                        Run default PRD (.claude/prds/prd.md)
  python ralph.py --prd .claude/prds/prd-refactor.md    Run a specific PRD
  python ralph.py --prd .claude/prds/prd-refactor.md 5  Run 5 iterations on a specific PRD
  python ralph.py --list                                 List all PRDs with progress
  python ralph.py --status                               Show progress for default PRD
  python ralph.py --prd .claude/prds/prd-refactor.md --status
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "max_iterations",
        nargs="?",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"maximum iterations to run (default: {DEFAULT_ITERATIONS})",
    )
    parser.add_argument(
        "--prd",
        type=Path,
        default=DEFAULT_PRD,
        help=f"path to PRD file (default: {DEFAULT_PRD.relative_to(SCRIPT_DIR)})",
    )
    parser.add_argument("--list", action="store_true", help="list all PRDs in .claude/prds/ with progress")
    parser.add_argument("-n", "--dry-run", action="store_true", help="show config without executing")
    parser.add_argument("--status", action="store_true", help="show current task progress")
    args = parser.parse_args()
    prd = args.prd.resolve()

    if args.list:
        show_prd_list()
        return

    if args.status:
        show_status(prd)
        return

    # Preflight checks
    if not shutil.which("uv"):
        console.print("[red][ERROR][/] uv not found in PATH.")
        sys.exit(1)
    ensure_uv_in_path()

    if not prd.exists():
        console.print(f"[red][ERROR][/] PRD not found: {prd}")
        sys.exit(1)
    if not PROMPT_FILE.exists():
        console.print(f"[red][ERROR][/] Prompt not found: {PROMPT_FILE}")
        sys.exit(1)

    branch = get_branch()
    # Fetch so we can read PRD progress from feature branches
    subprocess.run(
        ["git", "fetch", "origin", "--quiet"],
        capture_output=True, cwd=SCRIPT_DIR,
    )
    total, done = count_tasks(prd)

    if done >= total > 0:
        console.print(f"[green]All {total} tasks already complete![/]")
        return

    show_config(branch, prd, done, total, args.max_iterations)

    if args.dry_run:
        console.print(r'[dim]\[DRY RUN] Would run: claude -p "<prompt>" --output-format text[/]')
        return

    run_loop(prd, args.max_iterations)


if __name__ == "__main__":
    main()
