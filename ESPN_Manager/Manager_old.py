import requests
import pandas as pd
import numpy as np
#from fuzzywuzzy import process, fuzz
import json
from datetime import datetime
from .Transaction import Transaction
from .FantasyPros import RequestFantasyProsData
from .ff_espn_api import League

"""
Get game info and 'vegas' odds
https://site.api.espn.com/apis/fantasy/v2/games/ffl/games?useMap=true&dates=20191010-20191015&pbpOnly=true
"""
class Manager(League):
    def __init__(self, league_id: int, team_id: int=None, username=None, password=None):
        super().__init__(league_id, 2019, username, password)
        self.league_id = str(league_id)
        self.current_year = int(datetime.now().year)
        current_month = int(datetime.now().month)
        if current_month <= 2:
            self.current_year = self.current_year - 1
        if team_id:
            self.get_team(team_id)

    def adjust_roster(self, team_id):
        pass

    def analyze_roster(self, team_id):
        pass

    def get_visualizations(self):
        pass

    def get_team_id(self, team_id):
        for t in self.teams:
            if t.team_id == team_id:
                self.team = t
                return

    def get_lineup_slot_counts(self):
        url = self.ENDPOINT
        payload = {"view": "mSettings"}
        response = requests.get(url, payload=payload, cookies=self.cookies)
        if response.ok is False:
            print("### ERROR: response error with get_roster function ###")
            print(json.dumps(response.json, indent=6))
        data = response.json() if self.year > 2018 else response.json()[0]
        lineup_slot_counts = data['settings']['rosterSettings']['lineupSlotCounts']
        return lineup_slot_counts

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

    def get_adjusted_roster_fantasypros(self, year, week, top20):
        fantasypros_data = RequestFantasyProsData().request_player_projections_week(week, top20)
        roster = self.get_roster(year, week)
        projection = self.correlate_player_names(roster.fullname, fantasypros_data.Player, fantasypros_data.FPTS)
        roster['FantasyPros_projected'] = projection
        roster = roster.sort_values(['FantasyPros_projected'], ascending=False)
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

    def correlate_player_names(self, espn_roster_names, match_roster_names, match_projections):
        name_validated = np.array([])
        espn_roster_names = espn_roster_names.str.lower()
        match_roster_names = match_roster_names.str.lower()
        for name in espn_roster_names:
            estimate = process.extractOne(name, match_roster_names, scorer=fuzz.ratio)
            est1 = estimate[0]
            est_per = estimate[1]
            if est_per >= 85:
                # print('Name = {}, Estimated = {}, Percent = {}'.format(name, est1, est_per))
                projection = float(match_projections[match_roster_names == est1])
                name_validated = np.append(name_validated, projection)
            else:
                name_validated = np.append(name_validated, None)
        return name_validated

    def make_roster_adjustments(self, site="ESPN"):
        if site == "ESPN":
            adjusted_roster = self.get_adjusted_roster(week=self.current_week)
        elif site == "FantasyPros":
            adjusted_roster = self.get_adjusted_roster_fantasypros()
        return Transaction(self).make_lineup_adjustment(adjusted_roster)

    def get_roster(self, year=0, week=0):
        return self.get_roster(year=year, week=week)

    def get_adjusted_roster(self, year=0, week=0):
        return self.get_adjusted_roster(year=year, week=week)

    def get_adjusted_roster_fantasypros(self, week=0, top20=False):
        year = self.current_year
        if week == 0:
            week = self.current_week
        return self.get_adjusted_roster_fantasypros(year=year, week=week, top20=top20)
