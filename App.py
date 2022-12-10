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
                    socket.on("message", (planes) => {        
                    for (let plane in planes) {
                    let moving_marker = L.marker(planes[plane],
                    {icon: L.icon({iconUrl: 
                    'https://img.icons8.com/ios/50/null/prop-plane--v1.png',
                    iconSize: [40, 30]})})
                    moving_marker.addTo({{this._parent.get_name()}}) 
                    moving_marker.bindPopup(plane) } });
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
    circle = vl.Circle((point.latitude, point.longtitude), radius=point.maxrange * 1000)
    circle.add_to(M)
    while True:
        traffic = point.params_calc()
        for plane in traffic:
            coords.setdefault(plane, traffic[plane][2:4])
        socketio.send(coords)
        time.sleep(10)
        traffic.clear()
        coords.clear()

if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)

