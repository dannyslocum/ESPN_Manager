from .constant import POSITION_MAP, PRO_TEAM_MAP
from .player import Player
from datetime import datetime, timedelta
from .utils import json_parsing
import numpy as np


class BoxPlayer(Player):
    '''player with extra data from a matchup'''
    def __init__(self, data, pro_schedule, positional_rankings, week, year):
        super(BoxPlayer, self).__init__(data, week)
        self.slot_position = 'FA'
        self.pro_opponent = "None" # professional team playing against
        self.pro_pos_rank = 0 # rank of professional team against player position
        self.game_played = 100 # 0-100 for percent of game played
        self.average_draft_position = json_parsing(data, 'averageDraftPosition')
        self.average_draft_position_percent_change = json_parsing(data, 'averageDraftPositionPercentChange')
        self.ownership_percent_change = json_parsing(data, 'percentChange')
        self.ownership_percent_owned = json_parsing(data, 'percentOwned')
        self.ownership_percent_started = json_parsing(data, 'percentStarted')
        self.transactions = self.get_player_transactions(data)
        self.seasonOutlook = json_parsing(data, 'seasonOutlook')


        if 'lineupSlotId' in data:
            self.slot_position = POSITION_MAP[data['lineupSlotId']]

        player = data['playerPoolEntry']['player'] if 'playerPoolEntry' in data else data['player']
        self.get_position_stats(player, week, year)
        if player['proTeamId'] in pro_schedule:
            (opp_id, date) = pro_schedule[player['proTeamId']]
            self.game_played = 100 if datetime.now() > datetime.fromtimestamp(date/1000.0) + timedelta(hours=3) else 0
            if str(player['defaultPositionId']) in positional_rankings:
                self.pro_opponent = PRO_TEAM_MAP[opp_id]
                # self.pro_pos_rank = positional_rankings[str(player['defaultPositionId'])][str(opp_id)]

    def __repr__(self):
        return 'Player(%s, points:%d, projected:%d)' % (self.name, self.points, self.projected_points)

    def get_player_transactions(self, data):
        transactions = json_parsing(data, "transactions")
        return [{"type": t.type, "week": t.scoringPeriodId, "status": t.status, "date": t.proposedDate} for t in transactions]

    def get_position_stats(self, player, week, year):
        position = self.position
        stats = player['stats']
        current_week_stats = None
        current_week_projections = None
        for stat in stats:
            if (stat['scoringPeriodId'] == week) and (stat['statSourceId'] == 0) and (stat['seasonId'] == year):
                current_week_stats = stat['stats']
            elif (stat['scoringPeriodId'] == week) and (stat['statSourceId'] == 1) and (stat['seasonId'] == year):
                current_week_projections = stat['stats']
            else:
                continue

        if position == "QB":
            return
        elif position == "RB":
            return
        elif position == "WR":
            current_week_stats_new = self.get_wr_stats(current_week_stats)
            current_week_projections_new = self.get_wr_stats(current_week_projections)
        elif position == "TE":
            return
        elif position == "DST":
            return
        elif position == "K":
            return
        else:
            return

        self.stats = current_week_stats_new
        self.stats_projections = current_week_projections_new
        return

    def get_qb_stats(self):
        return None

    def get_rb_stats(self):
        return None

    def get_wr_stats(self, stats):
        try:
            rec_yards = stats['42']
        except:
            rec_yards = 0

        try:
            rec_tds = stats['43']
        except:
            rec_tds = 0

        try:
            rec_2pt_conversion = stats['44']
        except:
            rec_2pt_conversion = 0

        try:
            receptions = stats['53']
        except:
            receptions = 0

        try:
            targets = stats['58']
        except:
            targets = 0

        try:
            rec_avg_yards = stats['60']
        except:
            rec_avg_yards = 0

        try:
            fumbles = stats['72']
        except:
            fumbles = 0

        try:
            stats_return = {
                "receptions": receptions,
                "rec_yards": rec_yards,
                "rec_tds": rec_tds,
                "rec_2pt_conversion": rec_2pt_conversion,
                "targets": targets,
                "rec_avg_yards": rec_avg_yards,
                "fumbles": fumbles,
            }
        except:
            stats_return = None

        return stats_return

    def get_te_stats(self):
        return None

    def get_dst_stats(self):
        return None

    def get_k_stats(self):
        return None