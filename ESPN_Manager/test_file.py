from ff_espn_api import League
import requests
import pandas as pd

class Manager(League):
    def __init__(self, league_id, year, username, password):
        super().__init__(league_id, username=username, password=password, year=year)
        self.team = self.get_user_team()

    def get_lineup_slot_counts(self):
        url = self.ENDPOINT
        payload = {"view": "mSettings"}
        response = requests.get(url, params=payload, cookies=self.cookies)
        if response.ok is False:
            print("### ERROR: response error with get_roster function ###")
            print(json.dumps(response.json, indent=6))
        data = response.json() if self.year > 2018 else response.json()[0]
        lineup_slot_counts = data['settings']['rosterSettings']['lineupSlotCounts']
        return lineup_slot_counts

    def get_roster_data(self):
        roster_data = [{
            "id": player.playerId,
            "projection": player.projected_points,
            "position": player.position,
            "eligible_slots": player.eligibleSlots,
            "lineup_locked": player.lineup_locked
        } for player in self.team.roster]
        return pd.DataFrame(roster_data)

def get_adjusted_roster(self, year=0, week=0):
    roster = self.get_roster(year, week)
    roster = roster.sort_values(['projected'], ascending=False)
    roster = roster.sort_values(['team_id', 'week']).reset_index()
    roster_group = roster.groupby(['team_id', 'week'])

    lineup_slot_counts = self.get_lineup_slot_counts(year)
    adjusted_slot = []
    for _, group in roster_group:
        lineup_slot_counts_copy = lineup_slot_counts.copy()
        for slots in group['slot_openings']:
            slot_found = 20
            try:
                slots.remove(3)
                slots.append(3)
            except:
                pass
            for slot in slots:
                if slot >= 20:
                    continue
                slot_counts = lineup_slot_counts_copy[str(slot)]
                if slot_counts > 0:
                    lineup_slot_counts_copy[str(slot)] += -1
                    slot_found = slot
                    break
            adjusted_slot.append(slot_found)
    roster['adjusted_slot'] = adjusted_slot
    roster['is_starting_adjusted'] = roster.adjusted_slot < 20
    return roster

def make_lineup_adjustment(self, adjusted_roster):
    team_adjusted_roster = adjusted_roster[adjusted_roster.team_id == self.team_id]
    team_adjustments = team_adjusted_roster[
        team_adjusted_roster.is_starting != team_adjusted_roster.is_starting_adjusted]
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
        print("-" * 100)
        if len(current_starters) > 0:
            benched_points = sum(current_starters.projected)
            for player in current_starters[['fullname', 'current_slot_id', 'projected']].values:
                print("--> Benched {} from the {} position (projected: {})".format(player[0],
                                                                                   self.slot_codes[player[1]],
                                                                                   player[2]))
        else:
            current_starter_points = 0
        current_bench = team_adjustments[team_adjustments.is_starting is False]
        for player in current_bench[['fullname', 'adjusted_slot', 'projected']].values:
            print("<-- Starting {} in the {} position (projected: {})".format(player[0], self.slot_codes[player[1]],
                                                                              player[2]))
        starting_points = sum(current_bench.projected)
        print("-" * 50)
        print("-" * 50)
        print("Projected for {} more points".format(float(starting_points - benched_points)))
    else:
        print("<--> No adjustments needed")
    return None
