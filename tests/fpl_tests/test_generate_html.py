"""Tests for generate_html CLI script."""
from unittest.mock import MagicMock, patch


def test_ranking_progression_output_option():
    """Test that -o ranking_progression generates the ranking progression HTML."""
    # Import the module (we need to import after mocking if necessary)
    from generate_html import main

    # Mock the shared API and rendering pipeline
    with patch('generate_html.FPL_API') as mock_api_class, \
         patch('generate_html.LeagueContext') as mock_context_class, \
         patch('generate_html.LeagueTemplateRenderer') as mock_renderer_class, \
         patch('sys.argv', ['generate_html.py', '-l', '1638989', '--dev', '-o', 'ranking_progression']):

        # Setup mocks
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_context = MagicMock()
        mock_context_class.build.return_value = mock_context

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Run main
        main()

        # Assert API was created with dev_mode=True
        mock_api_class.assert_called_once_with(dev_mode=True, cache_dir=None)

        # Assert context was built exactly once for the specified league
        mock_context_class.build.assert_called_once_with(
            '1638989', True, None, fpl_api=mock_api
        )

        # Assert renderer was created exactly once with ranking_progression output
        mock_renderer_class.assert_called_once_with(mock_context, 'ranking_progression')

        # Assert write_html_output was called exactly once
        mock_renderer.write_html_output.assert_called_once()


def test_ranking_progression_in_all_output():
    """Test that -o ALL includes ranking_progression."""
    from generate_html import main

    with patch('generate_html.FPL_API') as mock_api_class, \
         patch('generate_html.LeagueContext') as mock_context_class, \
         patch('generate_html.LeagueTemplateRenderer') as mock_renderer_class, \
         patch('sys.argv', ['generate_html.py', '-l', '1638989', '--dev', '-o', 'ALL']):

        # Setup mocks
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_context = MagicMock()
        mock_context_class.build.return_value = mock_context

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Run main
        main()

        # Assert context was built exactly once for the specified league
        mock_context_class.build.assert_called_once_with(
            '1638989', True, None, fpl_api=mock_api
        )

        # Assert renderer was created exactly 3 times (once for each output type)
        assert mock_renderer_class.call_count == 3
        calls = [call[0][1] for call in mock_renderer_class.call_args_list]
        assert 'standings' in calls
        assert 'gw_history' in calls
        assert 'ranking_progression' in calls

        # Assert write_html_output was called 3 times
        assert mock_renderer.write_html_output.call_count == 3


def test_default_league_when_no_league_specified():
    """Test that default league is used when no -l flag is provided."""
    from generate_html import FPL_LEAGUE_ID, main

    with patch('generate_html.FPL_API') as mock_api_class, \
         patch('generate_html.LeagueContext') as mock_context_class, \
         patch('generate_html.LeagueTemplateRenderer') as mock_renderer_class, \
         patch('sys.argv', ['generate_html.py', '--dev']):

        # Setup mocks
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_context = MagicMock()
        mock_context_class.build.return_value = mock_context

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Run main
        main()

        # Assert context was built with the default league ID
        mock_context_class.build.assert_called_with(
            FPL_LEAGUE_ID, True, None, fpl_api=mock_api
        )


def test_specified_league_overrides_default():
    """Test that specifying -l does NOT include the default league (bug fix)."""
    from generate_html import main

    with patch('generate_html.FPL_API') as mock_api_class, \
         patch('generate_html.LeagueContext') as mock_context_class, \
         patch('generate_html.LeagueTemplateRenderer') as mock_renderer_class, \
         patch('sys.argv', ['generate_html.py', '-l', '1638989', '--dev', '-o', 'standings']):

        # Setup mocks
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_context = MagicMock()
        mock_context_class.build.return_value = mock_context

        mock_renderer = MagicMock()
        mock_renderer_class.return_value = mock_renderer

        # Run main
        main()

        # Assert context was built exactly once (not twice with default league)
        mock_context_class.build.assert_called_once_with(
            '1638989', True, None, fpl_api=mock_api
        )

        # Assert renderer was called exactly once
        mock_renderer_class.assert_called_once()
        mock_renderer.write_html_output.assert_called_once()
