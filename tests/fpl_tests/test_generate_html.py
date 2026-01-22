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
        mock_api_class.assert_called_once_with(dev_mode=True)

        # Assert context was built (may be called multiple times due to default league)
        assert mock_context_class.build.call_count >= 1
        # Find the call for our specific league
        calls = [call for call in mock_context_class.build.call_args_list
                 if call[0][0] == '1638989']
        assert len(calls) == 1

        # Assert renderer was created with ranking_progression output
        calls = [call for call in mock_renderer_class.call_args_list
                 if call[0][1] == 'ranking_progression']
        assert len(calls) >= 1

        # Assert write_html_output was called
        assert mock_renderer.write_html_output.call_count >= 1


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

        # Assert renderer was created for all three output types
        # Note: may be called more than 3 times if default league is also processed
        calls = [call[0][1] for call in mock_renderer_class.call_args_list]
        assert 'standings' in calls
        assert 'gw_history' in calls
        assert 'ranking_progression' in calls
