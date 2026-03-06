from fpl import FPL_API, FPLAPIProtocol


def test_fpl_api_protocol_adherence() -> None:
	# This assignment will be checked by mypy for protocol adherence
	api: FPLAPIProtocol = FPL_API(dev_mode=True)
	# Optionally, call a method to ensure runtime compatibility (not required for mypy)
	assert hasattr(api, 'get_league_standings')
	assert hasattr(api, 'get_team')
	assert hasattr(api, 'get_team_history')
	assert hasattr(api, 'get_team_picks')
	assert hasattr(api, 'get_fixtures')
	assert hasattr(api, 'get_bootstrap_static')
	assert hasattr(api, 'get_transfers')
	assert hasattr(api, 'get_event_live')
