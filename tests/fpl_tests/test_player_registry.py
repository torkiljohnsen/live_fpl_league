from fpl.player_registry import PlayerRegistry


def _make_bootstrap(elements=None, teams=None, element_types=None):
    """Build a minimal bootstrap-static fixture."""
    return {
        "elements": elements or [],
        "teams": teams or [],
        "element_types": element_types or [],
    }


SAMPLE_ELEMENT_TYPES = [
    {"id": 1, "singular_name": "Goalkeeper"},
    {"id": 2, "singular_name": "Defender"},
    {"id": 3, "singular_name": "Midfielder"},
    {"id": 4, "singular_name": "Forward"},
]

SAMPLE_TEAMS = [
    {"code": 3, "id": 1, "name": "Arsenal"},
    {"code": 8, "id": 6, "name": "Chelsea"},
    {"code": 14, "id": 11, "name": "Liverpool"},
]

SAMPLE_ELEMENTS = [
    {
        "id": 1,
        "first_name": "David",
        "second_name": "Raya",
        "team": 1,
        "team_code": 3,
        "element_type": 1,
    },
    {
        "id": 328,
        "first_name": "Mohamed",
        "second_name": "Salah",
        "team": 11,
        "team_code": 14,
        "element_type": 3,
    },
    {
        "id": 200,
        "first_name": "Cole",
        "second_name": "Palmer",
        "team": 6,
        "team_code": 8,
        "element_type": 3,
    },
]


class TestPlayerRegistryGetPlayerName:
    def test_returns_full_name(self):
        registry = PlayerRegistry(
            _make_bootstrap(SAMPLE_ELEMENTS, SAMPLE_TEAMS, SAMPLE_ELEMENT_TYPES)
        )
        assert registry.get_player_name(328) == "Mohamed Salah"
        assert registry.get_player_name(1) == "David Raya"

    def test_missing_id_returns_unknown(self):
        registry = PlayerRegistry(
            _make_bootstrap(SAMPLE_ELEMENTS, SAMPLE_TEAMS, SAMPLE_ELEMENT_TYPES)
        )
        assert registry.get_player_name(99999) == "Unknown Player"

    def test_empty_bootstrap(self):
        registry = PlayerRegistry(_make_bootstrap())
        assert registry.get_player_name(1) == "Unknown Player"


class TestPlayerRegistryGetPlayerInfo:
    def test_returns_correct_dict(self):
        registry = PlayerRegistry(
            _make_bootstrap(SAMPLE_ELEMENTS, SAMPLE_TEAMS, SAMPLE_ELEMENT_TYPES)
        )
        info = registry.get_player_info(328)
        assert info == {
            "name": "Mohamed Salah",
            "team": "Liverpool",
            "position": "Midfielder",
        }

    def test_goalkeeper_position(self):
        registry = PlayerRegistry(
            _make_bootstrap(SAMPLE_ELEMENTS, SAMPLE_TEAMS, SAMPLE_ELEMENT_TYPES)
        )
        info = registry.get_player_info(1)
        assert info["position"] == "Goalkeeper"
        assert info["team"] == "Arsenal"

    def test_missing_id_returns_unknown_dict(self):
        registry = PlayerRegistry(
            _make_bootstrap(SAMPLE_ELEMENTS, SAMPLE_TEAMS, SAMPLE_ELEMENT_TYPES)
        )
        info = registry.get_player_info(99999)
        assert info == {
            "name": "Unknown Player",
            "team": "Unknown Team",
            "position": "Unknown",
        }


class TestPlayerRegistryGetTeamName:
    def test_returns_team_name(self):
        registry = PlayerRegistry(
            _make_bootstrap(SAMPLE_ELEMENTS, SAMPLE_TEAMS, SAMPLE_ELEMENT_TYPES)
        )
        assert registry.get_team_name(3) == "Arsenal"
        assert registry.get_team_name(14) == "Liverpool"
        assert registry.get_team_name(8) == "Chelsea"

    def test_missing_team_code_returns_unknown(self):
        registry = PlayerRegistry(
            _make_bootstrap(SAMPLE_ELEMENTS, SAMPLE_TEAMS, SAMPLE_ELEMENT_TYPES)
        )
        assert registry.get_team_name(99999) == "Unknown Team"


class TestPlayerRegistryWithRealSample:
    """Test PlayerRegistry with the full bootstrap-static sample data."""

    def test_real_sample_loads(self):
        import json
        from pathlib import Path

        sample_path = (
            Path(__file__).parent / "data_samples" / "bootstrap-static_sample.json"
        )
        bootstrap = json.loads(sample_path.read_text(encoding="utf-8"))
        registry = PlayerRegistry(bootstrap)

        # Element ID 1 should be David Raya Martín from Arsenal
        name = registry.get_player_name(1)
        assert "David" in name
        assert "Raya" in name

        info = registry.get_player_info(1)
        assert info["team"] == "Arsenal"
        assert info["position"] == "Goalkeeper"

        # Arsenal team code is 3
        assert registry.get_team_name(3) == "Arsenal"
