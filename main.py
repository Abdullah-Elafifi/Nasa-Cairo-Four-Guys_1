import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import folium
import xarray as xr

data = pd.read_csv('MOP02J-20001109-L2V18.0.3.csv')

data_cleaned = data.dropna(subset=['COTotalColumn'])

data_cleaned['COTotalColumn'] = data_cleaned['COTotalColumn'] / 1e18

features = ['Latitude', 'Longitude', 'COTotalColumn']
X_co2 = data_cleaned[features].values

model_co2 = IsolationForest(contamination=0.05)
model_co2.fit(X_co2)

data_cleaned['anomaly'] = model_co2.predict(X_co2)
anomalies_co2 = data_cleaned[data_cleaned['anomaly'] == -1]

methane_data = xr.open_dataset('Express_Extension_Gridded_GHGI_Methane_v2_2020.nc')

latitudes = methane_data['lat'].values
longitudes = methane_data['lon'].values

methane_emissions = methane_data['emi_ch4_1A_Combustion_Mobile'].isel(time=0).values

lat_flat = np.repeat(latitudes, len(longitudes))
lon_flat = np.tile(longitudes, len(latitudes))
methane_flat = methane_emissions.flatten()

methane_df = pd.DataFrame({
    'Latitude': lat_flat,
    'Longitude': lon_flat,
    'MethaneEmissions': methane_flat
})

virginia_lat_bounds = (36.54, 39.47)
virginia_lon_bounds = (-83.67, -75.23)

data_cleaned = data_cleaned[
    (data_cleaned['Latitude'].between(*virginia_lat_bounds)) &
    (data_cleaned['Longitude'].between(*virginia_lon_bounds))
]

methane_df = methane_df[
    (methane_df['Latitude'].between(*virginia_lat_bounds)) &
    (methane_df['Longitude'].between(*virginia_lon_bounds))
]

methane_threshold = 0.001
methane_df = methane_df[methane_df['MethaneEmissions'] >= methane_threshold]

X_methane = methane_df[['Latitude', 'Longitude', 'MethaneEmissions']].fillna(0).values
model_methane = IsolationForest(contamination=0.05)
model_methane.fit(X_methane)

methane_df['anomaly'] = model_methane.predict(X_methane)
normal_methane_df = methane_df[methane_df['anomaly'] == 1]
num_to_remove = int(0.45 * len(normal_methane_df))
remove_indices = np.random.choice(normal_methane_df.index, num_to_remove, replace=False)
methane_df = methane_df.drop(remove_indices)
anomalies_methane = methane_df[methane_df['anomaly'] == -1]

m = folium.Map(location=[37.5, -78.5], zoom_start=7,
                tiles='OpenStreetMap',
                attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors')

co2_normal = folium.FeatureGroup(name='Normal CO2 Emissions', show=True)
co2_anomalies = folium.FeatureGroup(name='CO2 Anomalies', show=True)

for idx, row in data_cleaned[data_cleaned['anomaly'] == 1].iterrows():
    size = np.clip(row['COTotalColumn'] * 150, 5, 40)
    co2_normal.add_child(
        folium.CircleMarker([row['Latitude'], row['Longitude']],
                            radius=size,
                            color='green',
                            fill=True,
                            fill_opacity=0.6))

for idx, row in anomalies_co2.iterrows():
    size = np.clip(row['COTotalColumn'] * 150, 5, 40)
    co2_anomalies.add_child(
        folium.CircleMarker(
            [row['Latitude'], row['Longitude']],
            radius=size,
            color='red',
            fill=True,
            fill_opacity=0.6,
            tooltip=f"CO₂: {row['COTotalColumn']:.4f}"
        )
    )

m.add_child(co2_normal)
m.add_child(co2_anomalies)

methane_normal = folium.FeatureGroup(name='Normal Methane Emissions', show=True)
methane_anomalies = folium.FeatureGroup(name='Methane Anomalies', show=True)

for idx, row in methane_df[methane_df['anomaly'] == 1].iterrows():
    size = np.clip(row['MethaneEmissions'] * 150, 5, 25)
    methane_normal.add_child(
        folium.CircleMarker([row['Latitude'], row['Longitude']],
                            radius=size,
                            color='blue',
                            fill=True,
                            fill_opacity=0.6)
    )

for idx, row in anomalies_methane.iterrows():
    size = np.clip(row['MethaneEmissions'] * 150, 10, 40)
    methane_anomalies.add_child(
        folium.CircleMarker(
            [row['Latitude'], row['Longitude']],
            radius=size,
            color='blue',
            fill=True,
            fill_opacity=0.8,
            tooltip=f"Methane: {row['MethaneEmissions']:.4f}"
        )
    )

m.add_child(methane_normal)
m.add_child(methane_anomalies)

folium.LayerControl(position='bottomright').add_to(m)

control_html = """
<div style="position: fixed; 
            bottom: 10px; left: 50%; 
            transform: translateX(-50%); 
            width: 80%; 
            background-color: rgba(255, 255, 255, 0.9); 
            border-radius: 10px; 
            padding: 15px; 
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);">
    <h4 style="text-align: center; margin: 0; color: #2a2a2a;">Layer Control</h4>
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
        <label><input type="checkbox" id="co2_normal" checked> Normal CO2</label>
        <label><input type="checkbox" id="co2_anomalies" checked> CO2 Anomalies</label>
        <label><input type="checkbox" id="methane_normal" checked> Normal Methane</label>
        <label><input type="checkbox" id="methane_anomalies" checked> Methane Anomalies</label>
    </div>
</div>
<script>
    var layers = {
        'co2_normal': {},
        'co2_anomalies': {},
        'methane_normal': {},
        'methane_anomalies': {}
    };
    function toggleLayer(layerId, checked) {
        if (checked) {
            map.addLayer(layers[layerId]);
        } else {
            map.removeLayer(layers[layerId]);
        }
    }
    document.getElementById('co2_normal').addEventListener('change', function() {
        toggleLayer('co2_normal', this.checked);
    });
    document.getElementById('co2_anomalies').addEventListener('change', function() {
        toggleLayer('co2_anomalies', this.checked);
    });
    document.getElementById('methane_normal').addEventListener('change', function() {
        toggleLayer('methane_normal', this.checked);
    });
    document.getElementById('methane_anomalies').addEventListener('change', function() {
        toggleLayer('methane_anomalies', this.checked);
    });
</script>
"""

m.get_root().html.add_child(folium.Element(control_html))

m.save('emissions_anomalies_map_virginia_with_ripples.html')
