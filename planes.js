
import { Server } from "socket.io"
import "./airplane-icon-png-2503.png"


var M = L.map(
    "M",
    {
        center: [0, 0],
        crs: L.CRS.EPSG3857,
        zoom: 1,
        zoomControl: true,
        preferCanvas: false,
    }
    );

var tile_layer = L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                {"attribution": "Data by \u0026copy; \u003ca href=\"http://openstreetmap.org\"\u003eOpenStreetMap\u003c/a\u003e, under \u003ca href=\"http://www.openstreetmap.org/copyright\"\u003eODbL\u003c/a\u003e.", "detectRetina": false, "maxNativeZoom": 18, "maxZoom": 18, "minZoom": 0, "noWrap": false, "opacity": 1, "subdomains": "abc", "tms": false}
            ).addTo(M);

var socket = new Server(5000);
var tr = {}


function newMarker(e){
    var new_mark = L.marker().setLatLng(e.latlng).addTo(M);
    new_mark.dragging.enable();
    new_mark.on('dblclick', function(e){ M.removeLayer(e.target)})
    var lat = e.latlng.lat.toFixed(4),
        lng = e.latlng.lng.toFixed(4);
    new_mark.bindPopup("Latitude: " + lat + "<br>Longitude: " + lng );
    L.circle(new_mark.getLatLng(),
        {radius: 300000, fill: false}).addTo(M);
    socket.emit("message", lat, lng);
    socket.on("message", (planes) => {
        for (let plane in planes) {
            let p = planes[plane]
            let new_marker = L.marker(p.slice(0,2), {icon: L.icon({iconUrl: "airplane-icon-png-2503.png",
                    iconSize: [40, 30]})})
            if (!(plane in tr)) {
                let path = L.polyline([p.slice(0,2), p.slice(2,4)], {color: 'blue', weight: 1}).addTo(M);
                new_marker.addTo(M).bindPopup(plane)
                tr[plane] = [new_marker, path] }
            if (plane in tr) { tr[plane][0].setLatLng(p.slice(0,2)),
                tr[plane][1].setLatLngs([p.slice(0,2), p.slice(2,4)]) }
        }
    });
}
M.on('click', newMarker);