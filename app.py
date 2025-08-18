from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from threading import Thread
import time, os, base64, json, cv2
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
import numpy as np

# project modules
from traffic_controller import controller
from sound_sensor import start_siren_listener   # NEW: mic siren listener

app = Flask(__name__)
app.secret_key = 'your_secret_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'captured_images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
capture_counter = 1

# Haar cascade for face detection (OpenCV)
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


# -------------------- Background Controller Thread --------------------
def background_controller():
    """Main traffic loop (auto/emergency handling)."""
    while True:
        try:
            if controller.mode == 'auto':
                # auto mode cycles normally; emergency is now triggered by mic listener
                controller.auto_cycle()
            elif controller.mode == 'emergency':
                controller.handle_emergency()
        except Exception as e:
            print("[controller-loop] error:", e)
        time.sleep(1)


# -------------------- Routes (login, pages) --------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            with open(USERS_FILE, 'r') as f:
                users = json.load(f)
        except Exception:
            return render_template('login.html', error="User data not found.")
        if username and password and username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('loading'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/loading')
def loading():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('loading.html')

@app.route('/index')
@app.route('/index.html')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['user'])

@app.route('/manual')
@app.route('/camera.html')
def manual():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('camera.html', username=session['user'])

@app.route('/auto')
@app.route('/auto.html')
def auto():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('auto.html', username=session['user'])

@app.route('/emergency')
@app.route('/emergency.html')
def emergency():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('emergency.html', username=session['user'])

@app.route('/settings')
@app.route('/setting.html')
def settings():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('setting.html', username=session['user'])


# -------------------- API ROUTES (controller) --------------------
@app.route('/get_status')
def get_status():
    """Return live controller status (mode, active direction, timers, etc.)."""
    return jsonify(controller.get_status())

@app.route('/set_mode', methods=['POST'])
def set_mode():
    data = request.get_json(force=True, silent=True) or {}
    controller.set_mode(data.get('mode', 'auto'))
    return jsonify({'status': 'ok'})

@app.route('/set_timer', methods=['POST'])
def set_timer():
    data = request.get_json(force=True, silent=True) or {}
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

# Manual test trigger (useful if mic not available)
@app.route('/emergency/trigger', methods=['POST'])
def emergency_trigger():
    data = request.get_json(force=True, silent=True) or {}
    direction = data.get('direction', 'North')
    controller.set_emergency(direction)
    return jsonify({'status': 'triggered', 'direction': direction})


# -------------------- Serve saved images --------------------
@app.route('/captured_images/<path:filename>')
def serve_captured_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# -------------------- Utility: create mock driving license image --------------------
def create_mock_license(face_img_path, username_hint="Unknown"):
    """
    Creates a demo/mock driving license image using the saved face image.
    Returns the generated filename (relative to UPLOAD_FOLDER).
    """
    name = username_hint if username_hint else "Demo User"
    dl_no = "DL" + datetime.now().strftime("%m%d%H%M%S")
    dob = (datetime.now() - timedelta(days=25*365)).strftime("%d/%m/%Y")
    issue = datetime.now().strftime("%d/%m/%Y")
    expiry = (datetime.now() + timedelta(days=10*365)).strftime("%d/%m/%Y")

    w, h = 900, 560
    card = Image.new("RGB", (w, h), (235, 245, 252))
    draw = ImageDraw.Draw(card)

    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 36)
        font_regular = ImageFont.truetype("arial.ttf", 24)
        font_large = ImageFont.truetype("arialbd.ttf", 48)
    except Exception:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_large = ImageFont.load_default()

    draw.rectangle([(0,0),(w,110)], fill=(18,60,150))
    draw.text((24, 28), "DRIVING LICENSE (DEMO)", font=font_large, fill=(255,255,255))

    if os.path.exists(face_img_path):
        try:
            face = Image.open(face_img_path).convert("RGB")
            face_thumb = face.resize((260, 320))
            card.paste(face_thumb, (40, 140))
        except Exception:
            pass

    x_base = 320
    draw.text((x_base, 150), f"Name: {name}", font=font_bold, fill=(0,0,0))
    draw.text((x_base, 200), f"DL Number: {dl_no}", font=font_regular, fill=(0,0,0))
    draw.text((x_base, 250), f"Date of Birth: {dob}", font=font_regular, fill=(0,0,0))
    draw.text((x_base, 300), f"Issue Date: {issue}", font=font_regular, fill=(0,0,0))
    draw.text((x_base, 350), f"Expiry Date: {expiry}", font=font_regular, fill=(0,0,0))
    draw.line((x_base, 420, x_base+180, 480), fill=(0,0,0), width=3)
    draw.text((x_base, 490), "Signature (Demo)", font=font_regular, fill=(0,0,0))

    license_filename = f"license_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    license_path = os.path.join(UPLOAD_FOLDER, secure_filename(license_filename))
    card.save(license_path)
    return os.path.basename(license_path)


