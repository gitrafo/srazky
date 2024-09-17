import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

def main(url):
    # Fetch JSON data
    json_data = fetch_json_from_url(url)
    # Convert JSON data to DataFrame
    df = json_to_dataframe(json_data)
    # Select
    filtered_df = df[['ELEMENT', 'DT', 'VAL']]
    # Convert DT to datetime format for better plotting
    filtered_df['DT'] = pd.to_datetime(filtered_df['DT'])
    # Filter year
    filtered_df = filtered_df[filtered_df['DT'].dt.year > 1986]
    # Filter srazky
    filtered_df = filtered_df[filtered_df["ELEMENT"] == "SRA"]
    # Ensure VAL is numeric, and drop rows with non-numeric values
    filtered_df['VAL'] = pd.to_numeric(filtered_df['VAL'], errors='coerce')
    filtered_df['VAL'] = filtered_df['VAL'].astype('float')
    filtered_df = filtered_df.dropna(subset=['VAL']).reset_index()
    # API 30
    filtered_df['mutiplied_VAL'] = filtered_df['VAL'] * 0.93
    filtered_df['API30'] = filtered_df['mutiplied_VAL'].rolling(window=30).sum()
    # 2-day srazky
    filtered_df['2_day_srazky'] = filtered_df['VAL'].rolling(window=2).sum()
    # 4-day srazky
    filtered_df['4_day_srazky'] = filtered_df['VAL'].rolling(window=4).sum()
    # 6-day srazky
    filtered_df['6_day_srazky'] = filtered_df['VAL'].rolling(window=6).sum()
    # 8-day srazky
    filtered_df['8_day_srazky'] = filtered_df['VAL'].rolling(window=8).sum()
    # 10-day srazky
    filtered_df['10_day_srazky'] = filtered_df['VAL'].rolling(window=10).sum()
    # Create an interactive plot
    fig = go.Figure()
    
    fig.add_scatter(x=filtered_df['DT'], y=filtered_df['API30'], mode='lines', name='API30 [mm]')
    fig.add_scatter(x=filtered_df['DT'], y=filtered_df['VAL'], mode='lines', name='1_day_srazky [mm]')
    fig.add_scatter(x=filtered_df['DT'], y=filtered_df['2_day_srazky'], mode='lines', name='2_day_srazky [mm]')
    fig.add_scatter(x=filtered_df['DT'], y=filtered_df['4_day_srazky'], mode='lines', name='4_day_srazky [mm]')
    fig.add_scatter(x=filtered_df['DT'], y=filtered_df['6_day_srazky'], mode='lines', name='6_day_srazky [mm]')
    fig.add_scatter(x=filtered_df['DT'], y=filtered_df['8_day_srazky'], mode='lines', name='8_day_srazky [mm]')
    fig.add_scatter(x=filtered_df['DT'], y=filtered_df['10_day_srazky'], mode='lines', name='10_day_srazky [mm]')
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Rožnov [mm]")

    combine_plotly_figs_to_html([fig], "API30.html",auto_open=True)

if __name__ == "__main__":
    # Chelcice
    # url = "https://opendata.chmi.cz/meteorology/climate/historical/data/daily/dly-0-203-0-11539.json"
    # CB Roznov
    url = "https://opendata.chmi.cz/meteorology/climate/historical/data/daily/dly-0-20000-0-11546.json"
    main(url)