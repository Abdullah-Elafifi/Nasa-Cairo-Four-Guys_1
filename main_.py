import folium
import pandas as pd

emissions_data = pd.read_csv('virginia_emissions_data.csv')

m = folium.Map(location=[37.5, -79.5], zoom_start=7)

def calculate_impact_score(emissions):
    return sum(emissions) / len(emissions)

grouped_data = emissions_data.groupby(['Latitude', 'Longitude'])

for (lat, lng), group in grouped_data:
    emissions = group['Emissions'].tolist()
    impact_score = calculate_impact_score(emissions)

    popup_content = f"""
    <b>Location:</b> ({lat}, {lng})<br>
    <b>Historical Emissions:</b> {emissions}<br>
    <b>Environmental Impact Score:</b> {impact_score:.2f}<br>
    <b>Facility Scenario:</b> {group['Facility_Scenario'].values[0]}<br>
    <button onclick="simulateScenario({lat}, {lng})">Simulate Scenario</button>
    """

    folium.Marker(location=[lat, lng],
                  popup=folium.Popup(popup_content, max_width=300)).add_to(m)

simulate_js = """
function simulateScenario(lat, lng) {
    // Dummy simulation logic
    var emissionsIncrease = Math.floor(Math.random() * 100) + 1; // Random increase
    alert(`Simulated emissions increase of ${emissionsIncrease} tons at (${lat}, ${lng})`);
}
"""

m.get_root().html.add_child(folium.Element(f'<script>{simulate_js}</script>'))

m.save('virginia_environmental_analysis_map.html')
