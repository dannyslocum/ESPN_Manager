import requests
import pandas as pd
import numpy as np
import json
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
from .ff_espn_api import League
from .ff_espn_api.league import checkRequestStatus

"""
Get game info and 'vegas' odds
https://site.api.espn.com/apis/fantasy/v2/games/ffl/games?useMap=true&dates=20191010-20191015&pbpOnly=true
URL for all boxscore from default league
https://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leaguedefaults/3?view=mPositionalRatings&view=mSettings&view=mTeam&view=modular&view=mNav
Positional ratings
https://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leagues/577577?scoringPeriodId=7&view=kona_player_info
Get weather stats for each stadium
https://www.ncdc.noaa.gov/cdo-web/webservices/v2
https://www.weather.gov/documentation/services-web-api
Get depth chart
https://www.rotowire.com/football/depth-charts-pos.php
"""


class Manager(League):
    def __init__(self, league_id: int, username=None, password=None, year=9999):
        super().__init__(league_id, username, password, year)
        # self.previous_seasons = self.manager_get_previous_seasons()

    def manager_get_previous_seasons(self):
        url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leagues/577577?view=modular&view=mNav&view=mMatchupScore&view=mScoreboard&view=mStatus&view=mSettings&view=mTeam&view=mPendingTransaction"
        r = requests.get(url, cookies=self.cookies)
        checkRequestStatus(r.status_code)
        data = r.json() if self.year >= self.current_year else r.json()[0]
        return data['status']['previousSeasons']

    def manager_get_rostered_player_data(self):
        player_data = []
        if self.year == self.current_year:
            week_range = self.current_week
        else:
            week_range = 17
        print("Loading {} weeks of data".format(week_range-1))
        print("Loading Week ", end="")
        for week in range(1, week_range):
            print(week, end=" ")
            self.load_roster_week(week)
            for team in self.teams:
                for player in team.roster:
                    weekly_data = self.manager_load_player_data(player, team, week)
                    player_data.append(weekly_data)
        print('\n')
        return pd.DataFrame(player_data)

    def manager_get_team_data(self):
        team_data = []
        if self.year == self.current_year:
            week_range = self.current_week
        else:
            week_range = 17
        print("Loading {} weeks of data".format(week_range-1))
        print("Loading Week ", end="")
        for week in range(1, week_range):
            print(week, end=" ")
            self.load_team_week(week)
            for team in self.teams:
                weekly_data = self.manager_load_team_data(team, week)
                team_data.append(weekly_data)
        print('\n')
        return pd.DataFrame(team_data)

    def manager_load_team_data(self, team, week):
        return {
            "year": self.year,
            "week": week,
            "owner": team.owner,
            "acquisitions_count": team.acquisitions_count,
            "total_acquisitions": team.total_acquisitions,
            "trades": team.trades,
            "projected_final_standings": team.projected_final_standings,
            "points_for": team.points_for,
            "points_against": team.points_against,
            "mov": team.mov,
            "scores_for": team.scores,
            "scores_against": np.subtract(team.scores, team.mov),
            "wins": team.wins,
            "moveToActive": team.moveToActive,
            "standings": team.standing,
        }

    def manager_load_player_data(self, player, team, week):
        try:
            return {
                "year": self.year,
                "week": week,
                "ff_team": team.owner,
                "name": player.name,
                "projected_points": player.projected_points,
                "actual_points": player.points,
                "point_diff": player.points - player.projected_points,
                "pro_team": player.proTeam,
                "position": player.position,
                "current_slot": player.currentSlot,
                "position_rank": player.posRank,
                "weekly_outlook": player.weeklyOutlook,
                "receptions": player.stats["receptions"],
                "rec_yards": player.stats["rec_yards"],
                "rec_tds": player.stats["rec_tds"],
                "rec_2pt_conversion": player.stats["rec_2pt_conversion"],
                "targets": player.stats["targets"],
                "rec_avg_yards": player.stats["rec_avg_yards"],
                "fumbles": player.stats["fumbles"],
                "receptions": player.stats_projections["receptions"],
                "rec_yards": player.stats_projections["rec_yards"],
                "rec_tds": player.stats_projections["rec_tds"],
                "rec_2pt_conversion": player.stats_projections["rec_2pt_conversion"],
                "targets": player.stats_projections["targets"],
                "rec_avg_yards": player.stats_projections["rec_avg_yards"],
                "fumbles": player.stats_projections["fumbles"],
                # "injury_status": player.injury_status,
                # previous week injury status
                # previous week score
                # previous three week average
                # previous three week stdev
                # opponent rank
                # game odds
                # weather
            }
        except:
            return {
                "player": player,
                "year": self.year,
                "week": week,
                "ff_team": team.owner,
                "name": player.name,
                "projected_points": player.projected_points,
                "actual_points": player.points,
                "point_diff": player.points - player.projected_points,
                "pro_team": player.proTeam,
                "position": player.position,
                "current_slot": player.currentSlot,
                "position_rank": player.posRank,
                "weekly_outlook": player.weeklyOutlook,
                # "injury_status": player.injury_status,
                # previous week injury status
                # previous week score
                # previous three week average
                # previous three week stdev
                # opponent rank
                # game odds
                # weather
            }

    def visualize(self):
        pass

