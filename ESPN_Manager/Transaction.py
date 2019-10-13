import pandas as pd


class Transaction:
    def __init__(self, ESPNFFL):
        self.session = ESPNFFL.session
        self.current_week = ESPNFFL.current_week
        self.team_info = ESPNFFL.Roster.team_info
        self.team_id = ESPNFFL.team_id
        self.url = ESPNFFL.current_url() + "/transactions/"
        self.slot_codes = {
            0: 'QB', 2: 'RB', 3: 'Flex', 4: 'WR', 6: 'TE',
            16: 'Def', 17: 'K', 20: 'Bench', 21: 'IR', 23: 'Flex',
        }

    def make_lineup_adjustment(self, adjusted_roster):
        team_adjusted_roster = adjusted_roster[adjusted_roster.team_id == self.team_id]
        team_adjustments = team_adjusted_roster[team_adjusted_roster.is_starting != team_adjusted_roster.is_starting_adjusted]
        adjustments_needed = len(team_adjustments)
        if adjustments_needed > 0:
            team_info = self.team_info[self.team_info.team_id == self.team_id].reset_index()
            leagueManager = team_info.isLeagueManager[0]
            if leagueManager:
                leagueManager = True
            else:
                leagueManager = False
            adjustment = {
                "isLeagueManager": leagueManager,
                "teamId": "{}".format(self.team_id),
                "type": "ROSTER",
                "memberId": "{}".format(team_info.swid[0]),
                "scoringPeriodId": "{}".format(self.current_week),
                "executionType": "EXECUTE",
                "items": []
            }

            current_starters = team_adjustments[team_adjustments.is_starting]
            if len(current_starters) > 0:
                move_starter_players = [
                    {
                        "playerId": "{}".format(player[0]),
                        "type": "LINEUP",
                        "fromLineupSlotId": "{}".format(player[1]),
                        "toLineupSlotId": "{}".format(20)
                    } for player in current_starters[['id', 'current_slot_id']].values
                ]
                adjustment["items"] = move_starter_players
                params = adjustment
                response = self.session.post(self.url, json=params)
                if response.ok is False:
                    print("### Error adjusting lineup ###")
                    return response

            move_bench_players = [
                {
                    "playerId": "{}".format(player[0]),
                    "type": "LINEUP",
                    "fromLineupSlotId": "{}".format(20),
                    "toLineupSlotId": "{}".format(player[1])
                } for player in team_adjustments[['id', 'adjusted_slot']].values
            ]
            adjustment["items"] = move_bench_players
            params = adjustment
            response = self.session.post(self.url, json=params)
            if response.ok is False:
                print("### Error adjusting lineup and moving players to starters ###")
                return response

            print("<--> {} lineup adjustments made".format(adjustments_needed))
            print("-"*100)
            if len(current_starters) > 0:
                benched_points = sum(current_starters.projected)
                for player in current_starters[['fullname', 'current_slot_id', 'projected']].values:
                    print("--> Benched {} from the {} position (projected: {})".format(player[0],
                                                                                       self.slot_codes[player[1]],
                                                                                       player[2]))
            else:
                current_starter_points = 0
            current_bench = team_adjustments[team_adjustments.is_starting == False]
            for player in current_bench[['fullname', 'adjusted_slot', 'projected']].values:
                print("<-- Starting {} in the {} position (projected: {})".format(player[0], self.slot_codes[player[1]],
                                                                                  player[2]))
            starting_points = sum(current_bench.projected)
            print("-"*50)
            print("-"*50)
            print("Projected for {} more points".format(float(starting_points - benched_points)))
        else:
            print("<--> No adjustments needed")
        return None

    def get_transaction_history(self, team_id=0, year=0, week=0, player_id=0):
        return pd.DataFrame([])

    def add_free_agent(self):
        adjustment = {
            "isLeagueManager": False,
            "teamId": 4,
            "type": "FREEAGENT",
            "memberId": "{CF0251D0-5ADB-4F18-AF30-FE7E257B8C7F}",
            "scoringPeriodId": 1,
            "executionType": "EXECUTE",
            "items": [
                {
                    "playerId": 4040761,
                    "type": "ADD",
                    "toTeamId": 4
                }, {
                    "playerId": 2574808,
                    "type": "DROP",
                    "fromTeamId": 4
                }
            ]
        }
        return

    def submit_waiver_claim(self):
        adjustment = {
            "isLeagueManager": False,
            "teamId": 2,
            "type": "WAIVER",
            "memberId": "{CF0251D0-5ADB-4F18-AF30-FE7E257B8C7F}",
            "scoringPeriodId": 1,
            "executionType": "EXECUTE",
            "items": [
                {
                    "playerId": 2971573,
                    "type": "ADD",
                    "toTeamId": 2
                }, {
                    "playerId": 9704,
                    "type": "DROP",
                    "fromTeamId": 2
                }
            ],
            "bidAmount": None
        }

    def cancel_waiver_claim(self):
        # mPendingTransactions to get the relatedTransactionId
        adjustment = {
            "isLeagueManager": False,
            "teamId": 2,
            "type": "WAIVER",
            "memberId": "{CF0251D0-5ADB-4F18-AF30-FE7E257B8C7F}",
            "scoringPeriodId": 1,
            "executionType": "CANCEL",
            "relatedTransactionId": "42de0279-2f00-462f-b062-eba05ac06423"
        }
