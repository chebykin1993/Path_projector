import main
import time
from folium import vector_layers as vl, features, Map
from flask import Flask
from flask_socketio import SocketIO
from jinja2 import Template

class SocketMarker(features.ClickForMarker):
    _template = Template(u"""
            {% macro script(this, kwargs) %}
                function newMarker(e){
                    var new_mark = L.marker().setLatLng(e.latlng).addTo({{this._parent.get_name()}});
                    new_mark.dragging.enable();
                    new_mark.on('dblclick', function(e){ {{this._parent.get_name()}}.removeLayer(e.target)})
                    var lat = e.latlng.lat.toFixed(4),
                       lng = e.latlng.lng.toFixed(4);
                    new_mark.bindPopup({{ this.popup }});
                    var socket = io.connect('http://127.0.0.1:5000');
                    socket.emit("message", lat, lng);
                    socket.on("message", (coords) => { function() {
                    var planes = JSON.parse(coords);};);
                    for (let plane in planes) { L.marker().setLatLng(planes[plane]).addTo({{this._parent.get_name()}});}
                    };
                {{this._parent.get_name()}}.on('click', newMarker);
            {% endmacro %}
            """)
    Map.default_js.append(('socket', 'https://cdn.socket.io/4.5.4/socket.io.js'))

app = Flask(__name__)
socketio = SocketIO(app)
M = Map()
click = SocketMarker()
M.add_child(click)

coords = {}

@app.route('/')
def home():
    return M._repr_html_()

@socketio.on('message')
def handle_message(lat, lng):
    point = main.Origin(float(lat), float(lng))
    while True:
        traffic = point.params_calc()
        for plane in traffic:
            coords.setdefault(plane, traffic[plane][2:4])
        socketio.emit('messages', coords)
        time.sleep(10)
        coords.clear()

if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)

