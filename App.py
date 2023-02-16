import main
import time
from folium import vector_layers as vl, features, Map
from flask import Flask
from flask_socketio import SocketIO
from jinja2 import Template

app = Flask(__name__)
socketio = SocketIO(app)
M = Map()

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
                    var circle = L.circle(new_mark.getLatLng(),
                     {radius: 300000, fill: false}).addTo({{this._parent.get_name()}});
                    var socket = io.connect('http://127.0.0.1:5000');
                    socket.emit("message", lat, lng);     
                    var tr = {}   
                    socket.on("message", (planes) => {
                    for (plane in planes) {
                    let p = planes[plane];
                    var new_marker = L.marker(p.slice(0,2), {icon: L.icon({iconUrl: "airplane-icon-png-2503.png",
                    iconSize: [40, 30]})})
                    if (!(plane in tr)) {
                    let path = L.polyline([p.slice(0,2), p.slice(2,4)], {color: 'blue', weight: 1}).addTo({{this._parent.get_name()}});     
                    new_marker.addTo({{this._parent.get_name()}}).bindPopup(plane)
                    tr[plane] = [new_marker, path] }
                    if (plane in tr) { tr[plane][0].setLatLng(p.slice(0,2)),
                                      tr[plane][1].setLatLngs([p.slice(0,2), p.slice(2,4)]) }
                    };
                    });                  
                    };
                {{this._parent.get_name()}}.on('click', newMarker);
            {% endmacro %}
            """)
    Map.default_js.append(('socket', 'https://cdn.socket.io/4.5.4/socket.io.js'))

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
        print(traffic)
        for plane in traffic:
            new_trajectory = point.direct_path(traffic, plane)
            coords.setdefault(plane, traffic[plane][3:5])
            if len(new_trajectory) > 2:
                coords[plane] = tuple(coords[plane]) + new_trajectory[1:3]
            else:
                coords[plane] = tuple(coords[plane]) + new_trajectory
        socketio.send(coords)
        time.sleep(10)
        traffic.clear()
        coords.clear()

if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)

