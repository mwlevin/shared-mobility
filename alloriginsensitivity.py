import os
import pandas as pd
import folium
import matplotlib.cm as cm
import matplotlib.colors as colors
import re
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt

# -------------------------------
# File paths for the two travel time files,
# the network, and the nodes.
# -------------------------------
# Base scenario
travel_times_file1 = '/Users/mobjoon/Downloads/attempt2basescenario/travel_times.txt'
# Scenario: Just the Private Vehicle
travel_times_file2 = '/Users/mobjoon/Downloads/just the private vehicle/travel_times.txt'
network_file = '/Users/mobjoon/Downloads/DNDP-master 3/data/Minneapolis/net.txt'
nodes_file = '/Users/mobjoon/Downloads/nodes_lat_lon.csv'

# -------------------------------
# Scenario naming for legend.
# -------------------------------
base_scenario_name = "Base Scenario"
scenario_name = "Private Vehicle"

# -------------------------------
# Parse travel times
# -------------------------------
def parse_travel_times(file_path):
    travel_times = {}
    current_origin = None
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('Origin'):
                current_origin = int(re.search(r'Origin\s+(\d+)', line).group(1))
                travel_times[current_origin] = {}
            elif current_origin is not None and line:
                destinations = line.split(';')
                for destination in destinations:
                    if destination.strip():
                        dest, time = destination.split(':')
                        travel_times[current_origin][int(dest.strip())] = float(time.strip())
    return travel_times

# -------------------------------
# Parse network links (optional)
# -------------------------------
def parse_network(file_path):
    links = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('<') or 'Init node' in line or not line:
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                links.append((int(parts[0]), int(parts[1])))
    return links

# -------------------------------
# Get a color from a colormap.
# Here we use a blue-to-purple colormap (BuPu).
# -------------------------------
def get_color(value, min_val, max_val, cmap=cm.BuPu):
    norm = colors.Normalize(vmin=min_val, vmax=max_val)
    rgba_color = cmap(norm(value))
    return colors.to_hex(rgba_color)

