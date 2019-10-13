import json
from FFL import espnffl

try:
    with open("D:/Github/espn_cookies.json") as file:
        data = file.read()
        data_json = json.loads(data)
except:
    data_json = {
        "espn_s2": "",
        "swid": "",
        "league_id": ""
    }

league_id = data_json["league_id"]
swid = data_json["SWID"]
espn_s2 = data_json["espn_s2"]

espn_ffl = espnffl.RequestData(league_id, swid, espn_s2)
