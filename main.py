import base64
from io import BytesIO
import streamlit as st
import pandas as pd
from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

SCENARIOS = {
    "1": "Santos rebaixado",
    "2": "Vasco rebaixado",
    "3": "Bahia rebaixado",
}

def set_df_scenario(df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    current_scenario = f"scenario_{scenario}"
    santos_division = df.loc[df["team"] == "Santos FC", [current_scenario]].values[0][0]
    teams = df.loc[df[current_scenario] == santos_division]
    return teams


def get_coordinates(df: pd.DataFrame) -> dict:

    _df = df.copy()
    _infos = []
    for _, row in _df.iterrows():
        info = (f"{row['team']} - {row['stadium']}<br>{row['city']} - {row['state']}"
                f"<br>Distância para Vila Belmiro: {round(row['vila_distance'], 2)} km"
                f"<br>({round(row['lat'], 4)}, {round(row['long'], 4)})")
        _infos.append(info)
    _df['infos'] = _infos
    _lat = _df.loc[:, "lat"].values
    _long = _df.loc[:, "long"].values
    _infos = _df.loc[:, "infos"].values
    return {
        "lat": _lat, "long": _long, "infos": _infos
    }


def run(df: pd.DataFrame):

    st.set_page_config(page_title="Distância Vila", page_icon="🏟️")

    st.title('Distância da Vila Belmiro 🏟️')

    st.markdown(
        "As distâncias são referentes à Vila Belmiro e aos estádios visitantes. Saiba mais na seção 'Informações' no fim da página."
    )

    selected_tab = st.sidebar.selectbox("Selecione um cenário", SCENARIOS.values())
    selected_scenario = [k for k, v in SCENARIOS.items() if v == selected_tab][0]
    df_scenario = set_df_scenario(df, selected_scenario)

    coordinates = get_coordinates(df_scenario)

    mapa = plot_map(coordinates)
    st.plotly_chart(mapa, key="k1")

    distances_near, distances_far = st.columns(2)

    # Adicionar conteúdo ao primeiro container (distances_near)
    with distances_near:
        top_distances_near = plot_top_distances_bar(df_scenario, near=True)
        st.plotly_chart(top_distances_near)

    # Adicionar conteúdo ao segundo container (distances_far)
    with distances_far:
        top_distances_far = plot_top_distances_bar(df_scenario, near=False)
        st.plotly_chart(top_distances_far)

    all_distances_bar = plot_all_distances_bar(df_scenario)
    expander = st.expander("Visualizar as distâncias dos estádios de cada clube")
    expander.plotly_chart(all_distances_bar)

    st.subheader('Comparação entre cenários 🆚')

    col_plot, col_selecao = st.columns([2, 1])
    stat = col_selecao.selectbox('Selecione a estatística:', ['Total', 'Média', 'Máxima', 'Mínima', 'Mediana', 'Desvio Padrão'])
    summary = total_scenarios(df, stat)
    col_plot.plotly_chart(summary)

    expander_bp = st.expander("Visualizar detalhes (Boxplot)")
    boxplots = boxplot_scenarios(df)
    expander_bp.plotly_chart(boxplots)

    regioes = plot_region(df)
    st.plotly_chart(regioes)
    estados = plot_states(df)
    st.plotly_chart(estados)

    st.divider()

    st.markdown(
        "Com o rebaixamento para a segunda divisão do Campeonato "
        "Brasileiro de Futebol Masculino o Santos passa a enfrentar mais "
        "adversários do estado de São Paulo (6) do que caso estivesse permanecido "
        "na Série A (4). Entretanto, quando analisamos outros estados da região "
        "Sudeste, há uma queda no número de adversários, visto que, em Minas Gerais, "
        "o clube deixa de enfrentar Atlético Mineiro e Cruzeiro, e confronta apenas "
        "o América. Já no Rio de Janeiro, na Série B o Santos não possui nenhum "
        "clube adversário, caso permanecesse na primeira divisão enfrentaria 4 adversários "
        "em caso de queda do Bahia, ou 3 caso o Vasco da Gama fosse rebaixado.\n\n"
        "Conduzindo a análise para a região Sul, o Santos deixa de enfrentar 3 adversários "
        "no Rio Grande do Sul, que representa o estado mais distante de São Paulo dentro "
        "da região. O número de adversários em Santa Catarina aumenta em 2 enquanto "
        "no Paraná, estado mais próximo, aumenta 1.\n\n"
        "No Centro-Oeste do país, o Peixe deixa de enfrentar o Cuiabá, do Mato Grosso e "
        "passa a enfrentar um adversário a mais em Goiás. Em comparação as distâncias "
        "passam a ser menores com o Santos na B.\n\n"
        "No Nordeste os adversários da Série B ficam mais distantes, o mais distante da região "
        "é o Ceará (Santos na B) ou Fortaleza (Santos na A), contudo, atualmente o Santos "
        "viaja para Pernambuco e Alagoas, além do Ceará, enquanto na Série A viajaria para "
        "o Ceará e Bahia (2 vezes caso o Vasco fosse rebaixado ou 1 vez caso o Bahia caísse) "
        "isso aumenta a distância total.\n\n"
        "A região que mais afeta a distância percorrida na Série B é a Norte, caso o peixe permanecesse "
        "na Série A, não teria nenhum adversário na região mais distante, entretanto, com a queda "
        "passa a viajar para o Pará (Paysandu) e para o Amazonas (Amazonas), assim aumentando "
        "a distância percorrida ao longo da temporada.\n\n"
        "Com o rebaixamento do Santos, a mediana das distâncias entre estádios "
        "diminui, por enfrentar mais adversários dos estados de São Paulo, "
        "Paraná e Santa Catarina, entretanto, ao enfrentar os adversários do Norte "
        "(Amazonas e Paysandu) a distribuição das distâncias acaba aumentando."
    )


    st.divider()

    expander = st.expander("Informações")
    expander.markdown("##### Distâncias")
    expander.markdown(
        "As distâncias calculadas são entre a Vila Belmiro e os estádios adversários. "
        "Não foram considerados os percursos entre os estádios bem como estradas e distâncias entre "
        "aeroportos, caso necessário. Foi considerada apenas a distância geodésica entre os pontos."
    )
    expander.markdown("##### Cálculo das distâncias")
    expander.markdown(
        "As distâncias foram calculadas pelo serviço GeoPy baseando-se nas "
        "coordenadas dos estádios. O cálculo é feito considerando a distância "
        "em um plano em três dimensões ([geodésica](https://doc.arcgis.com/pt-br/arcgis-online/analyze/geodesic-versus-planar-distance.htm#:~:text=A%20dist%C3%A2ncia%20geod%C3%A9sica%20%C3%A9%20calculada,da%20superf%C3%ADcie%20curva%20do%20mundo.)), "
        "como a superfície esférica da Terra. "
    )
    expander.markdown("##### Fontes")
    expander.markdown(
        f"- Estádios: https://www.transfermarkt.com.br/\n"
        f"- Localizações: https://api.opencagedata.com/geocode/v1/ (acesso via API). As localizações foram validadas manualmente\n"
        f"- Imagens: https://www.sofascore.com/\n"
        f"- Cálculo das distâncias: https://geopy.readthedocs.io/en/stable/\n"
    )

    st.markdown("Desenvolvido por: [Tiago Pereira](https://www.linkedin.com/in/tiago-pereira-demorais/)")

def plot_states(data: pd.DataFrame):
    _c1 = set_df_scenario(data, "1")
    _c1 = _c1.loc[_c1['team'] != "Santos FC"]
    _c2 = set_df_scenario(data, "2")
    _c2 = _c2.loc[_c2['team'] != "Santos FC"]
    _c3 = set_df_scenario(data, "3")
    _c3 = _c3.loc[_c3['team'] != "Santos FC"]

    _c1_st = dict(_c1['state'].value_counts())
    _c2_st = dict(_c2['state'].value_counts())
    _c3_st = dict(_c3['state'].value_counts())

    _aux_df = pd.DataFrame([_c1_st, _c2_st, _c3_st]).fillna(0).T
    _aux_df.columns = ["Santos rebaixado", "Vasco rebaixado", "Bahia rebaixado"]
    _d1 = dict(_aux_df['Santos rebaixado'])
    _d2 = dict(_aux_df['Vasco rebaixado'])
    _d3 = dict(_aux_df['Bahia rebaixado'])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(_d1.keys()),
        y=list(_d1.values()),
        name='Santos rebaixado',
        marker_color='rgb(220, 220, 220)',
        hovertemplate='%{y}'
    ))
    fig.add_trace(go.Bar(
        x=list(_d2.keys()),
        y=list(_d2.values()),
        name='Vasco rebaixado',
        marker_color='rgb(150, 150, 150)',
        hovertemplate='%{y}'
    ))
    fig.add_trace(go.Bar(
        x=list(_d3.keys()),
        y=list(_d3.values()),
        name='Bahia rebaixado',
        marker_color='rgb(70, 70, 70)',
        hovertemplate='%{y}'
    ))

    # Atualizar layout
    fig.update_layout(
        barmode='group',  # Agrupar barras lado a lado
        height=400,
        width=800,
        showlegend=True,
        legend=dict(title='Cenários'),
        yaxis=dict(title='Adversários por estado'),
        title="Quantidade de adversários do Santos por estado em cada cenário"
    )
    
    return fig


