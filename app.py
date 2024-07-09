from flask import Flask, render_template, request, jsonify
import numpy as np
import pygal
#import plotly.graph_objects as go
#import io
#import base64
#import plotly.io as pio
#import json  # Importez le module json
from pygal.style import Style


app = Flask(__name__)

# Définition des données initiales
sieges = [78, 9, 28, 69, 10, 9, 5, 33, 99, 26, 3, 39, 26, 17, 125, 1]
groupes = ['La France insoumise', 'Parti communiste français', 'Les Ecologistes', 'Parti socialiste',
           'Divers gauche', 'Régionaliste', 'Divers centre', 'Modem', 'Ensemble !', 'Horizons',
           'Union des Démocrates et Indépendants', 'Les Républicains', 'Divers droite',
           'LR-RN', 'Rassemblement National', 'Extrême droite']
n = len(sieges)

def calculate_coalitions(selected_mask, constraints):
    H = np.array([list(map(int, bin(x)[2:].zfill(n))) for x in range(2**n)])

    # Appliquer les contraintes
    if 'no_rn_lfi' in constraints:
        rn_idx = groupes.index('Rassemblement National')
        lfi_idx = groupes.index('La France insoumise')
        H = H[(H[:, rn_idx] == 0) | (H[:, lfi_idx] == 0)]

    if 'no_macron_lfi' in constraints:
        bloc_macroniste_indices = [groupes.index('Ensemble !'), groupes.index('Modem'), groupes.index('Horizons')]
        lfi_idx = groupes.index('La France insoumise')
        for macron_idx in bloc_macroniste_indices:
            H = H[(H[:, macron_idx] == 0) | (H[:, lfi_idx] == 0)]

    if 'no_macron_rn' in constraints:
        bloc_macroniste_indices = [groupes.index('Ensemble !'), groupes.index('Modem'), groupes.index('Horizons')]
        rn_idx = groupes.index('Rassemblement National')
        for macron_idx in bloc_macroniste_indices:
            H = H[(H[:, macron_idx] == 0) | (H[:, rn_idx] == 0)]

    if 'no_lr_lfi' in constraints:
        lr_idx = groupes.index('Les Républicains')
        lfi_idx = groupes.index('La France insoumise')
        H = H[(H[:, lr_idx] == 0) | (H[:, lfi_idx] == 0)]


    somme_sieges = np.sum(H * sieges, axis=1)
    maj_absolue = somme_sieges > 288
    first_ones = np.argmax(H, axis=1)
    last_ones = n - np.argmax(np.flip(H, axis=1), axis=1)
    tchebychev_dist = last_ones - first_ones + 1

    # Create list of tuples for sorting, only include coalitions with absolute majority
    coalition_data = [(H[i], np.count_nonzero(H[i]), somme_sieges[i], tchebychev_dist[i]) for i in range(len(H)) if maj_absolue[i]]

    # Sort by the criteria specified
    sorted_by_partis = sorted(coalition_data, key=lambda x: (x[1], -x[2]))
    sorted_by_distance = sorted(coalition_data, key=lambda x: (x[3], -x[2]))
    sorted_by_distance_and_partis = sorted(coalition_data, key=lambda x: (x[3], x[1]))

    # Récupérer les meilleurs résultats en fonction des indices triés
    top_results = []
    for coalition in [sorted_by_partis[0], sorted_by_distance[0], sorted_by_distance_and_partis[0]]:
        sieges_total = int(np.sum(coalition[0] * sieges))
        partis = [groupes[i] for i in range(n) if coalition[0][i] == 1]
        nombre_partis = int(np.sum(coalition[0] ))
        distance = coalition[3]

        top_results.append({"partis": partis, "total_sieges": int(sieges_total), "coalition": coalition[0].tolist(),"nombre_partis":  len(partis), "distance": int(distance)})

    custom_colors = ['#a10909', '#dd0001', '#02c001', '#ff9999',
                     '#ff9999', '#ac59ba', '#fdb334', '#fdb334', '#f08300',
                     '#c3581f', '#4a90e2', '#16428c', '#16428c',
                     '#503f34', '#4e301b', '#4e301b']

    # Générer les données pour le graphique d'état
    state_space_data = {
        "partis": [],
        "total_sieges": [],
        "nombre_partis": [],
        "distance": [],
        "color": [],
        "coalitions": []
    }

    for coalition in coalition_data:
        partis = [groupes[i] for i in range(n) if coalition[0][i] == 1]
        sieges_total = np.sum(coalition[0] * sieges)
        distance = coalition[3]


        main_party = np.argmax(coalition[0] * sieges)

        # Ajouter la couleur du parti le plus nombreux
        main_party_color = custom_colors[main_party]
        state_space_data["partis"].append(partis)
        state_space_data["nombre_partis"].append(len(partis))
        state_space_data["total_sieges"].append(int(sieges_total))
        state_space_data["distance"].append(int(distance))
        state_space_data["color"].append(main_party_color)
        #state_space_data["coalitions"].append({"partis": partis, "nombre_partis": int(len(partis)), "total_sieges": int(sieges_total), "distance": int(distance), "color": main_party_color})
        state_space_data["coalitions"].append({"partis": partis, "total_sieges": int(sieges_total), "coalition": coalition[0].tolist(),"nombre_partis":  len(partis), "distance": int(distance), "color": main_party_color})



    return top_results, state_space_data

