import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import re
import math
from matplotlib import pyplot as plt
from fuzzywuzzy import process, fuzz
import warnings
import time
import random
import json

warnings.filterwarnings("ignore")
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class RequestData:
    """
        Info
    """
    def __init__(self):
        self.session_fantasyPros = requests.Session()
        self.header = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/76.0.3809.100 Safari/537.36',
            'From': 'djslocum13@gmail.com'
        }

    def login_fantasy_pros(self):
        print('-Logging into FantasyPros')
        fantasy_pros_login = 'https://secure.fantasypros.com/accounts/login/'
        successful = False
        count = 0
        while successful is False:
            fantasypros_username = input("Input FantasyPros Username: ")
            fantasypros_password = input("Input FantasyPros Password: ")
            response = self.session_fantasyPros.get(fantasy_pros_login, headers=self.header)
            soup = bs(response.text, 'html.parser')
            hidden_input = soup.find("input", {"name": "csrfmiddlewaretoken"}).get("value")
            payload = {
                'csrfmiddlewaretoken': hidden_input,
                'username': fantasypros_username,
                'password': fantasypros_password
            }
            post = self.session_fantasyPros.post(fantasy_pros_login, data=payload, headers=self.header)
            if post.ok:
                print('-Successfully logged into FantasyPros')
                successful = True
            else:
                count += 1
                if count < 3:
                    print("### Error code {} ###".format(post.status_code))
                    print('### Error logging into FantasyPros ###')
                    print('### Wait 5 seconds and try again ###')
                    time.sleep(5)
                else:
                    print("### Check your username and password manually and try again ###")
                    return "Error"
        return None

    def request_draft_rankings_values(self):
        login_check = self.login_fantasy_pros()
        if login_check == "Error":
            print("### Error returning draft rankings ###")
            return None
        fantasy_pros_rankings_url = 'https://www.fantasypros.com/nfl/rankings/ppr-cheatsheets.php?filters=35fd0c3d9a'
        response = self.session_fantasyPros.get(fantasy_pros_rankings_url, headers=self.header)
        if response.ok:
            soup = bs(response.text, 'html.parser')
            table = soup.find('table', {'id': 'rank-data'})
            header = [th.text for th in table.thead.find_all('th')]
            header.append('Tier')
            header.append('Team')
            values = pd.DataFrame([], columns=header)
            for index, tr in enumerate(table.tbody.find_all("tr")):
                if 'tier-row' in tr.get('class'):
                    tier = tr.get('data-tier')
                elif 'static' in tr.get('class'):
                    continue
                elif 'player-row' in tr.get('class'):
                    vals = []
                    for i, td in enumerate(tr.find_all('td')):
                        if i == 2:
                            team = td.small.text
                            vals.append(td.span.text)
                        else:
                            vals.append(td.text)
                    vals.append(None)
                    vals.append(tier)
                    vals.append(team)
                    values.loc[index] = vals
            values = values.drop(['WSID', 'Notes\r\n                            '], axis=1)
            values.Pos = values.Pos.apply(lambda x: re.sub('\d', '', x))
            values['vs. ADP'] = values['vs. ADP'].apply(lambda x: re.sub('[+]', '', x))
            values.Team[values.Team == ''] = values[values.Team == '']['Overall (Team)'].apply(
                lambda x: re.findall(r'(?:[A-Za-z]+\s*[(])([A-Za-z]+)', x)[0])
            values.ADP = values.ADP.str.replace(',', '')
            values.Bye[values.Bye == ''] = 999
            values = values.astype({
                'Rank': 'int',
                'Overall (Team)': 'str',
                'Pos': 'category',
                'Bye': 'int',
                'Best': 'int',
                'Worst': 'int',
                'Avg': 'float',
                'Std Dev': 'float',
                'ADP': 'float',
                'vs. ADP': 'float',
                'Tier': 'int',
                'Team': 'category'
            })
            # values.sample(20)
            # values.dtypes
        else:
            print("### Error returning draft rankings ###")
            return None
        values.to_csv('draft_rankings.csv', index=False)
        print('-Data Saved to "draft_rankings.csv"')
        return values

    def request_player_stats_year_week(self, year, week):
        return RequestPlayerStats(self.session_fantasyPros, self.header, year, week).data

    def request_player_projections_week(self, week):
        return RequestPlayerProjections(self.session_fantasyPros, self.header, week).data

    def request_draft_pick_values(self):
        print('-Scraping webpage for draft pick values')
        draft_pick_values_url = \
            'https://www.theringer.com/nfl/2018/8/20/17758898/fantasy-football-draft-pick-value-chart'
        response = requests.get(draft_pick_values_url, headers=self.header)
        if response.ok:
            soup = bs(response.text, 'html.parser')
            table = soup.find("table", {"class": "p-data-table"})
            header = [th.text for th in table.thead.tr.find_all("th")]
            values = pd.DataFrame([], columns=header)
            for index, tr in enumerate(table.tbody.find_all("tr")):
                vals = []
                for td in tr.find_all('td'):
                    vals.append(td.text)
                values.loc[index] = vals
            values['% of no. 1 pick'] = values['% of no. 1 pick'].str.replace('%', '')
            team = np.array([])
            for value in values.Pick:
                mod8 = int(value) % 8
                mod16 = int(value) % 16
                if mod16 == 0:
                    val = 1.0
                elif mod8 == 0:
                    val = 8.0
                elif mod16 > 8:
                    val = 9 - mod8
                else:
                    val = mod8
                team = np.append(team, val)
            values['Team #'] = team
            values = values.astype({'Pick': 'int', 'Value': 'float', '% of no. 1 pick': 'float', 'Team #': 'int'})
            values['Round'] = values.Pick.apply(lambda x: math.ceil(x / 8))
            # values.dtypes
        else:
            return None
        values.to_csv('draft_value.csv', index=False)
        print('-Data Saved to "draft_value.csv"')
        return values


