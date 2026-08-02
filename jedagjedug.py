import cv2
import time
import math
import numpy as np
import random

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Error: Could not open camera.")
    exit()

# Timers
last_flip_time = time.time()
start_time = time.time()
last_flash_time = time.time()  # ADDED: Timer for flash effect
is_flipped = False

# Zoom settings
zoom_speed = 1.6  
min_zoom = 1.0    
max_zoom = 1.6    

# Rainbow hue shift counter
hue_shift = 0

print("Press 'q' to quit.")

while True:
    ret, frame = cam.read()
    if not ret:
        break

    height, width = frame.shape[:2]
    current_time = time.time()

    # el shakie intensiti
    shake_intensity = 6

    # ----------------------------------------------------
    # 1. AUTO-FLIP EVERY 2 SECONDS
    # ----------------------------------------------------
    if current_time - last_flip_time >= 2.0:
        is_flipped = not is_flipped
        last_flip_time = current_time

    if is_flipped:
        frame = cv2.flip(frame, 1)

    # ----------------------------------------------------
    # 2. SMOOTH ZOOM IN & OUT (Sine Wave Motion)
    # ----------------------------------------------------
    elapsed = current_time - start_time
    sine_val = (math.sin(elapsed * zoom_speed) + 1) / 3.0
    current_zoom = min_zoom + (max_zoom - min_zoom) * sine_val

    crop_w = int(width / current_zoom)
    crop_h = int(height / current_zoom)

    start_x = (width - crop_w) // 2
    start_y = (height - crop_h) // 2

    cropped_frame = frame[start_y : start_y + crop_h, start_x : start_x + crop_w]
    frame = cv2.resize(cropped_frame, (width, height), interpolation=cv2.INTER_LINEAR)

    # ----------------------------------------------------
    # 3. RAINBOW COLOR SHIFT (HSV Manipulation)
    # ----------------------------------------------------
    # Convert BGR image to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Split into H (Hue), S (Saturation), and V (Value) channels
    h, s, v = cv2.split(hsv)

    # Shift the hue channel by adding the hue offset (modulo 180 because OpenCV H ranges 0-179)
    h = (h.astype(np.uint16) + hue_shift) % 180
    h = h.astype(np.uint8)

    # Recombine channels and convert back to standard BGR for displaying
    hsv_rainbow = cv2.merge([h, s, v])
    rainbow_frame = cv2.cvtColor(hsv_rainbow, cv2.COLOR_HSV2BGR)

    # Increment hue offset for the next frame
    hue_shift = (hue_shift + 2) % 180

    # ----------------------------------------------------
    # 4. RANDOM SCREEN SHAKE EFFECT
    # ----------------------------------------------------
    # Generate random pixel shifts for X and Y axes
    dx = random.randint(-shake_intensity, shake_intensity)
    dy = random.randint(-shake_intensity, shake_intensity)

    # Build 2x3 translation matrix
    translation_matrix = np.float32([
        [1, 0, dx],
        [0, 1, dy]
    ])

    # Shift the frame. BORDER_REFLECT fills the exposed edges seamlessly instead of black space
    shaken_frame = cv2.warpAffine(
        rainbow_frame,
        translation_matrix, 
        (width, height), 
        borderMode=cv2.BORDER_WRAP
    )

    # ----------------------------------------------------
    # 5. FLASH EFFECT
    # ----------------------------------------------------
    # Trigger a flash every 3 seconds (synced with flip or independent)
    flash_duration = 0.25  # How long the flash lasts in seconds
    time_since_flash = current_time - last_flash_time

    if time_since_flash >= 2.0:
        last_flash_time = current_time

    if time_since_flash < flash_duration:
        # Calculate flash intensity fading out from 1.0 (pure white) to 0.0
        alpha = 1.0 - (time_since_flash / flash_duration)
        white_screen = np.full_like(shaken_frame, 255)
        shaken_frame = cv2.addWeighted(white_screen, alpha, shaken_frame, 1.0 - alpha, 0)

    # ----------------------------------------------------
    # 6. DISPLAY FRAME & STATUS, DISABLED BY DEFAULT
    # ----------------------------------------------------
    status_text = f"Flipped: {is_flipped} | Zoom: {current_zoom:.2f}x | Hue: {hue_shift}"
    #cv2.putText(rainbow_frame, status_text, (20, 40), 
                #cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    cv2.imshow('jedagjedug', shaken_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()