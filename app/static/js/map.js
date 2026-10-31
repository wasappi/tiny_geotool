document.addEventListener("DOMContentLoaded", () => {
    const mapEl = document.getElementById("map");

    const map = new mapboxgl.Map({
        accessToken: mapEl.dataset.token,
        container: mapEl,
        style: "mapbox://styles/mapbox/satellite-streets-v12",
        center: [4.62810, 50.65666],
        zoom: 13,
        minZoom: 10,
    });

    function updateBbox() {
        const b = map.getBounds();
        document.getElementById("bbox").value =
            [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].map(v => v.toFixed(5)).join(",");
    }

    const interactions = ["dragPan", "scrollZoom", "boxZoom", "doubleClickZoom",
        "keyboard", "touchZoomRotate", "dragRotate"];

    function setMapLocked(locked) {
        interactions.forEach(name => locked ? map[name].disable() : map[name].enable());
        mapEl.classList.toggle("map-locked", locked);
    }

    map.on("load", updateBbox);
    map.on("moveend", updateBbox);

    document.body.addEventListener("htmx:beforeRequest", () => setMapLocked(true));
    document.body.addEventListener("htmx:afterRequest", () => setMapLocked(false));
});