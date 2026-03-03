let forecastChart = null;

document.getElementById('run-demo-btn').addEventListener('click', async () => {
    const sku = document.getElementById('sku-select').value;
    const forceShortage = document.getElementById('fail-safe-toggle').checked;

    // Defensive check in case browser is caching old HTML
    const scenarioDropdown = document.getElementById('scenario-select');
    const scenario = scenarioDropdown ? scenarioDropdown.value : 'normal';

    const fcSpinner = document.getElementById('forecast-spinner');
    const rtContent = document.getElementById('routing-content');
    const rtSpinner = document.getElementById('routing-spinner');

    // Reset UI
    if (forecastChart) {
        forecastChart.destroy();
    }
    const canvas = document.getElementById('forecastChart');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    fcSpinner.style.display = 'block';
    rtContent.style.display = 'none';
    rtContent.innerText = '';

    // 1. Generate Historical Target Data
    const history = [];
    const baseDate = new Date();
    baseDate.setDate(baseDate.getDate() - 30);

    for (let i = 0; i < 30; i++) {
        const d = new Date(baseDate);
        d.setDate(d.getDate() + i);
        history.push({
            date: d.toISOString().split('T')[0],
            demand_qty: Math.floor(Math.random() * 20) + 10
        });
    }

    try {
        // CALL FORECAST ENDPOINT
        const baseUrl = window.location.origin.includes('8000') ? window.location.origin : 'http://localhost:8000';

        const forecastRes = await fetch(`${baseUrl}/forecast/${sku}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sku: sku,
                historical_demand: history,
                periods: 14
            })
        });

        let forecastData = await forecastRes.json();

        // Handle Prophet missing locally fallback
        if (!forecastRes.ok || forecastData.detail) {
            console.warn("Forecast failed. Generating synthetic forecast for demo continuity.");
            forecastData = [];
            const fd = new Date();
            for (let i = 0; i < 14; i++) {
                const d = new Date(fd);
                d.setDate(d.getDate() + i);
                let qty = parseFloat((15 + Math.random() * 5).toFixed(2));
                forecastData.push({
                    sku: sku,
                    date: d.toISOString().split('T')[0],
                    forecast_qty: qty
                });
            }
        }

        // Apply Scenario Adjustments
        if (scenario === 'high_demand') {
            // Spike the forecast 300% to force a massive shortage
            forecastData.forEach(f => f.forecast_qty = f.forecast_qty * 3);
        }

        // Render Graph
        fcSpinner.style.display = 'none';

        const labels = history.map(h => h.date).concat(forecastData.map(f => f.date));
        const currentData = history.map(h => h.demand_qty).concat(Array(forecastData.length).fill(null));

        // Pad the forecast array so it starts exactly where history leaves off visually
        const futureDataPadding = Array(history.length - 1).fill(null);
        // We add the very last historical point to connect the lines
        futureDataPadding.push(history[history.length - 1].demand_qty);
        const futureData = futureDataPadding.concat(forecastData.map(f => f.forecast_qty));

        forecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Historical Demand',
                        data: currentData,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Forecasted Demand',
                        data: futureData,
                        borderColor: '#ec4899',
                        backgroundColor: 'rgba(236, 72, 153, 0.1)',
                        borderDash: [5, 5],
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f8fafc' } }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: '#cbd5e1' }
                    },
                    x: {
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: '#cbd5e1', maxTicksLimit: 10 }
                    }
                }
            }
        });

        // 2. TRIGGER REPLENISHMENT ENDPOINT WITH FAIL-SAFE
        rtSpinner.style.display = 'block';

        let inventoryData = [
            { sku: sku, site: 'DC1', on_hand_qty: forceShortage ? 5 : 500 }, // DC1 stock
            { sku: sku, site: 'DC2', on_hand_qty: 800 }
        ];

        let networkData = [
            { source_site: 'DC2', target_site: 'DC1', transit_time_days: 1, cost: 50 },
            { source_site: 'VENDOR_A', target_site: 'DC1', transit_time_days: 3, cost: 15 }
        ];

        if (scenario === 'logistic_issue') {
            // DC2 goes completely offline, forcing the router to find an external vendor with a longer wait time
            networkData = networkData.filter(n => n.source_site !== 'DC2');
        }

        const forecastForReplenish = forecastData.map(f => ({
            sku: sku,
            site: 'DC1',
            date: f.date,
            forecast_qty: f.forecast_qty
        }));

        const replenishRes = await fetch(`${baseUrl}/replenish`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                forecast_data: forecastForReplenish,
                inventory_data: inventoryData,
                network_data: networkData
            })
        });

        const routingDirectives = await replenishRes.json();

        rtSpinner.style.display = 'none';
        rtContent.style.display = 'block';

        if (routingDirectives.length === 0) {
            rtContent.innerText = `✅ Stock levels nominal.\nNo replenishment required for DC1.\n(Current Stock covers dynamic reorder point).`;
            rtContent.style.color = '#a7f3d0';
        } else {
            let msg = `⚠️ Shortage Detected at DC1\n\nFail-Safe Logistics Evaluation:\n`;
            if (scenario === 'logistic_issue') {
                msg += `- Primary DC2 Offline/Unreachable.\n- Evaluating secondary Tier 2 networks...\n\n`;
            } else if (scenario === 'high_demand') {
                msg += `- Unprecedented Demand Spike Detected.\n- Depleting stock faster than standard lead time.\n\n`;
            }
            msg += `Action Taken: Target Source Overridden.\n\n` + JSON.stringify(routingDirectives, null, 2);
            rtContent.innerText = msg;
            rtContent.style.color = '#fecdd3';
        }

    } catch (err) {
        fcSpinner.style.display = 'none';
        rtSpinner.style.display = 'none';
        rtContent.style.display = 'block';
        rtContent.innerText = `Error connecting to FastAPI backend: ${err.message}\nMake sure uvicorn is running.`;
        rtContent.style.color = '#fca5a5';
    }
});
