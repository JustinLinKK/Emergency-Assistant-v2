from flask import Flask, request
from flask_socketio import SocketIO, emit
import os
import wave
import io
from serverEme import audio_to_text, reclassify, find_nearest_services, get_location


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)
OPENAI_API_KEY = 'your_openai_api_key'
GOOGLE_MAP_API_KEY = 'your_google_map_api_key'


global original_transcript 
original_transcript = ""

# Directory to save audio files
AUDIO_SAVE_PATH = 'recorded_audios'
if not os.path.exists(AUDIO_SAVE_PATH):
    os.makedirs(AUDIO_SAVE_PATH)

@app.route('/')
def index():
    # Serve your HTML page here
    return "Recording App"

@socketio.on('audio_chunk')
def handle_audio_chunk(json):
    # Convert the JSON data to bytes
    audio_data = json['audio'].encode('utf-8')

    # Convert bytes data to a BytesIO object
    audio_stream = io.BytesIO(audio_data)

    # Save the audio stream as a WAV file
    save_audio_as_wav(audio_stream)

def save_audio_as_wav(audio_stream):
    try:
        # Generate a unique filename for each audio file
        filename = os.path.join(AUDIO_SAVE_PATH, f"audio_{socketio.sid}_{len(os.listdir(AUDIO_SAVE_PATH))}.wav")

        # Open a new WAV file in write mode
        with wave.open(filename, 'wb') as wav_file:
            # Set parameters for the WAV file
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # Sample width in bytes
            wav_file.setframerate(44100)  # Frame rate

            # Write audio frames to the WAV file
            wav_file.writeframes(audio_stream.read())
        print(f"Saved: {filename}")
    except Exception as e:
        print(f"Error saving audio: {e}")
    
    text = audio_to_text(filename, OPENAI_API_KEY)
    global original_transcript
    original_transcript = original_transcript + text + "\n"



@socketio.event()
def report_generation():

    global original_transcript

    prefix = """Generate a brief report based on the following transcript. The report format should be:\n
    Situation Summary: (Identify if it is fake or not, if fake then provide reason and return string None in all sections next to it)\n
    Situation Location: \n
    Situation Scale: (a number between 1 and 5)\n
    Required unit type: (Three options: 1. Ambulance 2. Fire Engine 3. Police Car, at least choose one of them, separate mutichoice with comma)\n\n
    Below is transcript: \n\n"""
    
    # Reclassify the text
    reclassified_text = reclassify(original_transcript, prefix, OPENAI_API_KEY)

    # Find the line of Location and extract the location
    location = ""
    for line in reclassified_text.splitlines():
        if "Situation Location" in line:
            location = line.split(":")[1].strip()
            break
    
    # Find the line of Scale and extract the scale
    scale = ""
    for line in reclassified_text.splitlines():
        if "Situation Scale" in line:
            scale = line.split(":")[1].strip()
            break
    
    # Find the line of Unit Type and extract the unit type, unit type can be multiple separated by comma
    unit_type = []
    for line in reclassified_text.splitlines():
        if "Required unit type" in line:
            unit_type_string = line.split(":")[1].strip()
            if ',' in unit_type_string:
                unit_type = unit_type_string.split(",")
            else:
                unit_type.append(unit_type_string)
            break
        
    # Find the nearest services
    services = find_nearest_services(GOOGLE_MAP_API_KEY, location)
    
    # Generate the report suggestion location based on the services and unit type required
    unit_suggestion_location = "\n Unit Suggestion Location: \n "
    for service in services:
        if service in unit_type:
            unit_suggestion_location = unit_suggestion_location + service + ": " + services[service] + "\n"
            
    # Append the unit suggestion location to the reclassified text
    reclassified_text = reclassified_text + unit_suggestion_location
    
    # Get the location of the situation
    situation_location_latitude, situation_location_longitude = get_location(GOOGLE_MAP_API_KEY, location)
    
    # Emit the reclassified text and the location of the situation
    emit('report', {'reclassified_text': reclassified_text, 'situation_location_latitude': situation_location_latitude, 'situation_location_longitude': situation_location_longitude})
    
    




if __name__ == '__main__':
    socketio.run(app, debug=True)