def plot_region(data: pd.DataFrame):
    _c1 = set_df_scenario(data, "1")
    _c1 = _c1.loc[_c1['team'] != "Santos FC"]
    _c2 = set_df_scenario(data, "2")
    _c2 = _c2.loc[_c2['team'] != "Santos FC"]
    _c3 = set_df_scenario(data, "3")
    _c3 = _c3.loc[_c3['team'] != "Santos FC"]

    _c1_st = dict(_c1['region'].value_counts())
    _c2_st = dict(_c2['region'].value_counts())
    _c3_st = dict(_c3['region'].value_counts())

    _aux_df = pd.DataFrame([_c1_st, _c2_st, _c3_st]).fillna(0).T
    _aux_df.columns = ["Santos rebaixado", "Vasco rebaixado", "Bahia rebaixado"]
    _d1 = dict(_aux_df['Santos rebaixado'])
    _d2 = dict(_aux_df['Vasco rebaixado'])
    _d3 = dict(_aux_df['Bahia rebaixado'])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(_d1.keys()),
        y=list(_d1.values()),
        name='Santos rebaixado',
        marker_color='rgb(220, 220, 220)',
        hovertemplate='%{y}'
    ))
    fig.add_trace(go.Bar(
        x=list(_d2.keys()),
        y=list(_d2.values()),
        name='Vasco rebaixado',
        marker_color='rgb(150, 150, 150)',
        hovertemplate='%{y}'
    ))
    fig.add_trace(go.Bar(
        x=list(_d3.keys()),
        y=list(_d3.values()),
        name='Bahia rebaixado',
        marker_color='rgb(70, 70, 70)',
        hovertemplate='%{y}'
    ))

    # Atualizar layout
    fig.update_layout(
        barmode='group',  # Agrupar barras lado a lado
        height=400,
        width=800,
        showlegend=True,
        legend=dict(title='Cenários'),
        yaxis=dict(title='Adversários por região'),
        title="Quantidade de adversários do Santos por região em cada cenário"
    )
    
    return fig

