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

    st.title('Distância da Vila Belmiro 🏟️')

    selected_tab = st.sidebar.selectbox("Selecione um cenário:", SCENARIOS.values())
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

    summary = total_scenarios(df)
    st.plotly_chart(summary)

    boxplots = boxplot_scenarios(df)
    st.plotly_chart(boxplots)

    expander = st.expander("Informações")
    expander.markdown("##### Cálculo das distâncias")
    expander.markdown("##### Fontes")

def total_scenarios(data: pd.DataFrame):
    _c1 = set_df_scenario(data, "1")
    _c1 = _c1.loc[_c1['team'] != "Santos FC"]
    _c2 = set_df_scenario(data, "2")
    _c2 = _c2.loc[_c2['team'] != "Santos FC"]
    _c3 = set_df_scenario(data, "3")
    _c3 = _c3.loc[_c3['team'] != "Santos FC"]

    labels = ["Distância total", "Distância média"]

    c1_dist = [round(_c1['vila_distance'].sum(), 4), round(_c1['vila_distance'].mean(), 4)]
    c2_dist = [round(_c2['vila_distance'].sum(), 4), round(_c2['vila_distance'].mean(), 4)]
    c3_dist = [round(_c3['vila_distance'].sum(), 4), round(_c3['vila_distance'].mean(), 4)]

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
        width=800,
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
        width=800,
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