import json
import sys
from pathlib import Path
from fpl import FPL_API, FPLLeague

if __name__ == "__main__":
    # You can change this to your actual league ID if needed
    LEAGUE_ID = FPL_API.SAMPLE_LEAGUE_ID
    dev_mode = '--dev' in sys.argv
    fpl = FPL_API(dev_mode=dev_mode)
    league = FPLLeague(LEAGUE_ID, fpl)
    summary = league.get_summary()

    out_dir = Path("fpl/sample_data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"test_league_summary_{LEAGUE_ID}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote league summary to {out_path}")
