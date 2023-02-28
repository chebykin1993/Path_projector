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
            let tr = {}
            let new_mark = L.marker()
            let icn = L.icon({iconUrl: "https://www.freeiconspng.com/uploads/plane-icon--iconshow-14.png", iconSize: [30, 30]})
            var socket = io.connect('http://127.0.0.1:5000');
                function newMarker(e){
                    new_mark.setLatLng(e.latlng)
                    if ({{this._parent.get_name()}}.hasLayer(new_mark) == true) {return NaN}
                    else {new_mark.addTo({{this._parent.get_name()}})};
                    new_mark.dragging.enable();
                    new_mark.on('dblclick', function(e){ {{this._parent.get_name()}}.removeLayer(e.target)})
                    var lat = e.latlng.lat.toFixed(4),
                       lng = e.latlng.lng.toFixed(4);
                    new_mark.bindPopup({{ this.popup }});
                    var circle = L.circle(new_mark.getLatLng(),
                     {radius: 300000, fill: false}).addTo({{this._parent.get_name()}});
                    socket.emit("message", lat, lng);     
                    socket.on("message", (planes) => {
                    for (plane in planes) {
                    let p = planes[plane]
                    let new_marker = L.marker(p.slice(0,2), {icon: icn, rotationOrigin: 'center center'})
                    new_marker.setRotationAngle(p[4])
                    let path = L.polyline([p.slice(0,2), p.slice(2,4)], {color: 'blue', weight: 1})
                    new_marker.on('click', () => { if ({{this._parent.get_name()}}.hasLayer(path) == false) { path.addTo({{this._parent.get_name()}}) }
                    else { path.remove() }
                     })
                     
                    if (plane in tr) { tr[plane][0].setLatLng(p.slice(0,2)),
                                      tr[plane][1].setLatLngs([p.slice(0,2), p.slice(2,4)])
                                      }
                    else {
                    tr[plane] = [new_marker, path]     
                    new_marker.addTo({{this._parent.get_name()}}).bindPopup(plane)
            
                }
                    };
                    });                  
                    };
                {{this._parent.get_name()}}.on('click', newMarker);
                
            {% endmacro %}
            """)
    Map.default_js.append(('socket', 'https://cdn.socket.io/4.5.4/socket.io.js'))
    Map.default_js.append(('markerrotate', "https://cdn.jsdelivr.net/npm/leaflet-rotatedmarker@0.2.0/leaflet.rotatedMarker.min.js"))
click = SocketMarker()
M.add_child(click)
coords = {}

@app.route('/')
def home():
    return M._repr_html_()

@socketio.on('message')
def handle_message(lat, lng):
    point = main.Origin(float(lat), float(lng))
    point()
    while True:
        traffic = point.params_calc()
        for plane in traffic:
            new_trajectory = point.direct_path(traffic, plane)
            coords.setdefault(plane, traffic[plane][3:5])

            if len(new_trajectory) > 2:
                coords[plane] = tuple(coords[plane]) + new_trajectory[0:3]
            else:
                coords[plane] = tuple(coords[plane]) + new_trajectory

        socketio.send(coords)
        time.sleep(10)
        traffic.clear()
        coords.clear()

if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)

