import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as bs
import time
import random
import re
import math


class RequestFantasyProsData:
    """
        Info
    """
    def __init__(self):
        self.session_fantasyPros = requests.Session()
        self.header = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}

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

    def request_player_projections_week(self, week, top20=False):
        if top20:
            login_check = self.login_fantasy_pros()
            if login_check == "Error":
                print("### Error returning draft rankings ###")
                return None
        return RequestPlayerProjections(self.session_fantasyPros, self.header, week, top20).data

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
        random.shuffle(self.positions)
        print('-Scraping FantasyPros')

    def validate_response(self, response, pos):
        if response.ok:
            data = self.get_data(response, pos)
            self.data = self.data.append(data, sort=False)
            if pos != self.positions[-1]:
                wait = random.randint(500, 1000) / 100
                print('   -Scraped data for {} position, wait {} seconds for next'.format(pos, int(wait)))
                time.sleep(wait)
            else:
                print('   -Scraped data for {} position'.format(pos))
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
    def __init__(self, session_fantasyPros, header, week, top20=False):
        super().__init__()
        self.session_fantasyPros = session_fantasyPros
        self.header = header
        self.week = str(week)
        self.url = 'https://www.fantasypros.com/nfl/projections/{}.php?scoring=PPR&week={}'
        if top20:
            self.url = self.url + "?filters=47558abd64"
        for pos in self.positions:
            self.position_requests(pos)
        print("-Done scraping")
        self.data = self.fix_data()
        self.data.to_csv('player_projections_{}.csv'.format(self.week), index=False)
        print('-Data Saved to "player_projections_{}.csv"'.format(self.week))

    def position_requests(self, pos):
        response = self.session_fantasyPros.get(self.url.format(pos, self.week), headers=self.header)
        self.validate_response(response, pos)
        return

    def fix_data(self):
        data = self.data
        data.Player[data.SAFETY.notnull()] = data.Player[data.SAFETY.notnull()].apply(lambda x: x.split()[-1] + "D/ST")
        data['FPTS'][data.FPTS.isna()] = data['MISC FPTS'][data.FPTS.isna()]
        return data.reset_index()


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