def total_scenarios(data: pd.DataFrame, stat: str):
    _c1 = set_df_scenario(data, "1")
    _c1 = _c1.loc[_c1['team'] != "Santos FC"]
    _c2 = set_df_scenario(data, "2")
    _c2 = _c2.loc[_c2['team'] != "Santos FC"]
    _c3 = set_df_scenario(data, "3")
    _c3 = _c3.loc[_c3['team'] != "Santos FC"]

    if stat == "Média":
        labels = ["Distância média"]
        c1_dist = [round(_c1['vila_distance'].mean(), 4)]
        c2_dist = [round(_c2['vila_distance'].mean(), 4)]
        c3_dist = [round(_c3['vila_distance'].mean(), 4)]
    
    elif stat == "Mediana":
        labels = ["Distância mediana"]
        c1_dist = [round(_c1['vila_distance'].median(), 4)]
        c2_dist = [round(_c2['vila_distance'].median(), 4)]
        c3_dist = [round(_c3['vila_distance'].median(), 4)]
    
    elif stat == "Máxima":
        labels = ["Distância máxima"]
        c1_dist = [round(_c1['vila_distance'].max(), 4)]
        c2_dist = [round(_c2['vila_distance'].max(), 4)]
        c3_dist = [round(_c3['vila_distance'].max(), 4)]
    
    elif stat == "Mínima":
        labels = ["Distância mínima"]
        c1_dist = [round(_c1['vila_distance'].min(), 4)]
        c2_dist = [round(_c2['vila_distance'].min(), 4)]
        c3_dist = [round(_c3['vila_distance'].min(), 4)]
    
    elif stat == "Desvio Padrão":
        labels = ["Desvio padrão da distância"]
        c1_dist = [round(_c1['vila_distance'].std(), 4)]
        c2_dist = [round(_c2['vila_distance'].std(), 4)]
        c3_dist = [round(_c3['vila_distance'].std(), 4)]

    else:
        labels = ["Distância total"]
        c1_dist = [round(_c1['vila_distance'].sum(), 4)]
        c2_dist = [round(_c2['vila_distance'].sum(), 4)]
        c3_dist = [round(_c3['vila_distance'].sum(), 4)]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels,
        y=c1_dist,
        name='Santos rebaixado',
        marker_color='rgb(220, 220, 220)',
        hovertemplate='%{y}'
    ))
    fig.add_trace(go.Bar(
        x=labels,
        y=c2_dist,
        name='Vasco rebaixado',
        marker_color='rgb(150, 150, 150)',
        hovertemplate='%{y}'
    ))
    fig.add_trace(go.Bar(
        x=labels,
        y=c3_dist,
        name='Bahia rebaixado',
        marker_color='rgb(70, 70, 70)',
        hovertemplate='%{y}'
    ))

    # Atualizar layout
    fig.update_layout(
        barmode='group',  # Agrupar barras lado a lado
        height=400,
        width=600,
        showlegend=True,
        legend=dict(title='Cenários'),
        yaxis=dict(title='Distância em km'),
    )
    return fig