def generate_pie_chart(coalition):
    custom_colors = ['#a10909', '#dd0001', '#02c001', '#ff9999',
                     '#ff9999', '#ac59ba', '#fdb334', '#fdb334', '#f08300',
                     '#c3581f', '#4a90e2', '#16428c', '#16428c',
                     '#503f34', '#4e301b', '#4e301b']
    yourCustomStyle = Style( colors=custom_colors)

    pie_chart = pygal.Pie(half_pie=True, legend_at_bottom=True, show_legend=True,style = yourCustomStyle)
    for i, parti in enumerate(groupes):
        if parti in coalition["partis"]:
            pie_chart.add(parti, [{'value': sieges[i], 'color': custom_colors[i], 'stroke': '#000', 'stroke_width': 1}])
        else:
            pie_chart.add(parti, [{'value': sieges[i], 'color': '#E0E0E0'}])

    chart_uri = pie_chart.render_data_uri()
    return chart_uri



@app.route('/')
def index():
    return render_template('index.html', groupes=groupes)

@app.route('/calculate', methods=['POST'])
def calculate():
    selected_partis = request.form.getlist('selected_partis')
    constraints = request.form.getlist('constraints')
    selected_indices = [groupes.index(parti) for parti in selected_partis]
    selected_mask = np.zeros(n)
    for idx in selected_indices:
        selected_mask[idx] = 1

    top_coalitions, state_space_data = calculate_coalitions(selected_mask, constraints)

    # Préparer les données pour la sérialisation JSON
    top_coalitions_json = []
    for coalition in top_coalitions:
        top_coalitions_json.append({
            "partis": coalition["partis"],
            "nombre_partis": coalition["nombre_partis"],
            "total_sieges": coalition["total_sieges"],
            "distance": coalition["distance"]
        })

    state_space_data_json = {
        "partis": state_space_data["partis"],
        "total_sieges": state_space_data["total_sieges"],
        "nombre_partis": state_space_data["nombre_partis"],
        "distance": state_space_data["distance"],
        "color": state_space_data["color"],
        "coalitions": state_space_data["coalitions"]
    }

    return jsonify({
        "top_coalitions": top_coalitions_json,
        "state_space_data": state_space_data_json
    })


@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    coalition_data = request.json.get('coalition_data')
    if coalition_data:
        coalition = {
            "partis": coalition_data["partis"],
            "total_sieges": coalition_data["total_sieges"],
            "nombre_partis": coalition_data["nombre_partis"],
            "color": coalition_data["color"],
            "coalition": coalition_data["coalition"],
            "distance": coalition_data["distance"]
        }

        chart_uri = generate_pie_chart(coalition)
        return jsonify({"chart_uri": chart_uri})

    return jsonify({"error": "No coalition data received"})


@app.route('/generate_pie_chart', methods=['POST'])
def generate_pie_chart_endpoint():
    coalition = request.json
    print(coalition)
    chart_uri = generate_pie_chart(coalition)
    return jsonify({"chart": chart_uri})

if __name__ == '__main__':
    app.run()

