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

    const btn = document.getElementById("analyse-btn");
    const monthInput = document.getElementById("datetime_month");
    const spinner = document.getElementById("analyse-spinner");

    // Lock map + form controls for the whole analysis (POST + polling), not just the POST
    function setBusy(busy) {
        interactions.forEach(name => busy ? map[name].disable() : map[name].enable());
        btn.disabled = busy;
        monthInput.disabled = busy;
        spinner.classList.toggle("htmx-request", busy);  // .htmx-indicator shows when it has this class
    }

    map.on("load", updateBbox);
    map.on("moveend", updateBbox);

    const form = document.getElementById("analysis-form");

    // Lock only when the analysis form is submitted, not on every polling request
    form.addEventListener("htmx:beforeRequest", () => setBusy(true));

    // If the POST itself fails (e.g. 422 on a bad bbox), nothing gets swapped, so unlock here
    form.addEventListener("htmx:afterRequest", (e) => {
        if (!e.detail.successful) setBusy(false);
    });

    // Unlock once the final card (result or error) is inserted in the response area
    document.body.addEventListener("htmx:load", (e) => {
        const el = e.detail.elt;
        const inResponse = el.closest("#raster-analysis-response");
        if (inResponse && el.id !== "analysis-processing") setBusy(false);
    });

});