def boxplot_scenarios(data: pd.DataFrame):
    _c1 = set_df_scenario(data, "1")
    _c1 = _c1.loc[_c1['team'] != "Santos FC"]
    _c2 = set_df_scenario(data, "2")
    _c2 = _c2.loc[_c2['team'] != "Santos FC"]
    _c3 = set_df_scenario(data, "3")
    _c3 = _c3.loc[_c3['team'] != "Santos FC"]

    _c1['Category'] = 'Santos rebaixado'
    _c2['Category'] = 'Vasco rebaixado'
    _c3['Category'] = 'Bahia rebaixado'

    # Concatenar os dataframes
    combined_df = pd.concat([_c1, _c2, _c3])

    # Criar boxplots usando Plotly Express
    fig = px.box(combined_df, x='Category', y='vila_distance', points="all", title='Distribuições das distâncias', hover_data=['vila_distance', 'Category', 'team', 'stadium'], labels={'vila_distance': "Distância (km)", 'Category': "Cenário", 'team': "Clube", 'stadium': "Estádio"})

    # Atualizar layout
    fig.update_layout(
        height=400,
        width=600,
        showlegend=True,
        legend=dict(title='Legendas'),
        xaxis=dict(title='Cenários'),
        yaxis=dict(title='Distância em km'),
    )
    return fig

