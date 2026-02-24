"""Player registry for mapping FPL element IDs to human-readable names."""

from typing import Any


class PlayerRegistry:
    """Maps FPL element IDs to player names and metadata.

    Builds lookup dicts once at construction from bootstrap-static data.
    No API calls — pure data transformation.
    """

    def __init__(self, bootstrap_data: dict[str, Any]) -> None:
        self._elements: dict[int, dict[str, Any]] = {}
        self._teams_by_code: dict[int, dict[str, Any]] = {}
        self._position_map: dict[int, str] = {}

        for et in bootstrap_data.get("element_types", []):
            self._position_map[et["id"]] = et["singular_name"]

        for team in bootstrap_data.get("teams", []):
            self._teams_by_code[team["code"]] = team

        for element in bootstrap_data.get("elements", []):
            self._elements[element["id"]] = element

    def get_player_name(self, element_id: int) -> str:
        """Return 'FirstName LastName' for the given element ID."""
        element = self._elements.get(element_id)
        if element is None:
            return "Unknown Player"
        return f"{element['first_name']} {element['second_name']}"

    def get_player_info(self, element_id: int) -> dict[str, Any]:
        """Return dict with name, team, and position for the given element ID."""
        element = self._elements.get(element_id)
        if element is None:
            return {"name": "Unknown Player", "team": "Unknown Team", "position": "Unknown"}

        team_code = element.get("team_code")
        team_name = self._teams_by_code.get(team_code, {}).get("name", "Unknown Team") if team_code else "Unknown Team"
        position = self._position_map.get(element.get("element_type", 0), "Unknown")

        return {
            "name": f"{element['first_name']} {element['second_name']}",
            "team": team_name,
            "position": position,
        }

    def get_team_name(self, team_code: int) -> str:
        """Return team name for the given team code."""
        team = self._teams_by_code.get(team_code)
        if team is None:
            return "Unknown Team"
        return team["name"]