class RequestPlayerData:
    """
        Info
    """

    def __init__(self):
        self.data = pd.DataFrame([])
        self.positions = ['qb', 'rb', 'wr', 'te', 'k', 'dst']
        print('-Scraping FantasyPros')

    def validate_response(self, response, pos):
        if response.ok:
            data = self.get_data(response, pos)
            self.data = self.data.append(data)
            if pos != "dst":
                wait = random.randint(400, 600) / 100
                print('   -Scraped data for {} position, wait {} seconds for next'.format(pos, int(wait)))
                time.sleep(wait)
            else:
                print('   -Scraped data for {} position')
        else:
            print("### Error connecting to FantasyPros for the {} position ###".format(pos))

    def get_data(self, response, pos):
        soup = bs(response.text, 'html.parser')
        table = soup.find('table', {'class': 'table'})
        data = self.get_dataframe_header(table)
        for index, tr in enumerate(table.tbody.find_all("tr")):
            vals = []
            for i, td in enumerate(tr.find_all('td')):
                if i == 0:
                    name = td.find('a', {'class': 'player-name'}).text
                    vals.append(name)
                else:
                    vals.append(td.text)
            data.loc[index] = vals
        data = data.replace({',': ''}, regex=True)
        data['Position'] = pos
        return data

    def get_dataframe_header(self, table):
        tr = table.thead.find_all('tr')
        if len(tr) == 2:
            thead_top = tr[0].find_all('td')
            thead_top_header = []
            for td in thead_top:
                col_num = td.get("colspan")
                if col_num is None:
                    col_num = 1
                thead_top_header += int(col_num) * [td.text]
            header = [thead_top_header[index] + ' ' + th.text for index, th in enumerate(tr[1].find_all('th'))]
        elif len(tr) == 1:
            header = [th.text for th in table.thead.find_all('th')]
        else:
            print('### No header found ###')
        header[0] = "Player"
        values = pd.DataFrame([], columns=header)
        return values


