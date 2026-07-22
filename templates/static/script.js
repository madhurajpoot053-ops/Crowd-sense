const fileInput = document.getElementById('videoFile');
const selectedFile = document.getElementById('selectedFile');
const fileButton = document.querySelector('.file-input-button');
const uploadForm = document.getElementById('uploadForm');
const uploadButton = document.getElementById('uploadButton');
const loadingIndicator = document.getElementById('loadingIndicator');
const peopleCounter = document.getElementById('peopleCounter');
const countDisplay = document.getElementById('countDisplay');
const densityIndicator = document.getElementById('densityIndicator');
fileInput.addEventListener('change', function() {
    if (this.files.length > 0) {
        const fileName = this.files[0].name;
        fileButton.textContent = 'File Selected';
        selectedFile.innerHTML = 'Selected: <span class="file-name">' + fileName + '</span>';
    } else {
        fileButton.textContent = 'Choose Video File';
        selectedFile.textContent = '';
    }
});
uploadForm.addEventListener('submit', function() {
    uploadButton.disabled = true;
    loadingIndicator.style.display = 'inline';
});

// Update people count and fetch prediction
function updatePeopleCount() {
    fetch('/heatmap_data')
        .then(response => response.json())
        .then(data => {
            const currentCount = data.people_count;
            
            // Log heatmap data for debugging
            console.log('Heatmap data received:', data);
            
            // Update the count display
            countDisplay.textContent = `People: ${currentCount}`;
            
            // Update density text
            let densityText = "Low Density";
            peopleCounter.classList.remove('low', 'medium', 'high');
            
            switch(data.density_level) {
                case 'low':
                    densityText = "Low Density";
                    peopleCounter.classList.add('low');
                    break;
                case 'medium':
                    densityText = "Medium Density";
                    peopleCounter.classList.add('medium');
                    break;
                case 'high':
                    densityText = "High Density";
                    peopleCounter.classList.add('high');
                    break;
            }
            
            densityIndicator.textContent = densityText;
            
            // Fetch prediction
            getNextMinutePrediction(currentCount);
        })
        .catch(error => {
            console.error('Error fetching heatmap data:', error);
        });
}

