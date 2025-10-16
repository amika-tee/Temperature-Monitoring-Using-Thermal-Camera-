import sys
import os
from PySide6.QtCore import Qt, QTimer, QRegularExpression
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                               QHBoxLayout, QFrame, QPushButton, QLineEdit)
from PySide6.QtGui import QFontDatabase, QFont, QPainter, QColor, QRegularExpressionValidator

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

class TempGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_fonts()
        self.setup_window()
        self.create_interface()

    def setup_fonts(self):
        """Safely load fonts with fallback"""
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
            # Fallback to system default
            return QFont("Arial", size, weight)

    def setup_window(self):
        self.setWindowTitle("Thermal Machine Detection")
        self.setMinimumSize(1850, 1000)
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
        right_panel = self.right_panel()

        main_layout.addWidget(left_panel, 3)
        main_layout.addWidget(right_panel, 4)
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
        main_layout.setContentsMargins(20, 50, 30, 30)
        main_layout.setSpacing(90)
        
        # Welcome section
        title = QLabel("Welcome Back!")
        title.setFont(self.get_font(40, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {purple};")
        
        subtitle = QLabel("Thermal Machine Detection Monitor")
        subtitle.setFont(self.get_font(25, QFont.Weight.Medium))
        subtitle.setStyleSheet(f"color: {dark_text};")
        
        main_layout.addWidget(title)
        main_layout.addSpacing(-110)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(-70)

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

        status_indicator = StatusIndicator("connected")
        status_label = QLabel("Connected")
        status_label.setFont(self.get_font(16, QFont.Weight.DemiBold))
        status_label.setStyleSheet("color: #5cb85c;")

        status_layout.addWidget(status_indicator)
        status_layout.addWidget(status_label)
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
                background-color: {lightgray};
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
                background-color: {lightgray};
            }}
            QLineEdit:focus {{
                border: 3px solid {pink};
                background-color: #ffffff;
            }}
        """)

        port_layout.addWidget(port_label)
        port_layout.addWidget(port_input)
        port_layout.addStretch()
        plc_layout.addLayout(port_layout)
        plc_layout.addSpacing(10)

        # Register zone
        registers_layout = QHBoxLayout()
        registers_layout.setSpacing(5) 

        def create_register(name):
            layout = QVBoxLayout()
            layout.setSpacing(0)
            
            label = QLabel(name)
            label.setFont(self.get_font(16, QFont.Weight.Medium))
            label.setStyleSheet(f"color: {dark_text};")
            
            input_field = QLineEdit()
            input_field.setPlaceholderText("Send")
            input_field.setFixedWidth(120)
            input_field.setFont(self.get_font(16))
            input_field.setStyleSheet(f"""
                QLineEdit {{
                    border: 3px solid #cccccc;
                    border-radius: 8px;
                    padding: 6px 10px; 
                    color: #333333;
                    background-color: {lightgray};
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

        register1_layout, register1_input = create_register("Register 1")
        register2_layout, register2_input = create_register("Register 2")
        register3_layout, register3_input = create_register("Register 3")

        registers_layout.addLayout(register1_layout)
        registers_layout.addLayout(register2_layout)
        registers_layout.addLayout(register3_layout)

        plc_layout.addStretch()
        plc_layout.addLayout(registers_layout)
        plc_layout.addSpacing(10)
        main_layout.addWidget(PLC_panel)
        main_layout.addSpacing(-60)

        # Button
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(120, 0, 0, 0)  
        button_layout.setSpacing(10)

        connect_button = QPushButton("Connect")
        connect_button.setFixedHeight(40)
        connect_button.setFixedWidth(150)
        connect_button.setFont(self.get_font(13, QFont.Weight.Medium))
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
        disconnect_button.setFont(self.get_font(13, QFont.Weight.Medium))
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

        button_layout.addWidget(connect_button)
        button_layout.addSpacing(100)
        button_layout.addWidget(disconnect_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        panel.setLayout(main_layout)
        return panel
        
    def right_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {white};
                border-radius: 15px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def auto_insert_dot(self, text: str):
        # If deleting, don't interfere
        if len(text) < getattr(self, "_last_len", 0):
            self._last_len = len(text)
            return

        parts = text.split(".")

        if len(parts) < 4:
            last = parts[-1]

            # Auto-insert dot only when typing forward
            if last.isdigit() and len(last) == 3 and not text.endswith("."):
                self.ip_input.setText(text + ".")
                self.ip_input.setCursorPosition(len(self.ip_input.text()))

        # Remember current length for next check
        self._last_len = len(self.ip_input.text())

class StatusIndicator(QWidget):
    def __init__(self, status="connected"):
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
        
        # Choose color based on status
        color = "#5cb85c" if self.status == "connected" else "#d9534f"
        painter.setBrush(QColor(color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw pulsing circle
        painter.setOpacity(self.pulse_alpha)
        painter.drawEllipse(self.rect())

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