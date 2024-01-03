import shutil

import requests
import json
import time

with open("./data/link_images.json", "r") as fp:
    links = json.load(fp)

for team in links:
    url = team["image"]
    nome = team["team"]
    print(nome)

    response = requests.get(url, stream=True)
    with open(f'./data/images/teams/{nome}.png', 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)

    time.sleep(5)