def plot_all_distances_bar(dataframe: pd.DataFrame):
    df = dataframe.loc[dataframe['team'] != "Santos FC"]
    df = df.sort_values(by="vila_distance", ascending=True)

    image_base = "./data/images/teams/"
    _images = {}
    for _nome, _img in zip(df['team'], df['img']):
        image_path = image_base+_img+".png"
        img = Image.open(image_path)
        _images[_nome] = img

    color = 'rgb(150, 150, 150)'

    fig = make_subplots(rows=1, cols=1)

    fig.add_trace(go.Bar(
        x=df["team"], y=df["vila_distance"], marker_color=color,
        customdata=df[['stadium', 'city', 'state']],
        hovertemplate='Estádio: %{customdata[0]}<br>Distância (km): %{y}<br>%{customdata[1]}-%{customdata[2]}'
    ), row=1, col=1)

    fig.update_layout(
        images=[go.layout.Image(
            source=img,
            xref="x",
            yref="paper",
            x=category,
            y=0,
            sizex=0.4,
            sizey=0.4,
            xanchor="center",
            yanchor="bottom",
        ) for category, img in _images.items()]
    )
    
    fig.update_layout(height=400, width=650, showlegend=False, yaxis_title="km")
    fig.update_xaxes(tickangle=-75)

    return fig

def plot_top_distances_bar(dataframe: pd.DataFrame, near: bool):
    
    # Distâncias
    df = dataframe.loc[dataframe['team'] != "Santos FC"]
    df = df.sort_values(by="vila_distance", ascending=True)

    if near:
        df = df.head(3)
        color = 'rgb(188, 188, 188)'
        title = 'Clubes com estádios mais próximos da Vila Belmiro'
    else:
        df = df.tail(3)
        df = df.sort_values(by="vila_distance", ascending=False)
        color = 'rgb(109, 109, 109)'
        title = 'Clubes com estádios mais distantes da Vila Belmiro'

    image_base = "./data/images/teams/"
    _images = {}
    for _nome, _img in zip(df['team'], df['img']):
        image_path = image_base+_img+".png"
        img = Image.open(image_path)
        _images[_nome] = img

    fig = make_subplots(rows=1, cols=1, subplot_titles=[title])

    fig.add_trace(go.Bar(
        x=df["team"], y=df["vila_distance"], marker_color=color,
        customdata=df[['stadium', 'city', 'state']],
        hovertemplate='Estádio: %{customdata[0]}<br>Distância (km): %{y}<br>%{customdata[1]}-%{customdata[2]}'
    ), row=1, col=1)

    fig.update_layout(
        images=[go.layout.Image(
            source=img,
            xref="x",
            yref="paper",
            x=category,
            y=0,
            sizex=0.5,
            sizey=0.5,
            xanchor="center",
            yanchor="bottom",
        ) for category, img in _images.items()]
    )
    
    fig.update_layout(height=400, width=300, showlegend=False, yaxis_title="km")

    return fig

def plot_map(coordinates: dict):

    santos_position = [i for i, info in enumerate(coordinates['infos']) if info.startswith("Santos")][0]

    fig = go.Figure()

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            zoom=3,
            center=dict(lat=-15.6041, lon=-56.1223)
        ),
        height=750
    )
    for i, coord in enumerate(zip(coordinates["lat"], coordinates["long"])):

        fig.add_trace(go.Scattermapbox(
            lat=[coord[0]],
            lon=[coord[1]],
            text=coordinates['infos'][i],
            hoverinfo='text',
            line = dict(
                width = 1,
                color = "black",
            ),
            showlegend=False
        ))

    return fig

def display_content(selected_scenario):
    if selected_scenario == "1":
        st.write("Conteúdo da Aba 1")
    elif selected_scenario == "2":
        st.write("Conteúdo da Aba 2")
    elif selected_scenario == "3":
        st.write("Conteúdo da Aba 3")

if __name__ == "__main__":
    df = pd.read_csv("data/scenarios.csv")
    run(df)