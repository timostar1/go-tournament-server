import requests
import xlrd
import json
from pprint import pprint


r = requests.get("http://gofederation.ru/players/?export=xlsx")

#with open("players.xlsx", "wb+") as f:
    #f.write(r.content)
    
players = xlrd.open_workbook(file_contents=r.content).sheet_by_index(0)
d = {"players": []}
i = 0

for row in players.get_rows():
    if i > 0:
        player = {"num": int(row[0].value),
                  "name": row[1].value,
                  "rating": int(row[2].value),
                  "r-delta": int(row[3].value),
                  "city": row[6].value,}
        d["players"].append(player)
    i += 1
    
pprint(d["players"][:100])