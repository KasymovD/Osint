from flask import Flask, jsonify

app = Flask(__name__)

map_data = [
    {"name": "Taipei", "lat": 25.0330, "lon": 121.5654, "description": "Capital of Taiwan"},
    {"name": "Kaohsiung", "lat": 22.6273, "lon": 120.3014, "description": "Port city in Taiwan"},
]

@app.route('/api/map_data', methods=['GET'])
def get_map_data():
    return jsonify(map_data)

if __name__ == '__main__':
    app.run(debug=True)