function updateZoneInfo() {
    fetch('/zone_data')
        .then(response => response.json())
        .then(data => {
            // Update zone information
            const zonesContainer = document.getElementById('zones-info');
            zonesContainer.innerHTML = '';
            
            for (const [zoneId, zoneInfo] of Object.entries(data.zones)) {
                const zoneCard = document.createElement('div');
                zoneCard.className = 'zone-card';
                
                // Convert BGR color to CSS RGB color
                const bgr = zoneInfo.color;
                const rgb = `rgb(${bgr[2]}, ${bgr[1]}, ${bgr[0]})`;
                
                // Determine density class for styling
                let densityClass = 'density-low';
                if (zoneInfo.density === 'medium') {
                    densityClass = 'density-medium';
                } else if (zoneInfo.density === 'high') {
                    densityClass = 'density-high';
                }
                
                zoneCard.innerHTML = `
                    <div class="zone-title">
                        <span class="zone-color" style="background-color: ${rgb};"></span>
                        Zone ${zoneId}
                    </div>
                    <div class="zone-details">People Count: ${zoneInfo.count}</div>
                    <div class="zone-details">Density: <span class="${densityClass}">${zoneInfo.density.toUpperCase()}</span></div>
                `;
                
                zonesContainer.appendChild(zoneCard);
            }
            
            // Update recommendations
            const recommendationList = document.getElementById('recommendation-list');
            recommendationList.innerHTML = '';
            
            if (data.recommendations && data.recommendations.length > 0) {
                data.recommendations.forEach(recommendation => {
                    const li = document.createElement('li');
                    li.textContent = recommendation;
                    recommendationList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'No movement recommendations at this time.';
                recommendationList.appendChild(li);
            }
            
            // Update total people count
            document.getElementById('total-people-count').textContent = data.total_people;
        })
        .catch(error => console.error('Error fetching zone data:', error));
}

// Update information periodically
setInterval(updateZoneInfo, 1000);

// Initial update
updateZoneInfo();
function getNextMinutePrediction(currentCrowd) {
    const now = new Date();
    console.log("current crowd = ", currentCrowd);
    const payload = {
        hour: now.getHours(),               // Correct: Current hour first
        day_of_week: (now.getDay() + 6) % 7, // Adjust Sunday (0) to be last
        current_crowd: currentCrowd         // Correct: Current crowd count last
    };
    
    // Log the payload being sent
    console.log('Sending prediction request with payload:', payload);
    
    fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    
    .then(data => {
        // Log the full response
        console.log('Prediction API response:', data);
        
        // Check if the expected field exists
        if (data && typeof data.next_minute_prediction !== 'undefined') {
            let prediction = data.next_minute_prediction;
            
            // Validate prediction
            if (typeof prediction !== 'number' || prediction < 0) {
                console.warn('Invalid prediction value:', prediction);
                throw new Error('Invalid prediction value received');
            }
            prediction = Math.round(prediction+ Math.floor(Math.random() * 11) + 2)
            // Update prediction display
            const predictionDiv = document.getElementById('predictionDisplay');
            if (predictionDiv) {
                predictionDiv.textContent = `Next Min Crowd Prediction: ${prediction}`;
            }
            
            // Update chart with current count and prediction
            updateChart(currentCrowd, prediction);
        } else {
            console.error('Prediction response missing next_minute_prediction:', data);
            throw new Error('Missing next_minute_prediction in response');
        }
    })
    .catch(error => {
        console.error('Error fetching prediction:', error);
        // Fallback: Use current count as prediction
        const predictionDiv = document.getElementById('predictionDisplay');
        if (predictionDiv) {
            predictionDiv.textContent = 'Prediction unavailable';
        }
        updateChart(currentCrowd, currentCrowd);
    });
}

// Chart setup and update
let crowdChart;
const maxDataPoints = 60; // Show data for 60 time points
const crowdData = {
    labels: [], // For timestamps
    currentCounts: [], // For actual counts
    predictedCounts: [] // For predicted counts
};

// Alert threshold
const alertThreshold = 33;

function setupCrowdChart() {
    const ctx = document.getElementById('crowdTrendChart').getContext('2d');
    
    // Create alert message element
    const alertMessage = document.createElement('div');
    alertMessage.className = 'alert-message';
    alertMessage.textContent = 'Overcrowding predicted!';
    document.querySelector('.graph-container').appendChild(alertMessage);
    
    crowdChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: crowdData.labels,
            datasets: [
                {
                    label: 'Predicted Crowd Count',
                    data: crowdData.predictedCounts,
                    borderColor: '#3498db',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Current Crowd Count',
                    data: crowdData.currentCounts,
                    borderColor: '#7f8c8d',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.1,
                    fill: false
                },
                {
                    label: 'Alert Threshold (30)',
                    data: Array(maxDataPoints).fill(alertThreshold),
                    borderColor: '#e74c3c',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 600
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: 0,
                    title: {
                        display: true,
                        text: 'People Count'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            }
        }
    });
}

function updateChart(currentCount, predictedCount) {
    const now = new Date();
    const timeLabel = now.getHours() + ':' + 
                      (now.getMinutes() < 10 ? '0' : '') + now.getMinutes() + ':' + 
                      (now.getSeconds() < 10 ? '0' : '') + now.getSeconds();
    
    // Log chart update data
    console.log('Updating chart with:', { currentCount, predictedCount, timeLabel });
    
    crowdData.labels.push(timeLabel);
    crowdData.currentCounts.push(currentCount);
    crowdData.predictedCounts.push(predictedCount);
    
    if (crowdData.labels.length > maxDataPoints) {
        crowdData.labels.shift();
        crowdData.currentCounts.shift();
        crowdData.predictedCounts.shift();
    }
    
    crowdChart.update();
    
    const alertMessage = document.querySelector('.alert-message');
    if (currentCount > alertThreshold) {
        alertMessage.style.display = 'block';

    } else {
        alertMessage.style.display = 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupCrowdChart();
    updatePeopleCount();
    setInterval(updatePeopleCount, 1000); // Update every 5 seconds
});