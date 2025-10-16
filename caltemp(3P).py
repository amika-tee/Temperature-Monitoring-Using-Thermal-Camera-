import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import time
from collections import deque

cap = cv.VideoCapture(0, cv.CAP_V4L2)
cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('Y', '1', '6', ' '))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 160)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 120)
cap.set(cv.CAP_PROP_FPS, 9)
cap.set(cv.CAP_PROP_CONVERT_RGB, 0)

temperature_data = []
timestamps = []
sample_count = 0
points = []

# Buffer to store last 5 temperature readings for both points
temp_buffer_p1 = deque(maxlen=10)
temp_buffer_p2 = deque(maxlen=10)
temp_buffer_p3 = deque(maxlen=10)

# Timer for 2-second display updates
last_display_time = time.time()
display_interval = 2.0  # 2 seconds


def format_buffer_display(buffer, point_name):
    """Format buffer contents for display"""
    if len(buffer) == 0:
        return f"{point_name} Buffer: Empty"
    
    temps_str = ", ".join([f"{temp:.2f}°C" for temp in buffer])
    return f"{point_name} Buffer ({len(buffer)}/5): [{temps_str}]"

minraw = 26315  # --> -10 celsius
maxraw = 41315  # --> 140 celsius
# minraw = 27000  # --> -3.15 celsius
# maxraw = 35000  # --> 76.85 celsius

print(f"Starting data collection")

while True:
    ret, frame = cap.read()
    current_time = time.time()
    if ret:
        frame = cv.resize(frame, (720, 640), interpolation=cv.INTER_CUBIC)
        height, width = frame.shape[:2]
        center_x, center_y = width//2, height//2
        
        if frame.dtype == np.uint16:
            temp_center = frame[center_y, center_x]
            temp_celsius = (temp_center / 100) - 273.15
            m = 0.738
            b = 5.073
            cal_temp_p2 = (temp_celsius - b) / m
            temp_buffer_p2.append(cal_temp_p2)
            
            # Calculate average of last 5 frames for Point 2
            if len(temp_buffer_p2) > 0:
                avg_temp_p2 = sum(temp_buffer_p2) / len(temp_buffer_p2)
            else:
                avg_temp_p2 = cal_temp_p2

            # Process frame for display
            clipped = np.clip(frame, minraw, maxraw)
            frame_8 = ((clipped - minraw) / (maxraw - minraw) * 255).astype(np.uint8)
            thermal_frame = cv.applyColorMap(frame_8, cv.COLORMAP_JET)
    
            # Point 1
            p1_x = 182
            p1_y = height//2 
            
            if 0 <= p1_x < width and 0 <= p1_y < height:
                temp_p1_raw = frame[p1_y, p1_x]
                temp_p1 = (temp_p1_raw / 100) - 273.15
                m = 0.670
                b = 7.939
                cal_temp_p1 = (temp_p1 - b) / m
                temp_buffer_p1.append(cal_temp_p1)

                if len(temp_buffer_p1) > 0:
                    avg_temp_p1 = sum(temp_buffer_p1) / len(temp_buffer_p1)
                else:
                    avg_temp_p1 = cal_temp_p1
            else:
                avg_temp_p1 = float('nan')  
            
            # Point 3
            p3_x = 580
            p3_y = height//2 
            
            if 0 <= p3_x < width and 0 <= p3_y < height:
                temp_p3_raw = frame[p3_y, p3_x]
                temp_p3 = (temp_p3_raw / 100) - 273.15
                m = 0.607
                b = 10.868
                cal_temp_p3 = (temp_p3 - b) / m
                temp_buffer_p3.append(cal_temp_p3)

                if len(temp_buffer_p3) > 0:
                    avg_temp_p3 = sum(temp_buffer_p3) / len(temp_buffer_p3)
                else:
                    avg_temp_p3 = cal_temp_p3
            else:
                avg_temp_p3 = float('nan') 

            # Point 1 (left)
            if 0 <= p1_x < width and 0 <= p1_y < height:
                cv.circle(thermal_frame, (p1_x, p1_y), 2, (0, 0, 0), -1)
                cv.putText(thermal_frame, "P1",
                          (p1_x - 10, p1_y - 20), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)
                cv.putText(thermal_frame, "P1 (right): {0:.3f} Celsius".format(avg_temp_p1),
                          (30, height - 90), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)
            
            else:
                cv.putText(thermal_frame, "P3: Out of bounds",
                          (30, 60), cv.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 0), 2)

            # Point 2 (center)
            cv.circle(thermal_frame, (center_x, center_y), 2, (0, 0, 0), -1)
            cv.putText(thermal_frame, "P2",
                    (center_x - 10, center_y - 20), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)
            cv.putText(thermal_frame, "P2 (center): {0:.3f} Celsius".format(avg_temp_p2),
                      (30, height - 50), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)
               
            # Point 3 (left)
            if 0 <= p3_x < width and 0 <= p3_y < height:
                cv.circle(thermal_frame, (p3_x, p3_y), 2, (0, 0, 0), -1)
                cv.putText(thermal_frame, "P3",
                          (p3_x - 10, p3_y - 20), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)
                cv.putText(thermal_frame, "P3 (left): {0:.3f} Celsius".format(avg_temp_p3),
                          (30, height - 10), cv.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)
            
            else:
                cv.putText(thermal_frame, "P3: Out of bounds",
                          (30, 60), cv.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 0), 2)
        
            print("\n" + "="*80)
            print(f"Temperature Update - {datetime.now().strftime('%H:%M:%S')}")
            print("="*80)
            
            print(f"Point 2 - Current: {temp_celsius:.3f}°C, Average (last {len(temp_buffer_p2)} frames): {avg_temp_p2:.3f}°C")
            print(f"Position: x2 = {center_x}, y2 = {center_y}")
            print(format_buffer_display(temp_buffer_p2, "P2"))
            
            if not np.isnan(avg_temp_p3):
                print(f"\nPoint 3 - Current: {temp_p3:.3f}°C, Average (last {len(temp_buffer_p3)} frames): {avg_temp_p3:.3f}°C")
                print(f"Position: x3 = {p3_x}, y3 = {p3_y}")
                print(format_buffer_display(temp_buffer_p3, "P3"))
            else:
                print(f"\nPoint 3 - Out of bounds")
                print(format_buffer_display(temp_buffer_p3, "P3"))
            
            print("="*80)
            
            #time.sleep(0.5)

            cv.imshow('Thermal camera', thermal_frame)
        else:
            cv.imshow('Raw Frame', frame)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        print("No frame received")
        break

cap.release()
cv.destroyAllWindows()