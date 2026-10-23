// Weather Dashboard Client Controller
// Handles asynchronous weather updates, unit toggles, and SVG icon rendering

(function () {
    "use strict";

    let currentUnits = "metric";
    let currentCity = "Pune";

    const SVG_ICONS = {
        clear: `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2">
                <circle cx="12" cy="12" r="5"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>`,
        "mostly-clear": `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
                <path d="M12 2v2M4.93 4.93l1.41 1.41M2 12h2M19.07 4.93l-1.41 1.41"/>
                <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
            </svg>`,
        "partly-cloudy": `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2">
                <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
            </svg>`,
        overcast: `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2">
                <path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>
                <path d="M8 10a5 5 0 0 1 9.9 1"/>
            </svg>`,
        rain: `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2">
                <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>
                <path d="m8 19-2 3M12 19l-2 3M16 19l-2 3"/>
            </svg>`,
        "rain-showers": `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
                <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>
                <path d="M8 18v3M12 18v3M16 18v3"/>
            </svg>`,
        "heavy-rain": `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
                <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>
                <path d="m9 17-2 4M13 17l-2 4M17 17l-2 4"/>
            </svg>`,
        thunderstorm: `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2">
                <path d="M19 16.9A5 5 0 0 0 18 7h-1.26a8 8 0 1 0-11.62 9"/>
                <path d="m13 13-3 5h4l-2 5"/>
            </svg>`,
        snow: `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#e2e8f0" stroke-width="2">
                <path d="M20 17.58A5 5 0 0 0 18 8h-1.26A8 8 0 1 0 4 16.25"/>
                <path d="M8 16h.01M8 20h.01M12 18h.01M12 22h.01M16 16h.01M16 20h.01"/>
            </svg>`,
        fog: `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2">
                <path d="M4 14h16M4 18h16M4 10h16M4 6h16"/>
            </svg>`,
        drizzle: `
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2">
                <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>
                <path d="M8 19v1M12 19v1M16 19v1"/>
            </svg>`
    };

    function getIconSvg(iconKey, isSmall) {
        let svgStr = SVG_ICONS[iconKey] || SVG_ICONS["partly-cloudy"];
        if (isSmall) {
            svgStr = svgStr.replace('width="64" height="64"', 'width="30" height="30"');
        }
        return svgStr;
    }

    function getUvBadgeInfo(uvIndex) {
        if (uvIndex <= 2) return { text: "Low", bg: "#064e3b", color: "#6ee7b7", border: "#059669" };
        if (uvIndex <= 5) return { text: "Moderate", bg: "#78350f", color: "#fde68a", border: "#d97706" };
        if (uvIndex <= 7) return { text: "High", bg: "#854d0e", color: "#fef08a", border: "#ca8a04" };
        if (uvIndex <= 10) return { text: "Very High", bg: "#7f1d1d", color: "#fecaca", border: "#dc2626" };
        return { text: "Extreme", bg: "#581c87", color: "#e9d5ff", border: "#9333ea" };
    }

    // Elements
    const searchForm = document.getElementById("searchForm");
    const cityInput = document.getElementById("cityInput");
    const loadingIndicator = document.getElementById("loadingIndicator");
    const errorAlert = document.getElementById("errorAlert");
    const errorMessage = document.getElementById("errorMessage");
    const weatherContent = document.getElementById("weatherContent");
    const unitButtons = document.querySelectorAll(".unit-btn");
    const cityChips = document.querySelectorAll(".city-chip");

    // Weather display elements
    const cityNameEl = document.getElementById("cityName");
    const countryNameEl = document.getElementById("countryName");
    const currentTempEl = document.getElementById("currentTemp");
    const tempUnitEl = document.getElementById("tempUnit");
    const conditionTextEl = document.getElementById("conditionText");
    const feelsLikeEl = document.getElementById("feelsLike");
    const feelsLikeUnitEl = document.getElementById("feelsLikeUnit");
    const iconWrapperEl = document.getElementById("iconWrapper");
    const humidityValEl = document.getElementById("humidityVal");
    const humidityBarEl = document.getElementById("humidityBar");
    const windValEl = document.getElementById("windVal");
    const windUnitEl = document.getElementById("windUnit");
    const pressureValEl = document.getElementById("pressureVal");
    const uvValEl = document.getElementById("uvVal");
    const uvBadgeEl = document.getElementById("uvBadge");
    const forecastCardsEl = document.getElementById("forecastCards");
    const sourceTagEl = document.getElementById("sourceTag");

    function renderWeatherUI(data) {
        cityNameEl.textContent = data.city;
        countryNameEl.textContent = data.country || "Global Region";
        currentTempEl.textContent = data.temp;
        tempUnitEl.textContent = data.temp_unit;
        conditionTextEl.textContent = data.condition;
        feelsLikeEl.textContent = data.feels_like;
        feelsLikeUnitEl.textContent = data.temp_unit;
        
        // Large icon
        iconWrapperEl.innerHTML = getIconSvg(data.icon, false);

        // Metrics
        humidityValEl.textContent = data.humidity;
        humidityBarEl.style.width = Math.min(Math.max(data.humidity, 0), 100) + "%";
        windValEl.textContent = data.wind;
        windUnitEl.textContent = data.wind_unit;
        pressureValEl.textContent = data.pressure;
        uvValEl.textContent = data.uv_index;

        const uvMeta = getUvBadgeInfo(data.uv_index);
        uvBadgeEl.textContent = uvMeta.text;
        uvBadgeEl.style.backgroundColor = uvMeta.bg;
        uvBadgeEl.style.color = uvMeta.color;
        uvBadgeEl.style.borderColor = uvMeta.border;

        if (sourceTagEl) {
            sourceTagEl.textContent = data.source === "live-api" ? "Live Feed" : "Telemetry Cached";
        }

        // Render 5-Day Forecast
        if (forecastCardsEl && data.forecast) {
            forecastCardsEl.innerHTML = data.forecast.map(day => `
                <div class="forecast-day-card">
                    <span class="f-day">${day.day}</span>
                    <div class="f-icon">
                        ${getIconSvg(day.icon, true)}
                    </div>
                    <span class="f-cond">${day.condition}</span>
                    <div class="f-temps">
                        <span class="f-high">${day.high}${data.temp_unit}</span>
                        <span class="f-low">${day.low}${data.temp_unit}</span>
                    </div>
                </div>
            `).join("");
        }

        currentCity = data.city;
    }

    async function fetchWeather(city, units) {
        loadingIndicator.classList.remove("hidden");
        errorAlert.classList.add("hidden");

        try {
            const url = `/api/weather?city=${encodeURIComponent(city)}&units=${encodeURIComponent(units)}`;
            const response = await fetch(url);
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || "Failed to load weather data.");
            }
            const data = await response.json();
            renderWeatherUI(data);
        } catch (err) {
            errorMessage.textContent = err.message || "Could not retrieve weather data.";
            errorAlert.classList.remove("hidden");
        } finally {
            loadingIndicator.classList.add("hidden");
        }
    }

    // Initialize with initial data if passed from Flask
    if (window.INITIAL_WEATHER) {
        renderWeatherUI(window.INITIAL_WEATHER);
    }

    // Search submit listener
    if (searchForm) {
        searchForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const query = cityInput.value.trim();
            if (query) {
                fetchWeather(query, currentUnits);
            }
        });
    }

    // Quick City chips listener
    cityChips.forEach(chip => {
        chip.addEventListener("click", function () {
            const city = this.getAttribute("data-city");
            cityInput.value = city;
            fetchWeather(city, currentUnits);
        });
    });

    // Unit toggle buttons
    unitButtons.forEach(btn => {
        btn.addEventListener("click", function () {
            const chosenUnit = this.getAttribute("data-unit");
            if (chosenUnit === currentUnits) return;

            currentUnits = chosenUnit;
            unitButtons.forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            fetchWeather(currentCity, currentUnits);
        });
    });
})();
