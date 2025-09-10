from typing import Any, Dict, List

class ChipAnnotator:
    CHIP_ABBREVIATIONS: Dict[str, str] = {
        "wildcard": "WC",
        "freehit": "FH",
        "bboost": "BB",
        "3xc": "TC",
    }

    @classmethod
    def add_chips(cls, chips: List[Dict[str, Any]], finished_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for chip in chips:
            name = chip.get("name")
            if not isinstance(name, str):
                continue
            abbr = cls.CHIP_ABBREVIATIONS.get(name)
            chip_event = chip.get("event")
            if chip_event is None:
                continue
            for event in finished_history:
                if event["event"] == chip_event and abbr:
                    event["chip"] = abbr
        return finished_history
