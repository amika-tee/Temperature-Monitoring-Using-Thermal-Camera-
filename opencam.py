import cv2 as cv
import time

# Initialize camera
cap = cv.VideoCapture(0)

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

# Set camera properties (optional - try these for thermal cameras)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 160)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 120)
cap.set(cv.CAP_PROP_FPS, 30)

# Set buffer size to reduce latency
cap.set(cv.CAP_PROP_BUFFERSIZE, 1)

print("Camera initialized. Press 'q' to quit.")

while True:
    # Capture frame
    ret, frame = cap.read()
    
    # Check if frame was captured successfully
    if not ret or frame is None:
        print("Warning: Could not read frame from camera")
        time.sleep(0.1)  # Small delay before retrying
        continue
    
    # Check if frame has valid dimensions
    if frame.shape[0] == 0 or frame.shape[1] == 0:
        print("Warning: Frame has invalid dimensions")
        continue
    
    print(f"Original frame size: {frame.shape}")
    
    # Resize frame from whatever size to 640x480
    try:
        resized_frame = cv.resize(frame, (640, 480), interpolation=cv.INTER_CUBIC)
        print(f"Resized frame size: {resized_frame.shape}")
        
        # Display both original and resized frames
        cv.imshow('Original', frame)
        cv.imshow('Resized', resized_frame)
        
    except cv.error as e:
        print(f"OpenCV error during resize: {e}")
        continue
    
    # Break on 'q' key press
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv.destroyAllWindows()
print("Camera released and windows closed.")