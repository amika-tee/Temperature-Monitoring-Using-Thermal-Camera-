import cv2 as cv
import numpy as np

class ThermalCamera:
    def __init__(self):
        # Camera parameters (your calibrated values)
        self.camera_matrix = np.array([[104.65403680863373, 0.0, 79.21313258957062],
                                      [0.0, 104.48251047202757, 55.689070170705634],
                                      [0.0, 0.0, 1.0]])
        
        self.distortion_coeff = np.array([[-0.39758308581607127,
                                          0.18068641745671193,
                                          0.004626461618389028,
                                          0.004197358204037882,
                                          -0.03381399499591463]])
        
        self.new_camera_matrix = np.array([[66.54581451416016, 0.0, 81.92717558174809],
                                          [0.0, 64.58526611328125, 56.23740168870427],
                                          [0.0, 0.0, 1.0]])
        
        # Initialize camera with Lepton 3.1 R settings
        self.cap = cv.VideoCapture(0, cv.CAP_V4L2)
        self.cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('Y', '1', '6', ' '))
        self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 160)
        self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 120)
        self.cap.set(cv.CAP_PROP_FPS, 9)
        self.cap.set(cv.CAP_PROP_CONVERT_RGB, 0)
        
        # Pre-compute undistortion maps for 160x120 resolution
        self.map1, self.map2 = self.create_undistortion_maps()
        
        # Lepton 3.1 R specific parameters
        self.thermal_resolution = 0.05  # 50mK resolution
        self.kelvin_offset = 27315      # Convert to Kelvin (273.15 * 100)
        
        print("FLIR Lepton 3.1 R initialized successfully!")
        print(f"Resolution: {self.cap.get(cv.CAP_PROP_FRAME_WIDTH)}x{self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)}")
        print(f"FPS: {self.cap.get(cv.CAP_PROP_FPS)}")
    
    def create_undistortion_maps(self):
        """Pre-compute undistortion maps for 160x120 resolution"""
        map1, map2 = cv.initUndistortRectifyMap(
            self.camera_matrix, self.distortion_coeff, None, 
            self.new_camera_matrix, (160, 120), cv.CV_16SC2)
        return map1, map2
    
    def raw_to_temperature(self, raw_frame):
        """Convert raw Y16 values to temperature in Celsius using your calibration"""
        # Your specific calibration: minraw = 26315 (-10°C), maxraw = 47315 (200°C)
        minraw = 26315  # -10 celsius
        maxraw = 47315  # 200 celsius
        
        # Linear interpolation to get temperature in Celsius
        temperature_celsius = ((raw_frame - minraw) / (maxraw - minraw)) * (200 - (-10)) + (-10)
        return temperature_celsius
    
    def split_thermal_frame(self, raw_frame, show_regions=False):
        """Split thermal frame into 3 parts and return temperature data"""
        h, w = raw_frame.shape
        third_w = w // 3
        
        # Split into three regions (work with raw data)
        left_region = raw_frame[:, 0:third_w]
        middle_region = raw_frame[:, third_w:2*third_w]
        right_region = raw_frame[:, 2*third_w:]
        
        if show_regions:
            # Create visualization using your display method
            display_frame, _ = self.thermal_to_display(raw_frame)
            
            # Draw region boundaries
            cv.line(display_frame, (third_w, 0), (third_w, h), (255, 255, 255), 1)
            cv.line(display_frame, (2*third_w, 0), (2*third_w, h), (255, 255, 255), 1)
            
            # Add labels
            cv.putText(display_frame, 'L', (third_w//2-5, 15), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv.putText(display_frame, 'M', (third_w + third_w//2-5, 15), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv.putText(display_frame, 'R', (2*third_w + third_w//2-5, 15), cv.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Resize for better visibility
            display_frame = cv.resize(display_frame, (480, 360), interpolation=cv.INTER_NEAREST)
            cv.imshow('Thermal Regions', display_frame)
        
        return left_region, middle_region, right_region
    
    def thermal_to_display(self, raw_frame):
        """Convert raw thermal data to colored display frame using your method"""
        minraw = 26315  # -10 celsius
        maxraw = 47315  # 200 celsius
        
        # Your exact conversion method
        clipped = np.clip(raw_frame, minraw, maxraw)
        frame_8 = ((clipped - minraw) / (maxraw - minraw) * 255).astype(np.uint8)
        thermal_frame = cv.applyColorMap(frame_8, cv.COLORMAP_JET)
        return thermal_frame, frame_8
    
    def calculate_thermal_stats(self, raw_region, region_name=""):
        """Calculate temperature statistics for a thermal region using raw values"""
        # Convert raw values to temperature for statistics
        temp_region = self.raw_to_temperature(raw_region.astype(np.float32))
        
        mean_temp = np.mean(temp_region)
        min_temp = np.min(temp_region)
        max_temp = np.max(temp_region)
        std_temp = np.std(temp_region)
        
        stats = {
            'region': region_name,
            'mean': mean_temp,
            'min': min_temp,
            'max': max_temp,
            'std': std_temp,
            'pixels': raw_region.size
        }
        
        return stats
    
    def compare_thermal_regions(self, left_stats, middle_stats, right_stats):
        """Compare temperature statistics between regions"""
        print(f"\n=== Thermal Analysis (°C) ===")
        print(f"{'Region':<8} {'Mean':<8} {'Min':<8} {'Max':<8} {'Std':<8} {'Pixels':<8}")
        print("-" * 55)
        
        for stats in [left_stats, middle_stats, right_stats]:
            print(f"{stats['region']:<8} {stats['mean']:<8.2f} {stats['min']:<8.2f} "
                  f"{stats['max']:<8.2f} {stats['std']:<8.2f} {stats['pixels']:<8}")
        
        # Calculate error relative to middle region
        left_error = abs(left_stats['mean'] - middle_stats['mean'])
        right_error = abs(right_stats['mean'] - middle_stats['mean'])
        
        print(f"\nTemperature Error vs Middle Region:")
        print(f"Left region error:  {left_error:.3f}°C")
        print(f"Right region error: {right_error:.3f}°C")
        print(f"Total edge error:   {(left_error + right_error)/2:.3f}°C")
        
        return left_error, right_error
    
    def run_analysis(self):
        """Main analysis loop"""
        frame_count = 0
        show_analysis = True
        show_regions = True
        
        print("\nControls:")
        print("'q' - Quit")
        print("'s' - Save current frame")
        print("'a' - Toggle analysis")
        print("'r' - Toggle region visualization")
        print("'c' - Toggle lens correction")
        
        apply_correction = True
        
        while True:
            ret, raw_frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                break
            
            frame_count += 1
            
            # Work with raw 16-bit data
            raw_frame = raw_frame.astype(np.uint16)
            
            # Apply lens distortion correction if enabled
            if apply_correction:
                corrected_frame = cv.remap(raw_frame, self.map1, self.map2, cv.INTER_LINEAR)
                display_title = "Thermal (Corrected)"
            else:
                corrected_frame = raw_frame
                display_title = "Thermal (Original)"
            
            # Create display version using your exact method
            colored_frame, frame_8 = self.thermal_to_display(corrected_frame)
            
            # Resize for better visibility
            colored_frame = cv.resize(colored_frame, (480, 360), interpolation=cv.INTER_NEAREST)
            
            # Convert to temperature for display info
            temp_frame = self.raw_to_temperature(corrected_frame.astype(np.float32))
            min_temp, max_temp = np.min(temp_frame), np.max(temp_frame)
            
            # Add temperature range info
            cv.putText(colored_frame, f"Min: {min_temp:.1f}C", (10, 20), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv.putText(colored_frame, f"Max: {max_temp:.1f}C", (10, 40), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv.putText(colored_frame, f"Range: -10 to 200C", (10, 60), 
                      cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv.putText(colored_frame, f"Correction: {'ON' if apply_correction else 'OFF'}", 
                      (10, 340), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if apply_correction else (0, 0, 255), 1)
            
            cv.imshow(display_title, colored_frame)
            
            # Perform region analysis every 30 frames
            if show_analysis and frame_count % 30 == 0:
                left, middle, right = self.split_thermal_frame(corrected_frame, show_regions)
                
                left_stats = self.calculate_thermal_stats(left, "LEFT")
                middle_stats = self.calculate_thermal_stats(middle, "MIDDLE") 
                right_stats = self.calculate_thermal_stats(right, "RIGHT")
                
                self.compare_thermal_regions(left_stats, middle_stats, right_stats)
            
            # Handle key presses
            key = cv.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save both raw thermal data and visualization
                np.save(f'thermal_raw_frame_{frame_count}.npy', corrected_frame)
                cv.imwrite(f'thermal_visual_frame_{frame_count}.jpg', colored_frame)
                print(f"Frame {frame_count} saved! Raw range: {np.min(corrected_frame)} to {np.max(corrected_frame)}")
            elif key == ord('a'):
                show_analysis = not show_analysis
                print(f"Analysis {'enabled' if show_analysis else 'disabled'}")
            elif key == ord('r'):
                show_regions = not show_regions
                print(f"Region visualization {'enabled' if show_regions else 'disabled'}")
            elif key == ord('c'):
                apply_correction = not apply_correction
                print(f"Lens correction {'enabled' if apply_correction else 'disabled'}")
        
        self.cap.release()
        cv.destroyAllWindows()

# Usage
if __name__ == "__main__":
    try:
        thermal_cam = ThermalCamera()
        thermal_cam.run_analysis()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your FLIR Lepton 3.1 R is connected and accessible via V4L2")