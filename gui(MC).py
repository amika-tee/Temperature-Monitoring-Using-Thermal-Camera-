import sys
import os
from PySide6.QtCore import Qt, QTimer, QRegularExpression
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                               QHBoxLayout, QFrame, QPushButton, QLineEdit,
                               QMessageBox)
from PySide6.QtGui import QFontDatabase, QFont, QPainter, QColor, QRegularExpressionValidator, QImage, QPixmap

import cv2 as cv
import numpy as np
from collections import deque
from queue import Queue, Full, Empty
from SendtempTCP import ModbusClient
import time

from pymcprotocol import Type3E
import socket

# Colors
lightblue = "#DEEEF2"
black = "#102429"
lightgreen = "#91ceb3"
white = "#FFFFFF"
dark_text = '#333333'
light_text = '#666666'
green = '#479f78'
lightgray = '#F0F0F0'
gray = "#797979"
purple = '#5F489D'
pink = '#EAAEC3'
red = '#d9534f'

minraw = 26315  # --> -10 Celsius
maxraw = 42315  # --> 150 Celsius
BUF_SIZE = 2

class TempGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_fonts()
        self.setup_window()
        self.create_interface()

        self.plc_timer = QTimer()
        self.plc_timer.timeout.connect(self.send_to_plc_auto)
        self.plc_timer.start(1000)  


    def setup_fonts(self):
        self.font_family = "Arial"  # Default fallback
        
        # Try to load Poppins fonts
        font_files = [
            "Fonts/Poppins/Poppins-Regular.ttf",
            "Fonts/Poppins/Poppins-Bold.ttf"
        ]
        
        fonts_loaded = False
        for font_file in font_files:
            if os.path.exists(font_file):
                try:
                    font_id = QFontDatabase.addApplicationFont(font_file)
                    if font_id != -1:
                        fonts_loaded = True
                        print(f"Loaded font: {font_file}")
                except Exception as e:
                    print(f"Error loading {font_file}: {e}")
        
        # Check if Poppins is available
        if fonts_loaded:
            available_fonts = QFontDatabase.families()
            if "Poppins" in available_fonts:
                self.font_family = "Poppins"
                print("Using Poppins font")
            else:
                print("Poppins not found in available fonts, using Arial")

    def get_font(self, size, weight=QFont.Weight.Normal):
        """Create font with proper error handling"""
        try:
            return QFont(self.font_family, size, weight)
        except:
            return QFont("Arial", size, weight)

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def setup_window(self):
        self.setWindowTitle("Thermal Machine Detection")
        self.setMinimumSize(1850, 1020)
        self.showMaximized()
        
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {purple}, stop:1 {pink}
                );
            }}
        """)

    def create_interface(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(30, 30, 30, 30)

        left_panel = self.left_panel()
        self.right_panel_widget = self.right_panel()

        main_layout.addWidget(left_panel, 3)
        main_layout.addWidget(self.right_panel_widget, 4)
        self.setLayout(main_layout)
    
    def left_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {white};
                border-radius: 15px;
                padding: 20px;
            }}
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 30, 30)
        main_layout.setSpacing(90)
        
        # Welcome section
        title = QLabel("Welcome Back!")
        title.setFont(self.get_font(40, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {purple};")
        
        subtitle = QLabel("Thermal Machine Detection Monitor")
        subtitle.setFont(self.get_font(25, QFont.Weight.Medium))
        subtitle.setStyleSheet(f"color: {dark_text};")
        
        main_layout.addWidget(title)
        main_layout.addSpacing(-120)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(-60)

        # --- PLC SETTING ---
        PLC_panel = QFrame()
        PLC_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {lightgray};
                border-radius: 15px;
                padding: 20px;
            }}
        """)

        plc_layout = QVBoxLayout(PLC_panel)
        plc_layout.addStretch()

        plc_label_layout = QHBoxLayout()
        plc_label_layout.setContentsMargins(10, 0, 0, 0)  

        plc_label = QLabel("PLC Setting")
        plc_label.setFont(self.get_font(20, QFont.Weight.DemiBold))
        plc_label.setStyleSheet(f"color: {purple};")

        plc_label_layout.addWidget(plc_label)
        plc_label_layout.addStretch()
        plc_layout.addLayout(plc_label_layout) 

        # --- Status row ---
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(40, 0, 0, 0)  
        status_layout.setSpacing(5)

        self.status_indicator = StatusIndicator("Not connected")
        self.status_label = QLabel("Not Connected")
        self.status_label.setFont(self.get_font(16, QFont.Weight.DemiBold))
        self.status_label.setStyleSheet(f"color: {red};")

        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        plc_label_layout.addLayout(status_layout)

        # --- IP row ---
        ip_layout = QHBoxLayout()
        ip_layout.setContentsMargins(50, 0, 0, 0)  
        ip_layout.setSpacing(10)

        ip_label = QLabel("IP Address      ")
        ip_label.setFont(self.get_font(18, QFont.Weight.Medium))
        ip_label.setStyleSheet(f"color: {dark_text};")

        ip_input = QLineEdit()
        ip_input.setPlaceholderText("Enter IP address")
        ip_input.setFixedWidth(300)
        ip_input.setFont(self.get_font(16))
        ip_input.setStyleSheet(f"""
            QLineEdit {{
                border: 3px solid #cccccc;
                border-radius: 8px;
                padding: 6px 10px; 
                color: #333333;
                background-color: {white};
            }}
            QLineEdit:focus {{
                border: 3px solid {pink};
                background-color: #ffffff;
            }}
        """)

        # Partial IP validator
        ip_partial_regex = QRegularExpression(r"^(\d{1,3})(\.(\d{1,3})){0,3}$")
        validator = QRegularExpressionValidator(ip_partial_regex)
        ip_input.setValidator(validator)

        ip_input.textEdited.connect(self.auto_insert_dot)
        self.ip_input = ip_input

        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(ip_input)
        ip_layout.addStretch()
        plc_layout.addLayout(ip_layout)

        # --- Port row ---
        port_layout = QHBoxLayout()
        port_layout.setContentsMargins(50, 0, 0, 0)  
        port_layout.setSpacing(10)

        port_label = QLabel("Port                  ")
        port_label.setFont(self.get_font(18, QFont.Weight.Medium))
        port_label.setStyleSheet(f"color: {dark_text};")

        port_input = QLineEdit()
        port_input.setPlaceholderText("Enter Port")
        port_input.setFixedWidth(300)
        port_input.setFont(self.get_font(16))
        port_input.setStyleSheet(f"""
                                QLineEdit {{
                                    border: 3px solid #cccccc;
                                    border-radius: 8px;
                                    padding: 6px 10px; 
                                    color: #333333;
                                    background-color: {white};
                                }}
                                QLineEdit:focus {{
                                    border: 3px solid {pink};
                                    background-color: #ffffff;
                                }}
                            """)
        self.port_input = port_input

        port_layout.addWidget(port_label)
        port_layout.addWidget(port_input)
        port_layout.addStretch()
        plc_layout.addLayout(port_layout)
        plc_layout.addSpacing(10)

        # Register zone
        registers_layout = QHBoxLayout()
        registers_layout.setSpacing(2) 

        def create_register(name, placeholder):
            layout = QVBoxLayout()
            layout.setSpacing(0)
            
            label = QLabel(name)
            label.setFont(self.get_font(16, QFont.Weight.Medium))
            label.setStyleSheet(f"color: {dark_text};")
            
            input_field = QLineEdit()
            input_field.setPlaceholderText(placeholder)
            input_field.setFixedWidth(120)
            input_field.setFont(self.get_font(16))
            input_field.setStyleSheet(f"""
                QLineEdit {{
                    border: 3px solid #cccccc;
                    border-radius: 8px;
                    padding: 6px 10px; 
                    color: #333333;
                    background-color: {white};
                }}
                QLineEdit:focus {{
                    border: 3px solid {pink};
                    background-color: #ffffff;
                }}
            """)
            
            layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignHCenter)
            layout.addWidget(input_field, alignment=Qt.AlignmentFlag.AlignHCenter)
            layout.addStretch()
            
            return layout, input_field

        register1_layout, self.register1_input = create_register("Device 1", "State 1")
        register2_layout, self.register2_input = create_register("Device 2", "State 2")
        register3_layout, self.register3_input = create_register("Device 3", "State 3")

        registers_layout.addLayout(register1_layout)
        registers_layout.addLayout(register2_layout)
        registers_layout.addLayout(register3_layout)

        description_label = QLabel("Device ใส่เฉพาะตัวเลข เช่น D100 = 100")  # “Numbers only”
        description_label.setFont(self.get_font(12, QFont.Weight.Medium))
        description_label.setStyleSheet(f"color: {dark_text};")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.rpi_ip_label = QLabel(f"Raspberry Pi IP: {self.get_local_ip()}")
        self.rpi_ip_label.setFont(self.get_font(14))
        self.rpi_ip_label.setStyleSheet(f"color: {dark_text};")

        plc_layout.addLayout(registers_layout)
        plc_layout.addWidget(description_label, alignment=Qt.AlignmentFlag.AlignLeft)
        plc_layout.addSpacing(10)
        plc_layout.addWidget(self.rpi_ip_label, alignment=Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(PLC_panel)
        main_layout.addSpacing(-40)

        # Button
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(120, 0, 0, 0)  
        button_layout.setSpacing(40)

        connect_button = QPushButton("Connect")
        connect_button.setFixedHeight(40)
        connect_button.setFixedWidth(150)
        connect_button.setFont(self.get_font(14, QFont.Weight.Medium))
        connect_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {purple};
                color: white;
                border-radius: 20px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {pink};
            }}
            QPushButton:pressed {{
                background-color: {gray};
            }}
        """)

        disconnect_button = QPushButton("Disconnect")
        disconnect_button.setFixedHeight(40)
        disconnect_button.setFixedWidth(150)
        disconnect_button.setFont(self.get_font(14, QFont.Weight.Medium))
        disconnect_button.setStyleSheet(f"""
                                        QPushButton {{
                                            background-color: {gray};
                                            color: {white};
                                            border-radius: 20px;
                                            padding: 6px 12px;
                                        }}
                                        QPushButton:hover {{
                                            background-color: {pink};
                                        }}
                                        QPushButton:pressed {{
                                            background-color: {gray};
                                        }}
                                    """)

        connect_button.clicked.connect(self.connect_to_plc)
        disconnect_button.clicked.connect(self.disconnect_from_plc)

        button_layout.addWidget(connect_button)
        button_layout.addSpacing(100)
        button_layout.addWidget(disconnect_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        panel.setLayout(main_layout)
        return panel

    def right_panel(self):
        return ThermalCameraPanel()

    def auto_insert_dot(self, text: str):
        if len(text) < getattr(self, "_last_len", 0):
            self._last_len = len(text)
            return
        parts = text.split(".")
        if len(parts) < 4:
            last = parts[-1]

            if last.isdigit() and len(last) == 3 and not text.endswith("."):
                self.ip_input.setText(text + ".")
                self.ip_input.setCursorPosition(len(self.ip_input.text()))
        self._last_len = len(self.ip_input.text())

    def connect_to_plc(self):
        ip = self.ip_input.text().strip()
        port_text = self.port_input.text().strip()
        if not ip or not port_text:
            QMessageBox.warning(self, "Warning", "IP and Port must be filled!")
            return
        try:
            port = int(port_text)
        except ValueError:
            QMessageBox.warning(self, "Warning", "Port must be a number!")
            return

        if hasattr(self, 'plc_client') and self.plc_client:
            self.plc_client.close()

        self.plc_client = Type3E()

        try: 
            self.plc_client.connect(ip, port)
            self.update_plc_status(True)
        except:
            self.update_plc_status(False)
            QMessageBox.warning(self, "Error", "Can not connect PLC")
            self.plc_client = None

    def disconnect_from_plc(self):
        if hasattr(self, 'plc_client') and self.plc_client:
            self.plc_client.close()
            self.plc_client = None
        self.update_plc_status(False)

    def update_plc_status(self, connected: bool):
        if connected:
            self.status_indicator.status = "connected"
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet(f"color: {green};")
        else:
            self.status_indicator.status = "Not connected"
            self.status_label.setText("Not Connected")
            self.status_label.setStyleSheet(f"color: {red};")
        self.status_indicator.update()

    def send_to_plc_auto(self):
        if not hasattr(self, 'plc_client') or not self.plc_client:
            return  # not connected

        panel = self.right_panel_widget
        data_to_send = {}
        for key in ["state1", "state2", "state3"]:
            if panel.avg_temp_send[key]:
                data_to_send[key] = panel.avg_temp_send[key][-1]

        if not data_to_send:
            return  # nothing to send yet
        
        try:
            reg1 = self.register1_input.text().strip()
            reg2 = self.register2_input.text().strip()
            reg3 = self.register3_input.text().strip()

            register_map = {
                "state1": reg1 if reg1 else "D100",
                "state2": reg2 if reg2 else "D101",
                "state3": reg3 if reg3 else "D102",
            }

            values = []
            regs = []
            for key in ["state1", "state2", "state3"]:
                regs.append(register_map[key])
                if key in data_to_send:
                    val = data_to_send[key]
                    float_val = float(f"{val:.2f}")
                    int_val = int(float_val * 100)
                    values.append(int_val)
                else:
                    values.append(0)

            for reg, val in zip(regs, values):
                if reg: 
                    self.plc_client.batchwrite_wordunits(f"D{reg}", [val])

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error sending data: {e}")
            self.update_plc_status(False)






#####################################################################################################################################################
#RIGHT PANEL
class ThermalCameraPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {white};
                border-radius: 15px;
            }}
        """)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 60, 30, 30)

        self.title_label = QLabel("Livestream")
        self.title_label.setFont(QFont("Poppins", 35, QFont.Weight.Bold))  # You can use self.get_font if in TempGUI
        self.title_label.setStyleSheet(f"color: {dark_text};")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)
        self.layout.addSpacing(20)

        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setStyleSheet("border: 1px solid #ccc; border-radius: 10px;")
        self.layout.addWidget(self.camera_label)
        self.layout.addStretch()
        self.setLayout(self.layout)
        
        self.camera_label.setMouseTracking(True)
        self.camera_label.mousePressEvent = self.handle_mouse_click

        self.clear_button = QPushButton("Clear Points")
        self.clear_button.setFont(QFont("Poppins", 14, QFont.Weight.Medium))
        self.clear_button.setFixedHeight(40)
        self.clear_button.setFixedWidth(150)
        self.clear_button.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {purple};
                                color: {white};
                                border-radius: 20px;
                                padding: 6px 12px;
                            }}
                            QPushButton:hover {{
                                background-color: {pink};
                            }}
                            QPushButton:pressed {{
                                background-color: {gray};
                            }}
                            """)
        self.clear_button.clicked.connect(self.clear_points)
        self.layout.addWidget(self.clear_button, alignment=Qt.AlignCenter | Qt.AlignTop)

        # --- Thermal camera setup ---
        self.cap = cv.VideoCapture(0, cv.CAP_V4L2)
        self.cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('Y','1','6',' '))
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 160)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 120)
        self.cap.set(cv.CAP_PROP_FPS, 9)
        self.cap.set(cv.CAP_PROP_CONVERT_RGB, 0)

        self.p1 = self.p2 = self.p3 = None
        self.buffers = {
            "state1": deque(maxlen=5),
            "state2": deque(maxlen=5),
            "state3": deque(maxlen=5),
        }
        self.avg_temp_send = {"state1": [], "state2": [], "state3": []}
        self.compensation = {
            "left": {"m": 0.752, "b": 5.093},
            "middle": {"m": 0.728, "b": 5.142},
            "right": {"m": 0.704, "b": 5.190},
        }

        self.plc_client = ModbusClient("192.168.3.40")

        self.frame_queue = Queue(BUF_SIZE)
        self.last_send_time = time.time()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(110)  # ~9 FPS

    def apply_zone(self, temp_celsius, zone):
        comp = self.compensation[zone]
        return ((temp_celsius - comp["b"]) / comp["m"]) - 9

    def text_position(self, x, y, text, frame_width, frame_height):
        text_width = len(text) * 12
        text_height = 60
        margin = 10
        offset_x, offset_y = -30, 35
        text_x = x + offset_x
        text_y = y + offset_y
        if text_x + text_width > frame_width - margin:
            text_x = frame_width - text_width - margin
        if text_x < margin:
            text_x = margin
        if text_y < margin:
            text_y = margin
        if text_y + text_height > frame_height - margin:
            text_y = frame_height - text_height - margin
        if y > frame_height - 50:
            text_y = max(margin, frame_height - text_height - margin)
        return int(text_x), int(text_y)

    def handle_mouse_click(self, event):
        if self.camera_label.pixmap() is None:
            return

        if all([self.p1, self.p2, self.p3]):
            print("Maximum of 3 points reached. Press Clear to reset.")
            return

        mapped = self.map_label_click_to_image_coords(event)
        if mapped is None:
            return

        x, y = mapped

        if event.button() == Qt.LeftButton:
            if self.p1 is None:
                self.p1 = (x, y)
            elif self.p2 is None:
                self.p2 = (x, y)
            elif self.p3 is None:
                self.p3 = (x, y)

    def map_label_click_to_image_coords(self, event):
        pm = self.camera_label.pixmap()
        if pm is None:
            return None

        click_x = int(event.position().x())
        click_y = int(event.position().y())

        label_w = self.camera_label.width()
        label_h = self.camera_label.height()
        pixmap_w = pm.width()
        pixmap_h = pm.height()

        scale = min(label_w / pixmap_w, label_h / pixmap_h)
        disp_w = int(pixmap_w * scale)
        disp_h = int(pixmap_h * scale)

        offset_x = (label_w - disp_w) // 2
        offset_y = (label_h - disp_h) // 2

        if not (offset_x <= click_x <= offset_x + disp_w and offset_y <= click_y <= offset_y + disp_h):
            return None

        img_x = int((click_x - offset_x) * (pixmap_w / disp_w))
        img_y = int((click_y - offset_y) * (pixmap_h / disp_h))

        return max(0, min(img_x, pixmap_w-1)), max(0, min(img_y, pixmap_h-1))

    def clear_points(self):
        self.p1 = self.p2 = self.p3 = None
        for key in self.buffers:
            self.buffers[key].clear()
        for key in self.avg_temp_send:
            self.avg_temp_send[key].clear()

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()

            # Release camera
            self.cap.release()
            self.cap = None

            # Show error popup
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Camera Error")
            msg.setText("Camera stream stopped. Please reconnect the camera.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
            return 
        try:
            if self.frame_queue.full():
                self.frame_queue.get_nowait()
            self.frame_queue.put_nowait(frame)
        except Full:
            pass

        try:
            frame = self.frame_queue.get_nowait()
        except Empty:
            return

        frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)
        frame = cv.resize(frame, (720, 640), interpolation=cv.INTER_CUBIC)
        height, width = frame.shape[:2]

        if frame.dtype == np.uint16:
            clipped = np.clip(frame, minraw, maxraw)
            frame_8 = ((clipped - minraw) / (maxraw - minraw) * 255).astype(np.uint8)
            thermal_frame = cv.applyColorMap(frame_8, cv.COLORMAP_JET)

            third = width // 3
            cv.line(thermal_frame, (third,0),(third,height),(255,255,255),1)
            cv.line(thermal_frame,(2*third,0),(2*third,height),(255,255,255),1)
            cv.putText(thermal_frame,"LEFT",(third//2-40,30),cv.FONT_HERSHEY_PLAIN,2,(255,255,255),2)
            cv.putText(thermal_frame,"MIDDLE",(third+third//2-40,30),cv.FONT_HERSHEY_PLAIN,2,(255,255,255),2)
            cv.putText(thermal_frame,"RIGHT",(2*third+third//2-40,30),cv.FONT_HERSHEY_PLAIN,2,(255,255,255),2)

            points_data = [("state1", self.p1, "state1"),
                        ("state2", self.p2, "state2"),
                        ("state3", self.p3, "state3")]

            for point_name, point, buffer_key in points_data:
                if point is not None:
                    x, y = point
                    temp_raw = frame[y, x]
                    temp_celsius = (temp_raw / 100) - 273.15

                    if x < width // 3:
                        zone = "left"
                    elif x < 2 * width // 3:
                        zone = "middle"
                    else:
                        zone = "right"

                    cal_temp = self.apply_zone(temp_celsius, zone)

                    self.buffers[buffer_key].append(cal_temp)
                    avg_temp = sum(self.buffers[buffer_key]) / len(self.buffers[buffer_key])
                    self.avg_temp_send[buffer_key].append(round(avg_temp, 1))

                    text1 = f"{point_name}"       
                    text2 = f"{avg_temp:.2f}C"
                    x_text, y_text = self.text_position(x, y, text1, width, height)
                    cv.putText(thermal_frame, text1, (x_text, y_text),
                            cv.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
                    cv.putText(thermal_frame, text2, (x_text, y_text + 30),
                            cv.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)
                    cv.circle(thermal_frame, (x, y), 5, (0, 0, 0), -1)

            thermal_frame_rgb = cv.cvtColor(thermal_frame, cv.COLOR_BGR2RGB)
            h,w,ch = thermal_frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(thermal_frame_rgb.data,w,h,bytes_per_line,QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))













#####################################################################################################################################################
class StatusIndicator(QWidget):
    def __init__(self, status="Not connected"):
        super().__init__()
        self.status = status
        self.setFixedSize(20, 20)
        
        # Pulsing animation
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.update_pulse)
        self.pulse_timer.start(50) 
        self.pulse_alpha = 1.0
        self.pulse_direction = -0.02
    
    def update_pulse(self):
        self.pulse_alpha += self.pulse_direction
        if self.pulse_alpha <= 0.3 or self.pulse_alpha >= 1.0:
            self.pulse_direction *= -1
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = "#5cb85c" if self.status == "connected" else "#d9534f"
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw pulsing circle
        painter.setOpacity(self.pulse_alpha)
        painter.drawEllipse(self.rect())

    def set_status(self, connected: bool):
        self.status = "connected" if connected else "Not connected"
        self.update() 



def main():
    app = QApplication(sys.argv)
    try:
        window = TempGUI()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()