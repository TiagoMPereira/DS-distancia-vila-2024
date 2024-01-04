import pandas as pd


data = pd.read_csv("./data/scenarios.csv")

regioes = {
    "Norte": ["PA", "AM"],
    "Nordeste": ["CE", "BA", "PE", "AL"],
    "Sul": ["RS", "PR", "SC"],
    "Sudeste": ["SP", "RJ", "MG"],
    "Centro-Oeste": ["GO", "MT"]
}

valores_regioes = []

for state in data["state"]:
    for reg, states in regioes.items():
        if state in states:
            valores_regioes.append(reg)

data['region'] = valores_regioes

data.to_csv("./data/scenarios.csv", index=False)