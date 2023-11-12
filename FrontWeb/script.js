const socket = io(); // Initialize socket
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let silenceTimer;

// Get user media for recording
navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
            if (isRecording) {
                clearTimeout(silenceTimer);
                silenceTimer = setTimeout(endRecording, 700); // 0.7 seconds of silence
            }
        };
        mediaRecorder.onstop = sendAudioToServer;
    }).catch(error => {
        console.error("Error accessing media devices:", error);
    });

// Start recording
function startRecording() {
    audioChunks = [];
    isRecording = true;
    mediaRecorder.start();
}

// End recording
function endRecording() {
    isRecording = false;
    mediaRecorder.stop();
}

// Send audio to server
function sendAudioToServer() {
    const audioBlob = new Blob(audioChunks);
    const formData = new FormData();
    formData.append('audio', audioBlob);
    socket.emit('audio_chunk', formData);
    if (isRecording) {
        startRecording(); // Start next recording
    }
}

// Add event listeners to buttons
document.getElementById('startRecording').addEventListener('click', startRecording);
document.getElementById('endRecording').addEventListener('click', () => isRecording = false);
document.getElementById('generateReport').addEventListener('click', () => {
    socket.emit('report_generation');
});

// Handle report generation
socket.on('report', (data) => {
    displayReport(data.reclassified_text);
    showMap(data.situation_location_latitude, data.situation_location_longitude);
});

// Display report
function displayReport(report) {
    const reportSection = document.getElementById('reportSection');
    reportSection.innerHTML = `<pre>${report}</pre>`;
}

// Show map
function showMap(lat, lng) {
    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 8,
        center: { lat: parseFloat(lat), lng: parseFloat(lng) },
    });

    new google.maps.Marker({
        position: { lat: parseFloat(lat), lng: parseFloat(lng) },
        map: map,
    });
}
