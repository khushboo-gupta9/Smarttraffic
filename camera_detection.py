import cv2
import os
import datetime

def detect_emergency_vehicle():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Error: Camera not accessible")
        return

    capture_folder = 'static/captures'
    os.makedirs(capture_folder, exist_ok=True)

    print("Starting camera detection...")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        # Dummy detection logic: Detect red color (simulate emergency light)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_red = (0, 120, 70)
        upper_red = (10, 255, 255)
        mask1 = cv2.inRange(hsv, lower_red, upper_red)

        lower_red2 = (170, 120, 70)
        upper_red2 = (180, 255, 255)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

        mask = mask1 + mask2
        red_detected = cv2.countNonZero(mask)

        if red_detected > 5000:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{capture_folder}/emergency_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Emergency vehicle detected! Image saved as {filename}")
            yield 'north'  # Simulate direction
        else:
            yield None
