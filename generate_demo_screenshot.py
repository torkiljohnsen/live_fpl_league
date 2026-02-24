"""
Generate a demo HTML page with 5 teams showing varied score progressions.

This script creates a realistic example with:
- 5 teams with different progression patterns
- Non-parallel lines showing varied performance
- Realistic rank movements and score variations
- All statistics (Klatreren, I fritt fall, Haien kommer, Høyeste lagverdi)

The example demonstrates:
- Emma: Consistent leader with steady improvement
- Oliver: Close second, chasing the leader
- Sophia: Mid-pack with ups and downs (visible dip at GW4)
- Noah: Started poorly but climbing steadily
- Liam: Struggling and falling behind
"""
import sys

sys.path.insert(0, 'tests/fpl_tests')
from test_utils import make_test_participant

from fpl.league_context import LeagueContext
from fpl.league_template_renderer import LeagueTemplateRenderer

# Create 5 participants with varied and realistic progression patterns
participants = [
    # Emma: Strong start, consistent performer, leads by end
    make_test_participant(
        first_name='Emma',
        history=[
            {'event': 1, 'overall_rank': 450000, 'total_points': 65, 'value': 1000, 'bank': 5},
            {'event': 2, 'overall_rank': 380000, 'total_points': 135, 'value': 1005, 'bank': 10},
            {'event': 3, 'overall_rank': 310000, 'total_points': 210, 'value': 1010, 'bank': 15},
            {'event': 4, 'overall_rank': 280000, 'total_points': 290, 'value': 1015, 'bank': 8},
            {'event': 5, 'overall_rank': 250000, 'total_points': 365, 'value': 1020, 'bank': 12},
            {'event': 6, 'overall_rank': 235000, 'total_points': 448, 'value': 1025, 'bank': 15},
            {'event': 7, 'overall_rank': 220000, 'total_points': 528, 'value': 1030, 'bank': 18},
        ],
        entry_id=1,
        league_rank=1
    ),
    # Oliver: Close second, very consistent chaser
    make_test_participant(
        first_name='Oliver',
        history=[
            {'event': 1, 'overall_rank': 480000, 'total_points': 62, 'value': 995, 'bank': 8},
            {'event': 2, 'overall_rank': 400000, 'total_points': 130, 'value': 1000, 'bank': 12},
            {'event': 3, 'overall_rank': 330000, 'total_points': 202, 'value': 1005, 'bank': 18},
            {'event': 4, 'overall_rank': 295000, 'total_points': 280, 'value': 1010, 'bank': 10},
            {'event': 5, 'overall_rank': 265000, 'total_points': 358, 'value': 1015, 'bank': 14},
            {'event': 6, 'overall_rank': 248000, 'total_points': 437, 'value': 1020, 'bank': 16},
            {'event': 7, 'overall_rank': 232000, 'total_points': 517, 'value': 1025, 'bank': 20},
        ],
        entry_id=2,
        league_rank=2
    ),
    # Sophia: Mid-pack, inconsistent with ups and downs
    make_test_participant(
        first_name='Sophia',
        history=[
            {'event': 1, 'overall_rank': 520000, 'total_points': 58, 'value': 990, 'bank': 10},
            {'event': 2, 'overall_rank': 450000, 'total_points': 125, 'value': 995, 'bank': 15},
            {'event': 3, 'overall_rank': 380000, 'total_points': 198, 'value': 1000, 'bank': 20},
            {'event': 4, 'overall_rank': 420000, 'total_points': 265, 'value': 1005, 'bank': 12},  # Bad gameweek
            {'event': 5, 'overall_rank': 385000, 'total_points': 340, 'value': 1010, 'bank': 18},  # Recovery
            {'event': 6, 'overall_rank': 360000, 'total_points': 418, 'value': 1015, 'bank': 22},
            {'event': 7, 'overall_rank': 340000, 'total_points': 495, 'value': 1020, 'bank': 25},
        ],
        entry_id=3,
        league_rank=3
    ),
    # Noah: Started poorly but improving steadily
    make_test_participant(
        first_name='Noah',
        history=[
            {'event': 1, 'overall_rank': 650000, 'total_points': 45, 'value': 985, 'bank': 15},
            {'event': 2, 'overall_rank': 580000, 'total_points': 110, 'value': 990, 'bank': 20},
            {'event': 3, 'overall_rank': 500000, 'total_points': 182, 'value': 995, 'bank': 25},
            {'event': 4, 'overall_rank': 440000, 'total_points': 258, 'value': 1000, 'bank': 18},
            {'event': 5, 'overall_rank': 395000, 'total_points': 335, 'value': 1005, 'bank': 22},
            {'event': 6, 'overall_rank': 365000, 'total_points': 414, 'value': 1010, 'bank': 28},
            {'event': 7, 'overall_rank': 345000, 'total_points': 492, 'value': 1015, 'bank': 30},
        ],
        entry_id=4,
        league_rank=4
    ),
    # Liam: Struggling, falling behind
    make_test_participant(
        first_name='Liam',
        history=[
            {'event': 1, 'overall_rank': 550000, 'total_points': 55, 'value': 1000, 'bank': 5},
            {'event': 2, 'overall_rank': 520000, 'total_points': 118, 'value': 1005, 'bank': 8},
            {'event': 3, 'overall_rank': 510000, 'total_points': 185, 'value': 1010, 'bank': 10},
            {'event': 4, 'overall_rank': 530000, 'total_points': 250, 'value': 1015, 'bank': 5},  # Dropped
            {'event': 5, 'overall_rank': 545000, 'total_points': 318, 'value': 1020, 'bank': 8},  # Still dropping
            {'event': 6, 'overall_rank': 560000, 'total_points': 388, 'value': 1025, 'bank': 10},
            {'event': 7, 'overall_rank': 575000, 'total_points': 455, 'value': 1030, 'bank': 12},
        ],
        entry_id=5,
        league_rank=5
    ),
]

# Create league data structure
league_data = {
    'id': 'demo_league',
    'name': 'Demo League',
    'participants': participants,
    'current_event_id': 7,
    'finished_event_ids': [1, 2, 3, 4, 5, 6],
    'event_ids': [1, 2, 3, 4, 5, 6, 7],
}

# Read logo SVG
with open('assets/fpl_logo.svg') as f:
    logo_svg = f.read()

# Create context
context = LeagueContext(
    league_data=league_data,
    league_join_code='DEMO123',
    logo_svg=logo_svg,
    dev_mode=True
)

# Generate ranking progression HTML
renderer = LeagueTemplateRenderer(context, 'ranking_progression')
renderer.write_html_output()
print('Demo HTML generated successfully: docs/ranking_progression_demo_league-dev.html')
print('\nTeam Progressions:')
print('- Emma: Strong consistent leader (528 points)')
print('- Oliver: Close second, chasing hard (517 points, 11 behind)')
print('- Sophia: Mid-pack with ups and downs (495 points)')
print('- Noah: Started poorly but climbing (492 points, 3 behind Sophia)')
print('- Liam: Struggling and falling behind (455 points)')