class RequestPlayerProjections(RequestPlayerData):
    """
        Info
    """

    def __init__(self, session_fantasyPros, header, week):
        super().__init__()
        self.session_fantasyPros = session_fantasyPros
        self.header = header
        self.week = str(week)
        self.url = 'https://www.fantasypros.com/nfl/projections/{}.php?scoring=PPR&week={}'
        for pos in self.positions:
            self.position_requests(pos)
        print("-Done scraping")
        self.data = self.data.reset_index()
        self.data.to_csv('player_projections_{}.csv'.format(self.week), index=False)
        print('-Data Saved to "player_projections_{}.csv"'.format(self.week))

    def position_requests(self, pos):
        response = self.session_fantasyPros.get(self.url.format(pos, self.week), headers=self.header)
        self.validate_response(response, pos)
        return


class RequestPlayerStats(RequestPlayerData):
    """
        Info
    """

    def __init__(self, session_fantasyPros, header, year, week):
        super().__init__()
        self.session_fantasyPros = session_fantasyPros
        self.header = header
        self.year = str(year)
        self.week = str(week)
        self.url = \
            'https://www.fantasypros.com/nfl/stats/{}.php?year={}&scoring=PPR&ownership=consensus&range={}'

        for pos in self.positions:
            self.position_requests(pos)
        print("-Done scraping")
        self.data = self.data.reset_index()
        self.data.to_csv('player_stats_{}_{}.csv'.format(self.year, self.week), index=False)
        print('-Data Saved to "player_stats_{}_{}.csv"'.format(self.year, self.week))

    def position_requests(self, pos):
        if self.week == "full":
            url = self.url.format(pos, self.year, "full")
        else:
            url = self.url.format(pos, self.year, "week") + "&week={}".format(self.week)
        response = self.session_fantasyPros.get(url, headers=self.header)
        self.validate_response(response, pos)
        return


class FantasyFootball(RequestData):
    """
        Info
    """
    def __init__(self):
        super().__init__()
        self.player_projections = self.get_player_projections('draft')
        self.player_stats_2018 = self.get_player_stats(2018, 'full')

    def get_player_projections(self, week):
        try:
            player_projections = pd.read_csv('player_projections_{}.csv'.format(str(week)))
            print('-File Found (player_projections_week.csv)'.format(str(week)))
        except:
            player_projections = self.request_player_projections_week(week)
        return player_projections

    def get_player_stats(self, year, week):
        try:
            player_stats = pd.read_csv('player_stats_{}_{}.csv'.format(str(year), str(week)))
            print('-File Found (player_stats_{}_{}.csv)'.format(str(year), str(week)))
        except:
            player_stats = self.request_player_stats_year_week(year, week)
        return player_stats

    def plot_bar(self, x, y, x_labels=[], y_label='', title=''):
        plt.figure(figsize=(5, 3))
        plt.bar(x, y, align='center')
        if len(x_labels) > 0:
            plt.xticks(x, x_labels)
            plt.xticks(rotation=90)
        if y_label != '':
            plt.ylabel(y_label)
        if title != '':
            plt.title(title)
        plt.show()


class FantasyFootballDraft(FantasyFootball):
    def __init__(self):
        super().__init__()
        self.draft_value = self.get_draft_pick_value()
        self.draft_rankings = self.get_draft_rankings()
        self.draft_keeper_2019 = self.get_draft_keeper_2019()
        self.team_draft_values = self.merge_team_draft_values()

    def get_draft_pick_value(self):
        try:
            draft_value = pd.read_csv('draft_value.csv')
            print('-File Found (draft_value.csv)')
        except:
            draft_value = self.request_draft_pick_values()
        return draft_value

    def get_draft_rankings(self):
        try:
            draft_rankings = pd.read_csv('draft_rankings.csv')
            print('-File Found (draft_rankings.csv)')
        except:
            draft_rankings = self.request_draft_rankings_values()
        return draft_rankings

    def get_draft_keeper_2019(self):
        try:
            return pd.read_csv('2019_draft_keeper.csv')
        except:
            print('### Could not find file 2019_draft_keeper.csv ###')
            return None

    def merge_team_draft_values(self):
        draft_value = self.draft_value
        draft_keeper_2019 = self.draft_keeper_2019
        team_draft_values = draft_value.merge(draft_keeper_2019[['Order', 'Team']], how='left', left_on='Team #',
                                              right_on='Order')
        team_draft_values = team_draft_values[team_draft_values.Pick <= 128]
        return team_draft_values[['Pick', 'Round', 'Order', 'Team', 'Value', '% of no. 1 pick']]

    def show_team_draft_values(self):
        team_draft_values = self.team_draft_values
        team_draft_values_sum = team_draft_values.groupby(['Team']).Value.sum().reset_index().sort_values(['Value'],
                                                                                                          ascending=False).reset_index().drop(
            ['index'], axis=1)
        print(team_draft_values_sum)
        y_val = team_draft_values_sum['Value']
        x_val = np.arange(len(y_val))
        x_names = team_draft_values_sum['Team']
        self.plot_bar(x_val, y_val, x_names, "Total Draft Value", "Draft Value")

    def create_cheat_sheet(self):
        self.player_projections['Player_lower'] = self.player_projections['Player'].str.lower()
        draft_rankings_and_projections = self.draft_rankings.merge(self.player_projections, how="left", left_on="Name",
                                                                   right_on="Player_lower")
        self.player_stats_2018['Player_lower'] = self.player_stats_2018['Player'].str.lower()
        draft_rankings_and_projections_and_stats = draft_rankings_and_projections.merge(self.player_stats_2018,
                                                                                        how='left', left_on="Name",
                                                                                        right_on="Player_lower")
        draft_rankings_and_projections_and_stats.to_csv("draft_cheat_sheet.csv", index=True)
        return


