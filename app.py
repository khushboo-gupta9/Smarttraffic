from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from threading import Thread
import time
import os
import base64
import json
from traffic_controller import controller
from sound_sensor import check_emergency_sound

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Absolute base directory (this file's location)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')  # Correct path to JSON

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'captured_images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
capture_counter = 1

# -------------------- Background Controller Thread --------------------
def background_controller():
    while True:
        if controller.mode == 'auto':
            controller.auto_cycle()
        elif controller.mode == 'emergency':
            controller.handle_emergency()
        time.sleep(1)

# -------------------- LOGIN ROUTE --------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
        except Exception as e:
            return render_template('login.html', error="User data not found.")

        if username and password and username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('loading'))
        else:
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')

# -------------------- LOADING ROUTE --------------------
@app.route('/loading')
def loading():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('loading.html')

# -------------------- INDEX PAGE ROUTE --------------------
@app.route('/index')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['user'])

# -------------------- API ROUTES --------------------
@app.route('/get_status')
def get_status():
    return jsonify(controller.get_status())

@app.route('/set_mode', methods=['POST'])
def set_mode():
    data = request.get_json()
    controller.set_mode(data.get('mode', 'auto'))
    return jsonify({'status': 'ok'})

@app.route('/set_timer', methods=['POST'])
def set_timer():
    data = request.get_json()
    controller.set_timer(int(data.get('time', 15)))
    return jsonify({'status': 'ok'})

@app.route('/start', methods=['POST'])
def start():
    controller.set_mode("auto")
    return jsonify({'status': 'started'})

@app.route('/stop', methods=['POST'])
def stop():
    controller.set_mode("manual")
    return jsonify({'status': 'stopped'})

@app.route('/detect_emergency', methods=['POST'])
def detect_emergency():
    direction = check_emergency_sound(controller.mode == 'emergency')
    if direction:
        controller.set_emergency(direction)
        return jsonify({'status': 'emergency', 'direction': direction})
    else:
        return jsonify({'status': 'no emergency'})

@app.route('/save_image', methods=['POST'])
def save_image():
    global capture_counter
    data = request.get_json()
    image_data = data['image'].split(",")[1]
    image_binary = base64.b64decode(image_data)

    filename = f"capture_{capture_counter}.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, 'wb') as f:
        f.write(image_binary)

    capture_counter += 1
    if capture_counter > 3:
        capture_counter = 1

    return "Image saved"

# -------------------- RUN APP --------------------
if __name__ == '__main__':
    Thread(target=background_controller, daemon=True).start()
    app.run(debug=True)
