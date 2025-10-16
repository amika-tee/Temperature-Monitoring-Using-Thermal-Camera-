import cv2 as cv
import numpy as np
from datetime import datetime
import time
from collections import deque
from queue import Queue, Full, Empty
from SendtempTCP import ModbusClient

# Temperature range
minraw = 26315  # --> -10 celsius
maxraw = 42315  # --> 150 celsius
# maxraw = 47315  # --> 200 celsius

BUF_SIZE = 2

class ThermalCamera:
    def __init__(self):
        self.cap = cv.VideoCapture(0, cv.CAP_V4L2)
        self.cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('Y', '1', '6', ' '))
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 160)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 120)
        self.cap.set(cv.CAP_PROP_FPS, 9)
        self.cap.set(cv.CAP_PROP_CONVERT_RGB, 0)
        self.points = []

        self.p1 = None
        self.p2 = None
        self.p3 = None

        # Buffers for each point
        self.buffers = {
            "state1": deque(maxlen=5),
            "state2": deque(maxlen=5),
            "state3": deque(maxlen=5),
        }

        self.frame_queue = Queue(BUF_SIZE)

        self.compensation = {
            "left" : {"m": 0.752, "b": 5.093},
            #"middle" : {"m": 0.885, "b": 0.731},
            #"middle" : {"m": 0.770, "b": 3.671},
            "middle" : {"m": 0.728, "b": 5.142},
            "right" : {"m": 0.704, "b": 5.190}
        }

        self.avg_temp_send = {
            "state1": [],
            "state2": [],
            "state3": []
        }

        # -------- PLC SETTING --------
        self.plc = ModbusClient("192.168.3.40")
        if self.plc.connect():
            print("Connected to PLC")
        else:
            print("Failed to connect to PLC")

        # -------- FRAME SETTING --------
        self.window_name = "Thermal Machine Detection"
        cv.namedWindow(self.window_name)
        cv.setMouseCallback(self.window_name, self.select_point)
        print(f"Starting data collection")

    def apply_zone(self, temp_celsius, zone):
        comp = self.compensation[zone]
        return ((temp_celsius - comp["b"]) / comp["m"]) - 9

    def text_position(self, x, y, text, frame_width, frame_height):
        text_width = len(text) * 12  
        text_height = 60
        
        margin = 10
        
        # Start with default offsets from circle
        offset_x = -30  
        offset_y = 35  
        
        text_x = x + offset_x
        text_y = y + offset_y
        
        # ---------- X-axis ----------
        # RIGHT EDGE
        if text_x + text_width > frame_width - margin:
            text_x = frame_width - text_width - margin
        # LEFT EDGE
        if text_x < margin:
            text_x = margin
    
        # ---------- Y-axis ---------- 
        # TOP EDGE
        if text_y < margin:
            text_y = margin
        # BOTTOM EDGE
        if text_y + text_height > frame_height - margin:
            text_y = frame_height - text_height - margin 
            
        # Special case: if circle is very close to bottom edge
        if y > frame_height - 50:  
            text_y = max(margin, frame_height - text_height - margin)
            
        return int(text_x), int(text_y)


    def select_point(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            if self.p1 is None:
                self.p1 = (x, y)
                print(f"P1 selected at {x},{y}")
            elif self.p2 is None:
                self.p2 = (x, y)
                print(f"P2 selected at {x},{y}")
            elif self.p3 is None:
                self.p3 = (x, y)
                print(f"P3 selected at {x},{y}")
            else:
                print("Already selected 3 points")
        elif event == cv.EVENT_RBUTTONDOWN:
            if self.p3 is not None:
                print(f"Removed P3 at {self.p3}")
                self.p3 = None
            elif self.p2 is not None:
                print(f"Removed P2 at {self.p2}")
                self.p2 = None            
            elif self.p1 is not None:
                print(f"Removed P1 at {self.p1}")
                self.p1 = None
            else:
                print("No point to remove")

    def run(self):
        last_display_time = time.time()
        display_interval = 1

        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
            try : 
                if self.frame_queue.full():
                    self.frame_queue.get_nowait()
                self.frame_queue.put_nowait(frame)
            except Full:
                pass

            try :
                frame = self.frame_queue.get_nowait()
            except Empty:
                continue
            
            frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
            frame = cv.resize(frame, (720, 640), interpolation=cv.INTER_CUBIC)
            height, width = frame.shape[:2]

            if frame.dtype == np.uint16:
                clipped = np.clip(frame, minraw, maxraw)
                frame_8 = ((clipped - minraw) / (maxraw - minraw) * 255).astype(np.uint8)
                thermal_frame = cv.applyColorMap(frame_8, cv.COLORMAP_JET)

                third = width //3
                cv.line(thermal_frame, (third, 0), (third, height), (255,255,255), 1)
                cv.line(thermal_frame, (2 * third, 0), (2 * third, height), (255,255,255), 1)
                cv.putText(thermal_frame, "LEFT", (third //2 - 40, 30), cv.FONT_HERSHEY_PLAIN, 2, (255,255,255), 2)
                cv.putText(thermal_frame, "MIDDLE", (third + third //2 - 40, 30), cv.FONT_HERSHEY_PLAIN, 2, (255,255,255), 2)
                cv.putText(thermal_frame, "RIGHT", (2*third + third //2 - 40, 30), cv.FONT_HERSHEY_PLAIN, 2, (255,255,255), 2)

                point_data = [("state1", self.p1, "state1"), ("state2", self.p2, "state2"), ("state3", self.p3, "state3")]
                for point_name, point, buffer_key in point_data:
                    if point is not None:
                        x, y = point
                        temp_raw = frame[y, x]
                        temp_celsius = (temp_raw / 100) - 273.15

                        if x < width //3:
                            zone = "left"
                            point_name = "state1"
                        elif x < (2 * width //3 ):
                            zone = "middle"
                            point_name = "state2"
                        else:
                            zone = "right"
                            point_name = "state3"
                        
                        cal_temp = self.apply_zone(temp_celsius, zone)
                        self.buffers[buffer_key].append(cal_temp)
                        avg_temp = sum(self.buffers[buffer_key]) / len(self.buffers[buffer_key])
                        
                        avg_temp_data = round(avg_temp, 1)
                        self.avg_temp_send[buffer_key].append(np.float64(avg_temp_data))

                        print(f"Data : {self.avg_temp_send}")

                        # Create the text lines
                        text1 = f"{point_name}"
                        text2 = f"{avg_temp:.1f}C"
                        
                        # Get adjusted position for text to stay within frame
                        x_text, y_text = self.text_position(x, y, text1, width, height)
                        
                        # Draw the text with adjusted positions
                        cv.putText(thermal_frame, text1, (x_text, y_text), cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 2)
                        cv.putText(thermal_frame, text2, (x_text, y_text + 30), cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 2)

                        # Draw the circle
                        cv.circle(thermal_frame, (x, y), 5, (0, 0, 0), -1)
 
                if time.time() - last_display_time > display_interval:
                    last_display_time = time.time()

                cv.imshow(self.window_name, thermal_frame)
            else:
                print("Frame is not 16 bit")
                cv.imshow('Raw Frame', frame)

            if cv.waitKey(1) & 0xFF == ord('q'):
                break
            
            try:
                if cv.getWindowProperty(self.window_name, cv.WND_PROP_VISIBLE) < 1:
                    break
            except cv.error:
                break

        self.cap.release()
        cv.destroyAllWindows()


if __name__ == "__main__":
    cam = ThermalCamera()
    cam.run()