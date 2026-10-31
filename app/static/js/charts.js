const NDVI_CLASSES = {
    labels: ["Water", "Built / bare", "Sparse vegetation", "Dense vegetation"],
    colors: ["#3b82f6", "#a8a29e", "#86efac", "#15803d"],
};

function findAll(root, selector) {
    const found = [...root.querySelectorAll(selector)];
    if (root.matches?.(selector)) found.unshift(root);
    return found;
}

htmx.onLoad((content) => {
    findAll(content, "canvas[data-ndvi-chart]").forEach((canvas) => {
        const values = JSON.parse(canvas.dataset.ndviChart);

        new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: NDVI_CLASSES.labels,
                datasets: [{
                    data: values,
                    backgroundColor: NDVI_CLASSES.colors,
                    borderWidth: 0,
                }],
            },
            options: {
                cutout: "65%",
                plugins: {
                    legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } },
                    tooltip: {
                        callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed.toFixed(1)} %` },
                    },
                },
            },
        });
    });
});