document.addEventListener('DOMContentLoaded', () => {
    // --- Register Service Worker for PWA ---
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
        .then(() => console.log('Service Worker Registered'))
        .catch(err => console.error('Service Worker Failed', err));
    }

    // --- Elements ---
    const datePicker = document.getElementById('current-date');
    const mealsList = document.getElementById('meals-list');
    
    const elCalories = document.getElementById('total-calories');
    const elGoalCalories = document.getElementById('goal-calories');
    const elProtein = document.getElementById('total-protein');
    const elCarbs = document.getElementById('total-carbs');
    const elFat = document.getElementById('total-fat');
    
    // UI controls
    const searchInput = document.getElementById('food-search');
    const searchResults = document.getElementById('search-results');
    const selectedFoodId = document.getElementById('selected-food-id');
    const selectedFoodDisplay = document.getElementById('selected-food-display');
    const selectedFoodName = document.getElementById('selected-food-name');
    const btnClearSelection = document.getElementById('clear-selection');
    const submitBtn = document.getElementById('submit-log');
    const logForm = document.getElementById('log-meal-form');
    const btnExportPdf = document.getElementById('btn-export-pdf');

    // Advanced Actions
    const btnVoiceLog = document.getElementById('btn-voice-log');
    const btnScanBarcode = document.getElementById('btn-scan-barcode');
    const scannerContainer = document.getElementById('scanner-container');
    const btnCloseScanner = document.getElementById('btn-close-scanner');

    // Water Tracker
    const elWaterCount = document.getElementById('water-count');
    const btnWaterPlus = document.getElementById('btn-water-plus');
    const btnWaterMinus = document.getElementById('btn-water-minus');
    let currentWater = 0;

    // Profile & BMI
    const profileForm = document.getElementById('profile-form');
    const elHeight = document.getElementById('height');
    const elWeight = document.getElementById('weight');
    const elCalGoalInput = document.getElementById('calorie-goal-input');
    const elBmiValue = document.getElementById('bmi-value');
    const elBmiCategory = document.getElementById('bmi-category');

    // Circular Progress
    const circle = document.getElementById('calorie-ring');
    const radius = circle.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference;
    
    let currentGoal = 2000;
    let proGoal = 150;
    let carbsGoal = 200;
    let fatGoal = 65;
    
    let chartInstance = null;
    let radarInstance = null;
    let hasCelebrated = false;

    // --- State ---
    let currentDate = new Date().toISOString().split('T')[0];
    datePicker.value = currentDate;
    
    // --- Initialization ---
    initProfile();
    loadLogs(currentDate);
    loadWater(currentDate);
    loadWeeklyChart();
    loadInsights(currentDate);

    // --- Event Listeners ---
    datePicker.addEventListener('change', (e) => {
        currentDate = e.target.value;
        hasCelebrated = false;
        loadLogs(currentDate);
        loadWater(currentDate);
        loadInsights(currentDate);
    });

    btnWaterPlus.addEventListener('click', () => updateWater(1));
    btnWaterMinus.addEventListener('click', () => updateWater(-1));

    profileForm.addEventListener('submit', (e) => {
        e.preventDefault();
        saveProfile();
    });

    btnExportPdf.addEventListener('click', exportDoctorReport);

    // Search functionality with debounce
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(searchTimeout);
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        searchTimeout = setTimeout(() => {
            fetch(`/api/foods/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => displaySearchResults(data))
                .catch(err => console.error('Search error:', err));
        }, 300);
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });

    btnClearSelection.addEventListener('click', clearFoodSelection);

    logForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const foodId = selectedFoodId.value;
        const mealType = document.getElementById('meal-type').value;
        const servings = document.getElementById('servings').value;
        if (!foodId) return;

        const data = {
            date: currentDate,
            food_id: parseInt(foodId),
            servings: parseFloat(servings),
            meal_type: mealType
        };

        submitLog(data);
    });

    // --- Voice Logging Logic ---
    let speechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if(speechRec) {
        const recognition = new speechRec();
        recognition.continuous = false;
        recognition.lang = 'en-US';

        btnVoiceLog.addEventListener('click', () => {
            btnVoiceLog.classList.add('active');
            btnVoiceLog.textContent = 'Listening...';
            recognition.start();
        });

        recognition.onresult = (event) => {
            let text = event.results[0][0].transcript.toLowerCase().trim();
            btnVoiceLog.classList.remove('active');
            btnVoiceLog.textContent = '🎤 Voice Log';
            
            // Basic NLP: remove filler words
            text = text.replace(/^(i ate|i had|logged|log)\s+/i, '');
            
            let servings = 1;
            let mealType = 'Snack';
            
            // Extract meal type
            const mealMatch = text.match(/\b(?:for\s+)?(breakfast|lunch|dinner|snack)\b/i);
            if (mealMatch) {
                mealType = mealMatch[1].charAt(0).toUpperCase() + mealMatch[1].slice(1);
                text = text.replace(mealMatch[0], '').trim();
            }
            
            // Extract servings
            const numMatch = text.match(/^([\d\.]+)\s+/);
            if (numMatch) {
                servings = parseFloat(numMatch[1]);
                text = text.replace(numMatch[0], '').trim();
            } else if (text.match(/^(a|an|one)\s+/i)) {
                servings = 1;
                text = text.replace(/^(a|an|one)\s+/i, '').trim();
            }
            
            const foodQuery = text;
            if (!foodQuery) {
                alert("Could not understand the food name.");
                return;
            }
            
            document.getElementById('servings').value = servings;
            document.getElementById('meal-type').value = mealType;
            
            fetch(`/api/foods/search?q=${encodeURIComponent(foodQuery)}`)
            .then(res => res.json())
            .then(data => {
                if(data.length > 0) {
                    selectFood(data[0]);
                    // Auto-submit the log!
                    const formData = {
                        date: currentDate,
                        food_id: parseInt(data[0].id),
                        servings: parseFloat(servings),
                        meal_type: mealType
                    };
                    submitLog(formData);
                    alert(`Voice Logged: ${servings}x ${data[0].name} for ${mealType}`);
                } else {
                    alert(`Could not find a match for "${foodQuery}". Try typing it manually.`);
                }
            }).catch(() => alert("Error searching for food."));
        };

        recognition.onerror = () => {
            btnVoiceLog.classList.remove('active');
            btnVoiceLog.textContent = '🎤 Voice Log';
        };
    } else {
        btnVoiceLog.addEventListener('click', () => alert("Web Speech API not supported in this browser."));
    }

    // --- Barcode Scanning Logic ---
    btnScanBarcode.addEventListener('click', () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Camera API is not supported in your browser or requires HTTPS.");
            return;
        }
        scannerContainer.style.display = 'block';
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.querySelector('#interactive'),
                constraints: { 
                    width: { min: 640 }, 
                    height: { min: 480 }, 
                    facingMode: "environment",
                    aspectRatio: { min: 1, max: 2 }
                }
            },
            locator: {
                patchSize: "medium",
                halfSample: true
            },
            numOfWorkers: navigator.hardwareConcurrency ? Math.min(navigator.hardwareConcurrency, 4) : 2,
            decoder: { readers: ["ean_reader", "upc_reader", "ean_8_reader", "upc_e_reader"] },
            locate: true
        }, function(err) {
            if (err) {
                console.error("Quagga initialization error:", err);
                scannerContainer.style.display = 'none';
                alert("Camera not accessible: " + err.message);
                return;
            }
            Quagga.start();
        });
    });

    btnCloseScanner.addEventListener('click', () => {
        Quagga.stop();
        scannerContainer.style.display = 'none';
    });

    let lastScanTime = 0;
    Quagga.onDetected((result) => {
        if (Date.now() - lastScanTime < 3000) return; // Debounce scans
        lastScanTime = Date.now();
        
        const code = result.codeResult.code;
        Quagga.stop();
        scannerContainer.style.display = 'none';
        
        // Use OpenFoodFacts API
        fetch(`https://world.openfoodfacts.org/api/v0/product/${code}.json`)
        .then(res => res.json())
        .then(data => {
            if(data.status === 1 && data.product.product_name) {
                const name = data.product.product_name;
                
                // Auto-search our DB for this name
                fetch(`/api/foods/search?q=${encodeURIComponent(name)}`)
                .then(r => r.json())
                .then(foods => {
                    if (foods.length > 0) {
                        selectFood(foods[0]);
                        const formData = {
                            date: currentDate,
                            food_id: parseInt(foods[0].id),
                            servings: 1,
                            meal_type: document.getElementById('meal-type').value || 'Snack'
                        };
                        submitLog(formData);
                        alert(`Scanned & Automatically Logged: ${foods[0].name}`);
                    } else {
                        searchInput.value = name;
                        searchInput.dispatchEvent(new Event('input'));
                        alert(`Scanned: ${name}. We couldn't find a direct match in the database, please select the closest option.`);
                    }
                });
            } else {
                alert("Product not found in OpenFoodFacts database.");
            }
        }).catch(() => alert("Error looking up barcode."));
    });


    // --- Functions ---
    function submitLog(data) {
        fetch('/api/logs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                clearFoodSelection();
                document.getElementById('servings').value = 1;
                loadLogs(currentDate);
                loadWeeklyChart();
                loadInsights(currentDate);
                updateStreakUI();
            }
        });
    }

    function initProfile() {
        fetch('/api/profile')
            .then(res => res.json())
            .then(data => {
                if(data.id) {
                    elHeight.value = data.height_cm;
                    elWeight.value = data.weight_kg;
                    elCalGoalInput.value = data.calorie_goal;
                    currentGoal = data.calorie_goal;
                    proGoal = data.protein_goal || 150;
                    carbsGoal = data.carbs_goal || 200;
                    fatGoal = data.fat_goal || 65;
                    elGoalCalories.textContent = currentGoal;
                    calculateBMI(data.height_cm, data.weight_kg);
                    document.getElementById('streak-count').textContent = data.streak_count || 0;
                }
            });
    }

    function saveProfile() {
        const h = parseFloat(elHeight.value);
        const w = parseFloat(elWeight.value);
        const g = parseInt(elCalGoalInput.value);
        
        fetch('/api/profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({height_cm: h, weight_kg: w, calorie_goal: g})
        }).then(() => {
            currentGoal = g;
            elGoalCalories.textContent = currentGoal;
            calculateBMI(h, w);
            loadLogs(currentDate);
            loadInsights(currentDate);
        });
    }

    function calculateBMI(h, w) {
        if(!h || !w) return;
        const hm = h / 100;
        const bmi = (w / (hm * hm)).toFixed(1);
        elBmiValue.textContent = bmi;
        
        elBmiCategory.className = '';
        if(bmi < 18.5) {
            elBmiCategory.textContent = 'Underweight';
            elBmiCategory.classList.add('bmi-warning');
        } else if(bmi < 25) {
            elBmiCategory.textContent = 'Normal';
            elBmiCategory.classList.add('bmi-normal');
        } else if(bmi < 30) {
            elBmiCategory.textContent = 'Overweight';
            elBmiCategory.classList.add('bmi-warning');
        } else {
            elBmiCategory.textContent = 'Obese';
            elBmiCategory.classList.add('bmi-danger');
        }
    }

    function updateStreakUI() {
        fetch('/api/profile')
            .then(res => res.json())
            .then(data => {
                if(data.streak_count) {
                    document.getElementById('streak-count').textContent = data.streak_count;
                }
            });
    }

    function loadWater(date) {
        fetch(`/api/water?date=${date}`)
            .then(res => res.json())
            .then(data => {
                currentWater = data.glasses;
                elWaterCount.textContent = currentWater;
            });
    }

    function updateWater(change) {
        currentWater += change;
        if(currentWater < 0) currentWater = 0;
        elWaterCount.textContent = currentWater;
        
        fetch('/api/water', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({date: currentDate, glasses: currentWater})
        }).then(() => loadInsights(currentDate));
    }

    function displaySearchResults(foods) {
        searchResults.innerHTML = '';
        if (foods.length === 0) {
            searchResults.innerHTML = '<div class="search-item"><div class="search-item-title">No results found</div></div>';
            searchResults.style.display = 'block';
            return;
        }
        foods.forEach(food => {
            const div = document.createElement('div');
            div.className = 'search-item';
            div.innerHTML = `<div class="search-item-title">${food.name}</div><div class="search-item-meta">${food.calories} kcal | P: ${food.protein}g</div>`;
            div.addEventListener('click', () => selectFood(food));
            searchResults.appendChild(div);
        });
        searchResults.style.display = 'block';
    }

    function selectFood(food) {
        selectedFoodId.value = food.id;
        selectedFoodName.textContent = food.name;
        searchInput.style.display = 'none';
        searchResults.style.display = 'none';
        selectedFoodDisplay.style.display = 'flex';
        submitBtn.disabled = false;
    }

    function clearFoodSelection() {
        selectedFoodId.value = '';
        searchInput.value = '';
        searchInput.style.display = 'block';
        selectedFoodDisplay.style.display = 'none';
        submitBtn.disabled = true;
        searchInput.focus();
    }

    function loadLogs(date) {
        fetch(`/api/logs?date=${date}`)
            .then(res => res.json())
            .then(data => {
                updateTotals(data.totals);
                renderLogs(data.logs);
                loadSuggestions(date);
                updateRadarChart(data.totals);
            });
    }

    function updateTotals(totals) {
        elCalories.textContent = totals.calories;
        elProtein.textContent = totals.protein;
        elCarbs.textContent = totals.carbs;
        elFat.textContent = totals.fat;
        
        const percent = Math.min(100, Math.round((totals.calories / currentGoal) * 100));
        document.getElementById('cals-percent').textContent = percent + '%';
        
        const offset = circumference - (percent / 100) * circumference;
        circle.style.strokeDashoffset = offset;

        if(percent >= 100) circle.style.stroke = '#ef4444'; 
        else circle.style.stroke = '#3b82f6';

        if(percent >= 100 && percent <= 110 && !hasCelebrated && currentDate === new Date().toISOString().split('T')[0]) {
            confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
            hasCelebrated = true;
        }
    }

    function loadSuggestions(date) {
        fetch(`/api/suggestions?date=${date}`)
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById('suggestions-list');
                list.innerHTML = '';
                if(data.length === 0) {
                    list.innerHTML = '<div class="empty-state" style="padding:1rem 0">Daily goal met! Great job! 🎉</div>';
                    return;
                }
                data.forEach(food => {
                    list.innerHTML += `
                        <div class="suggestion-item">
                            <div class="suggestion-name">${food.name}</div>
                            <div class="suggestion-meta">${food.calories} kcal | ${food.protein}g Protein</div>
                        </div>
                    `;
                });
            });
    }

    function renderLogs(logs) {
        mealsList.innerHTML = '';
        if (logs.length === 0) {
            mealsList.innerHTML = '<div class="empty-state">No meals logged for today.</div>';
            return;
        }
        logs.forEach(log => {
            const el = document.createElement('div');
            el.className = 'meal-item';
            el.innerHTML = `
                <div class="meal-info-main">
                    <div class="meal-name">${log.name} <span style="font-weight:400; font-size:0.9rem; color:var(--text-secondary)">(${log.servings} serving${log.servings > 1 ? 's' : ''})</span></div>
                    <div class="meal-meta">${log.meal_type}</div>
                </div>
                <div class="meal-stats">
                    <div class="stat"><span style="color:var(--color-calories)">${log.total_calories}</span> kcal</div>
                    <div class="stat"><span style="color:var(--color-protein)">${log.total_protein}</span> P</div>
                    <div class="stat"><span style="color:var(--color-carbs)">${log.total_carbs}</span> C</div>
                    <div class="stat"><span style="color:var(--color-fat)">${log.total_fat}</span> F</div>
                    <button class="btn-delete" data-html2canvas-ignore data-id="${log.id}">🗑</button>
                </div>
            `;
            mealsList.appendChild(el);
        });

        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', function() {
                deleteLog(this.getAttribute('data-id'));
            });
        });
    }

    function deleteLog(logId) {
        if (!confirm('Are you sure you want to delete this meal?')) return;
        fetch(`/api/logs/${logId}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(result => {
            if (result.success) {
                hasCelebrated = false;
                loadLogs(currentDate);
                loadWeeklyChart();
                loadInsights(currentDate);
            }
        });
    }

    function loadWeeklyChart() {
        fetch('/api/charts/weekly')
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById('weeklyChart').getContext('2d');
                if(chartInstance) chartInstance.destroy();
                chartInstance = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Calories',
                            data: data.calories,
                            backgroundColor: 'rgba(244, 63, 94, 0.5)',
                            borderColor: 'rgba(244, 63, 94, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#94a3b8'} },
                            x: { grid: { display: false }, ticks: { color: '#94a3b8'} }
                        }
                    }
                });
            });
    }

    function updateRadarChart(totals) {
        const ctx = document.getElementById('radarChart').getContext('2d');
        if(radarInstance) radarInstance.destroy();
        
        // Calculate percentages of goals to normalize the radar chart
        const cPer = Math.min(100, (totals.calories / currentGoal) * 100) || 0;
        const pPer = Math.min(100, (totals.protein / proGoal) * 100) || 0;
        const caPer = Math.min(100, (totals.carbs / carbsGoal) * 100) || 0;
        const fPer = Math.min(100, (totals.fat / fatGoal) * 100) || 0;

        radarInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Calories', 'Protein', 'Carbs', 'Fat'],
                datasets: [{
                    label: '% of Daily Goal',
                    data: [cPer, pPer, caPer, fPer],
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255,255,255,0.1)' },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        pointLabels: { color: '#94a3b8', font: {size: 11} },
                        ticks: { display: false, max: 100, min: 0 }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    function loadInsights(date) {
        fetch(`/api/insights?date=${date}`)
            .then(res => res.json())
            .then(data => {
                document.getElementById('health-score-value').textContent = data.health_score;
                document.getElementById('fav-food').textContent = data.favorite_food;
                document.getElementById('fav-meal').textContent = data.favorite_meal;
                
                const ul = document.getElementById('insights-list');
                ul.innerHTML = '';
                data.trends.forEach(t => {
                    const li = document.createElement('li');
                    li.textContent = t;
                    ul.appendChild(li);
                });
            });
    }

    function exportDoctorReport() {
        const reportDOM = document.getElementById('doctor-report');
        
        // Fill data
        document.getElementById('report-date').textContent = new Date().toLocaleDateString();
        document.getElementById('report-height').textContent = elHeight.value || '--';
        document.getElementById('report-weight').textContent = elWeight.value || '--';
        document.getElementById('report-bmi').textContent = elBmiValue.textContent;
        document.getElementById('report-health-score').textContent = document.getElementById('health-score-value').textContent;
        document.getElementById('report-water').textContent = currentWater;
        document.getElementById('report-fav-food').textContent = document.getElementById('fav-food').textContent;
        
        const trends = document.getElementById('insights-list').innerHTML;
        document.getElementById('report-trends').innerHTML = trends;

        // Briefly unhide
        reportDOM.style.display = 'block';

        const opt = {
            margin:       1,
            filename:     `Medical_Report_${currentDate}.pdf`,
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2 },
            jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
        };

        html2pdf().set(opt).from(reportDOM).save().then(() => {
            reportDOM.style.display = 'none'; // hide again
        });
    }
});
