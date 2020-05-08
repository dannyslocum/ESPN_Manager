from .constant import POSITION_MAP, PRO_TEAM_MAP, DEFAULT_POSITION_MAP
from .utils import json_parsing

class Player(object):
    '''Player are part of team'''
    def __init__(self, data, week):
        self.data = data
        player = data['playerPoolEntry']['player'] if 'playerPoolEntry' in data else data['player']
        self.name = json_parsing(data, 'fullName')
        self.playerId = json_parsing(data, 'id')
        self.posRank = json_parsing(data, 'positionalRanking')
        self.get_weekly_pos_rank(player, week)
        try:
            self.currentSlot = POSITION_MAP[json_parsing(data, "lineupSlotId")]
        except:
            None
        self.eligibleSlots = [POSITION_MAP[pos] for pos in json_parsing(data, 'eligibleSlots')]
        try:
            self.position = DEFAULT_POSITION_MAP[json_parsing(data, 'defaultPositionId')]
        except:
            self.position = "Other"
        try:
            self.acquisitionType = json_parsing(data, 'acquisitionType')
        except:
            None
        self.weeklyOutlook = self.get_player_outlook(data, week)
        self.proTeam = PRO_TEAM_MAP[json_parsing(data, 'proTeamId')]
        self.points = 0
        self.projected_points = 0
        self.get_scores(player, week)
        # self.injury_status = self.get_injury_status(player) # Only works for current week's injury status
        self.lineup_locked = json_parsing(data, "lineupLocked")


    def __repr__(self):
        return 'Player(%s)' % (self.name, )

    def get_scores(self, player, week):
        player_stats = player['stats']
        for stats in player_stats:
            if stats['statSourceId'] == 0 and stats['scoringPeriodId'] == week:
                self.points = round(stats['appliedTotal'], 2)
            elif stats['statSourceId'] == 1 and stats['scoringPeriodId'] == week:
                self.projected_points = round(stats['appliedTotal'], 2)

    def get_weekly_pos_rank(self, player, week):
        try:
            rankings = player['rankings'][str(week)]
            for rank in rankings:
                try:
                    averageRank = rank['averageRank']
                    if rank['rankType'] == "STANDARD":
                        self.standardWeekRank = averageRank
                    else:
                        self.pprWeekRank = averageRank
                except:
                    return None
        except:
            return None

    def get_injury_status(self, player):
        # get injury status (set DST to 'Active' because it doesnt have this attribute)
        try:
            return player['injuryStatus']
        except:
            return 'ACTIVE'

    def get_player_outlook(self, data, week):
        try:
            return data['playerPoolEntry']['player']['outlooks']['outlooksByWeek'][str(week)]
        except:
            return json_parsing(data, "seasonOutlook")