class FantasyFootballSeason(FantasyFootball):
    def __init__(self):
        super().__init__()


class KeeperAnalysis(FantasyFootballDraft):
    """
    Info
    """

    def __init__(self):
        super().__init__()
        self.roster_2018 = self.get_roster_2018()
        self.keeper_current_values = self.get_keeper_current_values()
        self.keeper_full_values = self.get_keeper_full_values()
        self.keeper_trade_values = self.get_keeper_trade_values()

    def get_roster_2018(self):
        try:
            data = pd.read_csv('2018_roster.csv')
            return data
        except:
            print('### Could not find file 2018_roster.csv ###')
            return None

    def get_keeper_current_values(self):
        roster_2018 = self.roster_2018
        self.draft_rankings['Name'] = self.draft_rankings['Overall (Team)'].str.lower()

        draft_rankings = self.draft_rankings
        draft_rankings = draft_rankings.drop(['Best', 'Worst', 'Bye'], axis=1)
        team_draft_values = self.team_draft_values
        roster_2018['name_validated'] = self.correlate_player_names()
        self.roster_2018 = roster_2018
        roster_2018 = roster_2018.drop(['name', 'drafted round', 'position'], axis=1)
        keeper_current_values = roster_2018.merge(draft_rankings, how='left', left_on='name_validated',
                                                  right_on='Name')
        keeper_current_values = keeper_current_values[keeper_current_values.Rank.notnull()]
        keeper_current_values['Rank'] = keeper_current_values['Rank'].astype('int')
        keeper_current_values = keeper_current_values.merge(self.draft_value, how='left', left_on='Rank',
                                                            right_on='Pick')
        keeper_current_values = keeper_current_values.drop(['Name'], axis=1)
        return keeper_current_values

    def get_keeper_full_values(self):
        keeper_full_values = self.keeper_current_values.merge(
            self.team_draft_values[['Team', 'Round', 'Value', 'Pick', '% of no. 1 pick']], how='left',
            left_on=['team', 'keeper round'], right_on=['Team', 'Round'])
        keeper_full_values = keeper_full_values.drop(['Team_y', 'Round_y'], axis=1)
        keeper_full_values[
            ['name_validated', 'Pos', 'Team_x', 'team', 'keeper round', 'Pick_y', 'Value_y', '% of no. 1 pick_y', 'Avg',
             'Round_x', 'Rank', 'Value_x', '% of no. 1 pick_x']]
        keeper_full_values = keeper_full_values.dropna()
        keeper_full_values['Value_add'] = keeper_full_values['Value_x'] - keeper_full_values['Value_y']
        keeper_full_values['Value_add_norm'] = keeper_full_values['% of no. 1 pick_x'] - keeper_full_values[
            '% of no. 1 pick_y']
        keeper_full_values.Round_x = keeper_full_values.Round_x.astype('int')
        keeper_full_values = keeper_full_values[
            ['name_validated', 'Pos', 'Team_x', 'team', 'keeper round', 'Round_x', 'Value_add', 'Value_add_norm']]
        return keeper_full_values.sort_values(['Value_add'], ascending=False)

    def get_keeper_trade_values(self):
        keeper_trade_values = pd.DataFrame([])
        keeper_current_values = self.keeper_current_values
        best_keeper_value = self.get_best_keeper_value()
        my_keepers = keeper_current_values[keeper_current_values.team == 'Danny']
        for team in self.draft_keeper_2019.Team:
            if team != "Danny":
                my_keepers.team = team
                full_merge = my_keepers.merge(
                    self.team_draft_values[['Team', 'Round', 'Value', 'Pick', '% of no. 1 pick']], how='left',
                    left_on=['team', 'keeper round'], right_on=['Team', 'Round'])
                full_merge = full_merge.drop(['Team_y', 'Round_y'], axis=1)
                full_merge = full_merge.dropna()
                full_merge['Value_add'] = full_merge['Value_x'] - full_merge['Value_y']
                full_merge['Value_add_norm'] = full_merge['% of no. 1 pick_x'] - full_merge['% of no. 1 pick_y']
                full_merge.Round_x = full_merge.Round_x.astype('int')
                full_merge = full_merge[
                    ['name_validated', 'Pos', 'Team_x', 'team', 'keeper round', 'Round_x', 'Value_add',
                     'Value_add_norm']]
                full_merge['trade_value'] = full_merge.Value_add - float(
                    best_keeper_value.Value_add[best_keeper_value.team == team])
                keeper_trade_values = keeper_trade_values.append(full_merge, ignore_index=True)
        keeper_trade_values = \
            keeper_trade_values[['name_validated', 'team', 'trade_value']] \
                .sort_values(['trade_value'], ascending=False)[keeper_trade_values.trade_value > 0]
        draft_value = self.draft_value
        keeper_trade_values['trade_round'] = keeper_trade_values.trade_value.apply(
            lambda x: int(draft_value.Round[draft_value.Value == min(draft_value.Value, key=lambda y: abs(y - x))]))
        return keeper_trade_values

    def correlate_player_names(self):
        name_validated = np.array([])
        roster_2018_players = self.roster_2018.name.str.lower()
        fantasy_pros_players = self.draft_rankings['Overall (Team)'].str.lower()
        for name in roster_2018_players:
            estimate = process.extractOne(name, fantasy_pros_players, scorer=fuzz.ratio)
            est1 = estimate[0]
            est_per = estimate[1]
            if (est_per < 100) & (est_per >= 85):
                # print('Name = {}, Estimated = {}, Percent = {}'.format(name, est1, est_per))
                name_validated = np.append(name_validated, est1)
            else:
                name_validated = np.append(name_validated, name)
        return name_validated

    def get_best_keeper_value(self):
        best_keeper_value = self.keeper_full_values.groupby(['team'])['Value_add'].max().reset_index()
        return best_keeper_value

    def visualize_keeper_full_values(self):
        keeper_full_values = self.keeper_full_values
        keeper_full_values_viz = keeper_full_values[keeper_full_values.Value_add > 0].sort_values(['team', 'Value_add'],
                                                                                                  ascending=False)
        y_val = keeper_full_values_viz['Value_add']
        x_val = np.arange(len(y_val))
        x_names = keeper_full_values_viz['name_validated']
        x_colors = {
            'Danny': 'blue',
            'Zack': 'red',
            'Hunter': 'orange',
            'Nate': 'yellow',
            'Brendan': 'green',
            'Mac': 'purple',
            'Vinay': 'pink',
            'Bryan': 'black'
        }
        color = [x_colors[val] for val in keeper_full_values_viz.team]
        plt.figure(figsize=(20, 10))
        plt.bar(x_val, y_val, align='center', color=color)
        plt.xticks(x_val, x_names)
        plt.xticks(rotation=90)
        plt.ylabel('Keeper Value')
        plt.title('Keeper Analysis')
        plt.show()