# -------------------- SAVE IMAGE route (accept base64 from frontend) --------------------
@app.route('/save_image', methods=['POST'])
def save_image():
    global capture_counter
    data = request.get_json()

    if not data or 'image' not in data:
        return jsonify({"status": "error", "message": "No image data provided"}), 400

    try:
        image_b64 = data['image'].split(",")[1]
        image_bytes = base64.b64decode(image_b64)
        capture_filename = f"capture_{int(time.time())}.png"
        capture_path = os.path.join(UPLOAD_FOLDER, secure_filename(capture_filename))
        with open(capture_path, 'wb') as f:
            f.write(image_bytes)

        img_cv = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img_cv is None:
            img_cv = cv2.imread(capture_path)

        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))

        face_crop_path = capture_path
        if len(faces) > 0:
            (x,y,wf,hf) = faces[0]
            face_roi = img_cv[y:y+hf, x:x+wf]
            face_filename = f"face_{int(time.time())}.png"
            face_path = os.path.join(UPLOAD_FOLDER, secure_filename(face_filename))
            cv2.imwrite(face_path, face_roi)
            face_crop_path = face_path

        name_hint = session.get('user', 'Demo User')
        license_filename = create_mock_license(face_crop_path, username_hint=name_hint)

        capture_counter += 1
        if capture_counter > 1000000:
            capture_counter = 1

        return jsonify({
            "status": "ok",
            "capture_filename": os.path.basename(capture_path),
            "license_filename": license_filename,
            "face_found": len(faces) > 0
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------- RUN APP --------------------
if __name__ == '__main__':
    # 1) traffic controller loop
    Thread(target=background_controller, daemon=True).start()

    # 2) MIC SIREN LISTENER (auto emergency trigger)
    def on_siren_detect(direction):
        """
        Callback jab siren detect ho: direction choose karke emergency trigger.
        Direction yahan tum chaaho to density-based choose kar sakte ho.
        """
        # If already in emergency, ignore duplicate triggers
        if getattr(controller, "emergency_active", False):
            return
        # Choose a direction (you can make it smarter)
        chosen = direction or 'North'
        print(f"[siren] Detected! Triggering emergency on {chosen}")
        try:
            controller.set_emergency(chosen)
        except Exception as e:
            print("[siren] trigger error:", e)
 # ... (your full code as given above)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------------------- RUN APP --------------------
if __name__ == '__main__':
    # 1) traffic controller loop
    Thread(target=background_controller, daemon=True).start()

    # 2) MIC SIREN LISTENER (auto emergency trigger)
    def on_siren_detect(direction):
        if getattr(controller, "emergency_active", False):
            return
        chosen = direction or 'North'
        print(f"[siren] Detected! Triggering emergency on {chosen}")
        try:
            controller.set_emergency(chosen)
        except Exception as e:
            print("[siren] trigger error:", e)


    # Start listener; if mic/PyAudio missing, it auto-falls-back to simulation
    Thread(target=start_siren_listener, args=(on_siren_detect,), kwargs={"cooldown": 15}, daemon=True).start()

    app.run(debug=True)
