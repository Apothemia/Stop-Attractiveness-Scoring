document.addEventListener('DOMContentLoaded', () => {
    const map = L.map("map").setView([37.77, -122.42], 10);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors"
    }).addTo(map);

    fetch("/api/stations/")
        .then(res => res.json())
        .then(stations => {
            stations.forEach(s => {
                L.marker([s.lat, s.lon])
                    .addTo(map)
                    .bindPopup(`<b>${s.name}</b><br>${s.code}`);
            });
        })
        .catch(error => console.error('Error loading stations:', error));
});