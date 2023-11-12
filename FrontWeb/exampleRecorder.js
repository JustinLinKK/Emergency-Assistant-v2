// Variables to manage the recording state and audio data
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let silenceTimer;

// Request access to the user's microphone
navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        // Create a MediaRecorder instance
        mediaRecorder = new MediaRecorder(stream);

        // Event handler for when audio data is available
        mediaRecorder.ondataavailable = event => {
            // Add the current chunk of audio to the array
            audioChunks.push(event.data);

            // If we are still recording, reset the silence detection timer
            if (isRecording) {
                clearTimeout(silenceTimer);
                silenceTimer = setTimeout(endRecording, 700); // 0.7 seconds of silence
            }
        };

        // Event handler for when the recording stops
        mediaRecorder.onstop = sendAudioToServer;
    })
    .catch(error => {
        console.error("Error accessing the microphone: ", error);
    });

// Function to start recording
function startRecording() {
    audioChunks = []; // Clear previous audio data
    isRecording = true; // Set the recording flag
    mediaRecorder.start(); // Start recording
}

// Function to end the current recording
function endRecording() {
    isRecording = false; // Clear the recording flag
    mediaRecorder.stop(); // Stop recording
}

// Function to send the recorded audio to the server
function sendAudioToServer() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' }); // Create a Blob from the chunks
    const formData = new FormData();
    formData.append('audio', audioBlob); // Append the audio Blob to the FormData

    // Emit the audio data to the server using Socket.IO
    socket.emit('audio_chunk', formData);

    // If the recording was stopped manually, don't start a new recording
    if (isRecording) {
        startRecording(); // Start a new recording for the next speaker
    }
}

// Event listeners for the start and stop buttons
document.getElementById('startBtn').addEventListener('click', startRecording);
document.getElementById('stopBtn').addEventListener('click', () => isRecording = false);
