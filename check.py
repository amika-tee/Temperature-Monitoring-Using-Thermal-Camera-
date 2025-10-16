import cv2 as cv
import numpy as np

cap = cv.VideoCapture(0, cv.CAP_V4L2)
cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('Y', '1', '6', ' '))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 160)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 120)
cap.set(cv.CAP_PROP_FPS, 9)
cap.set(cv.CAP_PROP_CONVERT_RGB, 0)

x_mouse = 0
y_mouse = 0

def mouse_events(event, x, y, flags, param):
    if event == cv.EVENT_MOUSEMOVE:
        global x_mouse
        global y_mouse
        x_mouse = x
        y_mouse = y

def create_color_bar(height, width=50, colormap=cv.COLORMAP_INFERNO):
    """Create a vertical color bar"""
    # Create a gradient from 0 to 255
    gradient = np.linspace(255, 0, height).astype(np.uint8)
    # Reshape to create a vertical bar
    color_bar = np.tile(gradient.reshape(-1, 1), (1, width))
    # Apply the same colormap as the thermal image
    color_bar_colored = cv.applyColorMap(color_bar, colormap)
    return color_bar_colored

def raw_to_celsius(raw_value):
    """Convert raw thermal value to Celsius"""
    return (raw_value / 100) - 273.15

minraw = 26315  # --> -10 celsius
maxraw = 41315  # --> 140 celsius
 
mintemp = -10
maxtemp = 140

while True:
    ret, frame = cap.read()
    if ret:
        frame = cv.resize(frame, (640, 480), interpolation=cv.INTER_CUBIC)
        
        if frame.dtype == np.uint16:
            # Thermal pointer
            temp_pointer = frame[y_mouse, x_mouse]
            temp_pointer_celsius = raw_to_celsius(temp_pointer)
            
            # Find actual min/max temperatures in current frame
            current_min_raw = frame.min()
            current_max_raw = frame.max()
            current_min_celsius = raw_to_celsius(current_min_raw)
            current_max_celsius = raw_to_celsius(current_max_raw)
            
            # Process thermal image
            clipped = np.clip(frame, minraw, maxraw)
            frame_8 = ((clipped - minraw) / (maxraw - minraw) * 255).astype(np.uint8)
            mask = (frame_8 < 50).astype(np.uint8) * 255
            thermal_fixed = cv.inpaint(frame_8, mask, inpaintRadius=3, flags=cv.INPAINT_TELEA)
            thermal_frame = cv.applyColorMap(thermal_fixed, cv.COLORMAP_INFERNO)
            
            # Create color bar
            color_bar = create_color_bar(thermal_frame.shape[0], width=50)
            
            # Create a larger image to accommodate color bar and labels
            bar_width = 180  # Space for color bar + labels
            combined_width = thermal_frame.shape[1] + bar_width
            combined_frame = np.zeros((thermal_frame.shape[0], combined_width, 3), dtype=np.uint8)
            
            # Place thermal image
            combined_frame[:, :thermal_frame.shape[1]] = thermal_frame
            
            # Place color bar
            combined_frame[:, thermal_frame.shape[1]:thermal_frame.shape[1]+50] = color_bar
            
            # Add min/max temperature labels to color bar
            font = cv.FONT_HERSHEY_SIMPLEX
            font_scale = 0.4
            color = (255, 255, 255)
            thickness = 1
            
            # Add MAX temperature at the top
            max_text = f"MAX: {maxtemp} Celsius"
            x_pos = thermal_frame.shape[1] + 55
            cv.putText(combined_frame, max_text, (x_pos, 20), font, font_scale, color, thickness)
            
            # Add MIN temperature at the bottom
            min_text = f"MIN: {mintemp} Celsius"
            y_pos = thermal_frame.shape[0] - 10
            cv.putText(combined_frame, min_text, (x_pos, y_pos), font, font_scale, color, thickness)
            
            # Display min/max temperatures on the thermal frame itself
            frame_font = cv.FONT_HERSHEY_SIMPLEX
            frame_font_scale = 0.5
            frame_color = (0, 255, 255)  # Yellow color
            frame_thickness = 1
            
            cv.putText(combined_frame, f"Min: {current_min_celsius:.1f}°C", (10, 20), 
                      frame_font, frame_font_scale, frame_color, frame_thickness)
            cv.putText(combined_frame, f"Max: {current_max_celsius:.1f}°C", (10, 40), 
                      frame_font, frame_font_scale, frame_color, frame_thickness)
            
            # Show thermal pointer (uncomment if you want to use mouse tracking)
            # cv.circle(combined_frame, (x_mouse, y_mouse), 2, (0, 0, 0), -1)
            # cv.putText(combined_frame, f"{temp_pointer_celsius:.1f}°C", (x_mouse - 40, y_mouse - 15), 
            #           cv.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 1)
            
            # Set mouse callback (uncomment if you want mouse tracking)
            # cv.setMouseCallback('Thermal camera', mouse_events)
            
            cv.imshow('Thermal camera', combined_frame)
        else:
            cv.imshow('Raw Frame', frame)
        
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        print("No frame received")
        break

cap.release()
cv.destroyAllWindows()