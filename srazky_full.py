import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Function to combine plots into single HTML
def combine_plotly_figs_to_html(plotly_figs, html_fname, include_plotlyjs='cdn', 
                                separator=None, auto_open=False):
    with open(html_fname, 'w') as f:
        f.write(plotly_figs[0].to_html(include_plotlyjs=include_plotlyjs))
        for fig in plotly_figs[1:]:
            if separator:
                f.write(separator)
            f.write(fig.to_html(full_html=False, include_plotlyjs=False))

    if auto_open:
        import pathlib, webbrowser
        uri = pathlib.Path(html_fname).absolute().as_uri()
        webbrowser.open(uri)

def fetch_json_from_url(url):
    response = requests.get(url)
    response.raise_for_status()  # Raises an error for bad status codes
    return response.json()

def json_to_dataframe(json_data):
    metadata = {
        'zaznamID': json_data['zaznamID'],
        'datovyZdrojID': json_data['datovyZdrojID'],
        'datovyTokID': json_data['datovyTokID'],
        'datumVytvoreni': json_data['datumVytvoreni'],
        'verzeDat': json_data['verzeDat']
    }
    # Extracting the header and values
    header = json_data['data']['data']['header'].split(',')
    values = json_data['data']['data']['values']
    
    # Creating a DataFrame from the values
    df_values = pd.DataFrame(values, columns=header)
    
    # Adding the metadata columns to the DataFrame
    for key, value in metadata.items():
        df_values[key] = value
         
    return df_values

def fetch_JSON(url):
    # Fetch JSON data
    json_data = fetch_json_from_url(url)
    # Convert JSON data to DataFrame
    df = json_to_dataframe(json_data)
    # Select
    df_all = df[['ELEMENT', 'DT', 'VAL']]
    # Convert DT to datetime format for better plotting
    df_all['DT'] = pd.to_datetime(df_all['DT'])
    # Filter year
    df_all = df_all[df_all['DT'].dt.year > 1986]
    # Filter srazky
    df_all = df_all[df_all["ELEMENT"] == "SRA"]
    # Ensure VAL is numeric, and drop rows with non-numeric values
    df_all['VAL'] = pd.to_numeric(df_all['VAL'], errors='coerce')
    df_all['VAL'] = df_all['VAL'].astype('float')
    df_all = df_all.dropna(subset=['VAL']).reset_index(drop=True)
    
    return df_all

def find_json_files(url, station_id):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a")
    json_files = [urljoin(url, link.get("href")) for link in links if link.get("href").endswith(".json") and station_id in link.get("href")]
    subfolders = [urljoin(url, link.get("href")) for link in links if link.get("href").endswith("/") and not link.get("href").startswith("..")]
    for folder in subfolders:
        json_files.extend(find_json_files(folder, station_id))
        
    return json_files

def main():
    #### Chelcice
    station_id = "dly-0-203-0-11539"
    url_history = "https://opendata.chmi.cz/meteorology/climate/historical/data/daily/" + station_id + ".json"
    url_recent = "https://opendata.chmi.cz/meteorology/climate/recent/data/daily/"
    #### CB Roznov
    # station_id = "dly-0-20000-0-11546"
    # url_history = "https://opendata.chmi.cz/meteorology/climate/historical/data/daily/" + station_id + ".json"
    # url_recent = "https://opendata.chmi.cz/meteorology/climate/recent/data/daily/"
    
    
    # url_history = "https://opendata.chmi.cz/meteorology/climate/historical/data/daily/dly-0-20000-0-11546.json"
    
    ######################
    #### history data ####
    ######################
    df_history = fetch_JSON(url_history)
    ######################
    #### recent data #####
    ######################
    json_files = find_json_files(url_recent, station_id = station_id)
    df_lst = [fetch_JSON(json) for json in json_files]
    df_recent = pd.concat(df_lst).reset_index(drop=True)
    
    df_all = pd.concat([df_history, df_recent]).reset_index(drop=True).sort_values(by=['DT']).reset_index(drop=True)

     # API 30
    df_all['mutiplied_VAL'] = df_all['VAL'] * 0.93
    df_all['API30'] = df_all['mutiplied_VAL'].rolling(window=30).sum()
    # 2-day srazky
    df_all['2_day_srazky'] = df_all['VAL'].rolling(window=2).sum()
    # 4-day srazky
    df_all['4_day_srazky'] = df_all['VAL'].rolling(window=4).sum()
    # 6-day srazky
    df_all['6_day_srazky'] = df_all['VAL'].rolling(window=6).sum()
    # 8-day srazky
    df_all['8_day_srazky'] = df_all['VAL'].rolling(window=8).sum()
    # 10-day srazky
    df_all['10_day_srazky'] = df_all['VAL'].rolling(window=10).sum()

    # Create an interactive plot
    fig = go.Figure()
    fig.add_scatter(x=df_all['DT'], y=df_all['API30'], mode='lines', name='API30 [mm]')
    fig.add_scatter(x=df_all['DT'], y=df_all['VAL'], mode='lines', name='1_day_srazky [mm]')
    fig.add_scatter(x=df_all['DT'], y=df_all['2_day_srazky'], mode='lines', name='2_day_srazky [mm]')
    fig.add_scatter(x=df_all['DT'], y=df_all['4_day_srazky'], mode='lines', name='4_day_srazky [mm]')
    fig.add_scatter(x=df_all['DT'], y=df_all['6_day_srazky'], mode='lines', name='6_day_srazky [mm]')
    fig.add_scatter(x=df_all['DT'], y=df_all['8_day_srazky'], mode='lines', name='8_day_srazky [mm]')
    fig.add_scatter(x=df_all['DT'], y=df_all['10_day_srazky'], mode='lines', name='10_day_srazky [mm]')
    fig.update_layout(title_text="Srážky - Chelčice")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="srážky [mm]")

    combine_plotly_figs_to_html([fig], "index.html",auto_open=True)

if __name__ == "__main__":
    main()