# -------------------------------
# Create a difference accessibility map for a given origin.
# -------------------------------
def create_difference_accessibility_map(tt_data1, tt_data2, node_coords, network_links,
                                          selected_origin, store_locations, excluded_nodes,
                                          hospital_locations):
    # Check that the selected origin exists in both datasets.
    if selected_origin not in tt_data1 or selected_origin not in tt_data2:
        print(f"Origin {selected_origin} not found in one of the datasets!")
        return None

    # Compute differences (Scenario - Base Scenario)
    diff_travel_times = {}
    for node, base_time in tt_data1[selected_origin].items():
        if node in tt_data2[selected_origin] and node not in excluded_nodes:
            scenario_time = tt_data2[selected_origin][node]
            diff_travel_times[node] = scenario_time - base_time
    print(f"Origin {selected_origin}: computed differences for {len(diff_travel_times)} nodes.")

    # Prepare data for interpolation.
    points = []
    values = []
    for node, diff in diff_travel_times.items():
        if node in node_coords:
            lat, lon = node_coords[node]
            points.append([lat, lon])
            values.append(diff)
    points = np.array(points)
    values = np.array(values)
    if len(points) == 0:
        print(f"Origin {selected_origin}: no interpolation points found.")
        return None

    # Create a grid covering the area.
    lat_min, lat_max = points[:, 0].min() - 0.05, points[:, 0].max() + 0.05
    lon_min, lon_max = points[:, 1].min() - 0.05, points[:, 1].max() + 0.05
    grid_lat = np.linspace(lat_min, lat_max, 150)
    grid_lon = np.linspace(lon_min, lon_max, 150)
    grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)

    # Interpolate differences (using cubic interpolation).
    grid_points = np.column_stack((grid_lat.flatten(), grid_lon.flatten()))
    grid_diff = griddata(points, values, grid_points, method='cubic', fill_value=np.nan)
    grid_diff = grid_diff.reshape(grid_lat.shape)

    # Use the actual minimum and maximum difference.
    vmin = np.nanmin(grid_diff)
    vmax = np.nanmax(grid_diff)
    print(f"Origin {selected_origin}: difference range from {vmin:.1f} to {vmax:.1f}.")

    # Create the base map centered on the selected origin.
    origin_coords = node_coords[selected_origin]
    mymap = folium.Map(location=origin_coords, zoom_start=11, tiles='cartodbpositron')

    # Add the heatmap layer.
    for i in range(len(grid_lat) - 1):
        for j in range(len(grid_lon) - 1):
            cell_value = grid_diff[i, j]
            if np.isfinite(cell_value):
                corners = [
                    [grid_lat[i, j], grid_lon[i, j]],
                    [grid_lat[i+1, j], grid_lon[i+1, j]],
                    [grid_lat[i+1, j+1], grid_lon[i+1, j+1]],
                    [grid_lat[i, j+1], grid_lon[i, j+1]]
                ]
                color = get_color(cell_value, vmin, vmax, cmap=cm.BuPu)
                folium.Polygon(
                    locations=corners,
                    color=None,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.6,
                    weight=0,
                    popup=folium.Popup(f"Difference: {cell_value:.1f} min", parse_html=True)
                ).add_to(mymap)

    # Add store markers.
    for lat, lon in store_locations:
        folium.Marker(
            location=(lat, lon),
            popup="Store",
            icon=folium.Icon(color='blue', icon='shopping-cart', prefix='fa')
        ).add_to(mymap)

    # Add origin marker.
    folium.Marker(
        location=origin_coords,
        popup=f"Origin {selected_origin}",
        icon=folium.Icon(color='green', icon='home', prefix='fa')
    ).add_to(mymap)

    # Add hospital markers.
    for lat, lon in hospital_locations:
        folium.Marker(
            location=(lat, lon),
            popup="Medical Center",
            icon=folium.Icon(color='red', icon='hospital', prefix='fa')
        ).add_to(mymap)

    # Add legend.
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 300px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; padding: 10px;
                border-radius: 5px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);">
        <b>Difference in Travel Time<br>({scenario_name} - {base_scenario_name})</b><br>
        <i style="background:linear-gradient(to right, {neg_color}, {mid_color}, {pos_color});
        width:200px;height:10px;display:inline-block;border-radius:2px;"></i><br>
        <span style="float:left;margin-top:5px;">{vmin:.1f} min</span>
        <span style="float:right;margin-top:5px;">{vmax:.1f} min</span>
        <br clear="all">
    </div>
    '''
    neg_color = colors.to_hex(cm.BuPu(0.0))
    mid_color = colors.to_hex(cm.BuPu(0.5))
    pos_color = colors.to_hex(cm.BuPu(1.0))
    legend_html = legend_html.format(neg_color=neg_color, mid_color=mid_color,
                                     pos_color=pos_color, vmin=vmin, vmax=vmax,
                                     scenario_name=scenario_name, base_scenario_name=base_scenario_name)
    mymap.get_root().html.add_child(folium.Element(legend_html))
    
    return mymap

# -------------------------------
# Main Script
# -------------------------------
print("Loading data for difference map...")

# Parse the travel time datasets and network.
travel_times_data1 = parse_travel_times(travel_times_file1)
travel_times_data2 = parse_travel_times(travel_times_file2)
network_links = parse_network(network_file)

# Load node data.
nodes_data = pd.read_csv(nodes_file)
node_coords = {
    int(row['Node']): (float(row['Latitude']), float(row['Longitude']))
    for _, row in nodes_data.iterrows()
}

# Define store locations (complete list).
store_locations = [
    (44.98192655611847, -93.23511364703194),
    (45.008073594527765, -93.22953935747238),
    (44.97711695003733, -93.27460046767696),
    (44.950213588860464, -93.23717829034591),
    (44.94294423112828, -93.34614823480233),
    (44.89036813374768, -93.24822971283476),
    (44.92161480289106, -93.1879721608547),
    (44.95817468709137, -93.1556913294368),
    (45.012970864054886, -93.16429955114823),
    (45.05631402338738, -93.3649787197961),
    (45.07303418169383, -93.25145779597653),
    (45.06353469167184, -93.1449310522975),
    (44.896911957134684, -93.0764418734434),
    (44.95443272870456, -93.0280933698863),
    (45.01637841070388, -93.00907100783105),
    (45.07057060723914, -93.25110651320225),
    (45.12991502540842, -93.26798862311864),
    (45.16825348091124, -93.23287383449257),
    (45.22304591872331, -93.31475527460026),
    (45.1998938809581, -93.34959052321989),
    (45.143826943155965, -93.47249980944223),
    (45.096521034392616, -93.37719582736963),
    (45.058462353824815, -93.36470771937394),
    (45.0375657199851, -93.44949539997644),
    (45.05242633263801, -93.5290249298439),
    (44.975294975337086, -93.44489451808327),
    (44.943203786205096, -93.39428481725852),
    (44.94366900408017, -93.34564692295942),
    (44.919938085799984, -93.50667778921996),
    (44.863596086873976, -93.4271482591027),
    (44.88222764754178, -93.32329978208568),
    (44.86825454252502, -93.5408557687479),
    (44.79825949198736, -93.20690884177948),
    (44.757499540735516, -93.28743843595562),
    (44.69082988930936, -93.28883895063694),
    (44.7336267064243, -93.21286102917512),
    (44.7284032101487, -93.17539726139647),
    (44.82428990868711, -92.92674691488476),
    (45.02672538226125, -93.18252160568782),
    (45.05777786730312, -93.06766630347329),
    (45.17290158769242, -93.15754344305084),
    (45.18674341206377, -93.23835734166258),
    (45.12762598637742, -93.26554706456),
    (44.906058054854284, -93.07521900335945),
    (44.8257623215255, -93.04047657965721),
    (44.83701046676123, -93.16207506261506),
    (44.86726243523267, -93.26819050892301),
    (44.78450034012022, -93.2866946273589),
    (44.79100956081815, -93.41992174399361),
    (44.8652874186799, -93.4306884939935),
    (45.11310998138177, -93.3876214953332),
    (45.13382857716995, -93.49724658624102),
    (45.104290355028034, -93.38553173019528),
    (44.8678004325985, -93.26480862734577),
    (44.739867749294994, -93.22612664123794),
    (44.83551203705133, -93.15874511705012),
    (44.90404800366286, -93.07888553088304),
    (45.13187706690812, -93.49342432068603),
    (44.995842442880786, -93.25733252594043),
    (44.9379910989954, -93.1483099107759),
    (44.948022845354735, -93.33800926116218),
    (44.98273458520639, -93.42086644868722),
    (44.86849247125795, -93.33037767810067),
    (44.80045702146825, -93.20827234911638),
    (45.06903705444764, -93.14503923232094),
    (45.102136472112115, -93.43285893635533),
    (44.98427684169572, -93.42304690099053),
    (45.06518704042935, -93.14940012366733),
    (44.95419535661196, -92.91827217951848),
    (44.974416350600286, -93.25644181784155),
    (44.96021790676063, -93.23637363108514),
    (44.96773516776212, -93.28595385718924),
    (44.900044357629845, -93.30838300709347),
    (44.873280322373844, -93.28713433876315),
    (44.79626435610884, -93.25644181784155),
    (44.84566686857612, -93.17616907081586),
    (44.89744486967629, -93.07862515985681),
    (44.91533002213331, -93.17121655813693),
    (44.96150757643707, -93.01339031106855),
    (44.96597440116849, -93.14596435860598),
    (45.00244045157757, -93.15332958346919),
    (45.00541624795023, -93.15122523350827),
    (45.03293503650809, -93.19015570778514),
    (44.95704040390892, -93.01233813608809),
    (45.022524077343796, -93.10177300942685),
    (45.03293503650809, -93.18173830794149),
    (45.04334410211205, -93.01759901099035),
    (45.06787226463322, -93.24697315672975),
    (45.0729123653229, -93.37139222869413),
    (45.10362254959269, -93.3522956244836),
    (45.114853857505686, -93.20588832553615),
    (45.13918077643559, -93.26954367290459),
    (45.59110278162324, -93.19934163513751),
    (45.29047182809289, -93.56189043570248),
    (45.23634285711386, -93.32156452696783),
    (45.28950568934966, -92.98922812644996),
    (45.19280896556658, -93.10458456299335),
    (45.17635415570072, -93.23092732682659),
    (45.136649458007604, -93.2625130177849),
    (45.181194299386, -93.3916023634406),
    (45.00264438232122, -92.94889526475221),
    (45.057672685745885, -92.98004037382375),
    (45.03796029273171, -93.01313205221224),
    (44.94841958933283, -92.8951147664414),
    (44.65625224935745, -93.29548490300674),
    (44.442275283092954, -93.18935180912702),
    (44.29526376683391, -93.29340892365985),
    (44.36240027548676, -94.51893287726644),
    (44.181646693666984, -94.02693723565511),
    (44.89037655810113, -94.37983462501296),
    (44.868473428380106, -93.7075264445912),
    (45.33574254606957, -93.7925309404885),
    (45.59228211216919, -94.14285244446307),
    (46.00259220122413, -94.32348025147878),
    (44.36032237478368, -94.50920529806083),
    (44.89979325187998, -94.38835569787251)
]


# Define hospital locations (complete list).
hospital_locations = [
    (45.119093916501605, -93.2583389437839),
    (45.021136646850664, -93.32219697545649),
    (44.9968638768925, -93.3331833034862),
    (44.9788954049053, -93.26177217129319),
    (44.981809593817935, -93.23087312370966),
    (44.96189301745996, -93.17182161055005),
    (44.959949566538775, -93.17250825605193),
    (44.894319494150935, -93.32357026646021),
    (44.93856726154512, -93.35721589605114),
    (44.96547203343599, -93.09414558305882),
    (44.951096173654506, -93.11039818318054),
    (44.92904619327653, -92.9817317655504),
    (45.037775839177314, -93.0304895659155),
    (44.93000506345222, -92.97766861482093),
    (45.11931705141099, -93.25725332115547),
    (45.22713470826386, -93.38470361558772),
    (45.14302176195473, -93.47623609843536),
    (45.01784786207956, -93.45190467893417),
    (45.19366774379878, -93.3615308351099),
    (44.898965892922746, -93.3232957465039),
    (44.93998749568892, -93.36964130743944),
    (44.760918784385524, -93.26999835142807),
    (44.91537805112581, -93.20859048159036),
    (45.02358075483286, -92.98729042543964),
    (45.06205819520439, -92.82276368411857),
    (44.930144986365484, -92.93051711329363),
    (44.97360335992917, -92.71848617201367),
    (44.94900832223515, -92.9629590059485),
    (44.752691272794415, -92.8969165816154),
    (44.9293247007476, -92.97338675715899),
    (45.025758384201204, -93.46212932815537),
    (44.947954939864246, -93.36476815535957),
    (44.933634763979995, -93.46971591304853),
    (44.90140130917966, -93.44063400429135),
    (44.832396833006456, -93.58983684052389),
    (44.78305727639139, -93.50259111425233),
    (44.573066498760625, -93.58332622951951),
    (44.31055742769792, -93.24990183586075),
    (44.135442487018, -93.240766920966),
    (45.313421639532194, -93.78293248960141),
    (45.57391515461066, -93.59130382300917),
    (45.15196316140169, -93.47666881710133),
    (45.197796489494216, -93.36716672190578),
    (44.75360074226516, -92.89664990147688),
    (44.50032184956381, -92.90349378242661),
    (44.48689652528939, -93.21146842516411),
    (44.65631657114679, -93.13960767519202),
    (44.868913347481566, -93.11565409186801)
]

# Define the output folder.
output_folder = '/Users/mobjoon/Downloads/difference_maps'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Define nodes to exclude (if any).
excluded_nodes = {}

# Loop over origins (from 1 to 3061 in steps of 5).
for origin in range(1, 3061, 5):
    if origin not in travel_times_data1 or origin not in travel_times_data2:
        print(f"Origin {origin} not in datasets; skipping.")
        continue
    print(f"Creating difference accessibility map for origin {origin}...")
    diff_map = create_difference_accessibility_map(travel_times_data1, travel_times_data2,
                                                     node_coords, network_links,
                                                     origin, store_locations,
                                                     excluded_nodes, hospital_locations)
    if diff_map is not None:
        output_file = os.path.join(output_folder, f"difference_accessibility_map_origin_{origin}.html")
        diff_map.save(output_file)
        print(f"Map for origin {origin} saved as {output_file}")
