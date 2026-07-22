"""
Video processing and frame generation
"""
import cv2
import numpy as np
import time
import os
from config import Config

class VideoProcessor:
    def __init__(self, detector, zone_manager, heatmap_generator):
        """
        Initialize video processor
        
        Args:
            detector: YOLO detector instance
            zone_manager: Zone manager instance
            heatmap_generator: Heatmap generator instance
        """
        self.detector = detector
        self.zone_manager = zone_manager
        self.heatmap_generator = heatmap_generator
        
        self.using_webcam = True
        self.video_path = Config.DEFAULT_VIDEO_PATH
        self.cap = cv2.VideoCapture(Config.WEBCAM_INDEX)
        self.total_people_count = 0
        self.last_update_time = time.time()
    
    def set_video_source(self, use_webcam=True, video_path=None):
        """
        Set video source (webcam or file)
        
        Args:
            use_webcam: Boolean, True for webcam, False for video file
            video_path: Path to video file (if not using webcam)
        """
        self.using_webcam = use_webcam
        
        if not use_webcam and video_path:
            self.video_path = video_path
        
        # Release current capture and open new source
        if self.cap is not None:
            self.cap.release()
        
        if use_webcam:
            self.cap = cv2.VideoCapture(Config.WEBCAM_INDEX)
        else:
            self.cap = cv2.VideoCapture(self.video_path)
    
    def process_frame(self, frame):
        """
        Process a single frame
        
        Args:
            frame: Input frame
            
        Returns:
            processed_frame: Frame with annotations
            people_count: Number of people detected
        """
        height, width, _ = frame.shape
        
        current_time = time.time()
        if current_time - self.last_update_time > 0.1:
            # Reset counts
            self.heatmap_generator.reset_grid()
            self.zone_manager.reset_counts()
            
            # Detect objects
            results = self.detector.detect(frame)
            person_detections = self.detector.get_person_detections(results)
            
            # Update people count
            self.total_people_count = len(person_detections)
            
            # Process each detected person
            for i, detection in enumerate(person_detections):
                bbox = detection['bbox']
                cx, cy = detection['center']
                
                # Add to zone
                self.zone_manager.add_person_to_zone(cx, cy, width, height)
                
                # Add to heatmap grid
                self.heatmap_generator.add_person_to_grid(cx, cy, height, width)
                
                # Draw on frame
                cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                cv2.putText(frame, f"Person {i+1}", (bbox[0], bbox[1] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Calculate zone densities
            self.zone_manager.calculate_densities()
            
            # Update smoothed grid
            self.heatmap_generator.update_smoothed_grid()
            
            self.last_update_time = current_time
        
        # Add annotations to frame
        frame = self._add_annotations(frame, width, height)
        
        return frame, self.total_people_count
    
    def _add_annotations(self, frame, width, height):
        """Add visual annotations to frame"""
        # Add people count
        cv2.putText(frame, f"Total People: {self.total_people_count}", 
                   (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Draw zones
        zones = self.zone_manager.get_zones()
        for zone_id, zone_info in zones.items():
            x1 = int(zone_info['coords'][0] * width)
            y1 = int(zone_info['coords'][1] * height)
            x2 = int(zone_info['coords'][2] * width)
            y2 = int(zone_info['coords'][3] * height)
            
            # Get density color
            if zone_info['density'] == 'high':
                density_color = (0, 0, 255)
            elif zone_info['density'] == 'medium':
                density_color = (0, 165, 255)
            else:
                density_color = (0, 255, 0)
            
            # Draw translucent overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, y1), (x2, y2), zone_info['color'], -1)
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
            
            # Draw border
            cv2.rectangle(frame, (x1, y1), (x2, y2), zone_info['color'], 2)
            
            # Add label
            label_bg_y1 = y1 + 5
            label_bg_y2 = y1 + 65
            label_bg_x1 = x1 + 5
            label_bg_x2 = x1 + 140
            
            overlay = frame.copy()
            cv2.rectangle(overlay, (label_bg_x1, label_bg_y1), (label_bg_x2, label_bg_y2), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            cv2.putText(frame, f"Zone {zone_id}", (label_bg_x1 + 5, label_bg_y1 + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"Count: {zone_info['count']}", (label_bg_x1 + 5, label_bg_y1 + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f"{zone_info['density'].capitalize()}", (label_bg_x1 + 5, label_bg_y1 + 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, density_color, 2)
        
        # Add source indicator
        source_text = "Source: Webcam" if self.using_webcam else f"Source: Video - {os.path.basename(self.video_path)}"
        cv2.putText(frame, source_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, source_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        return frame
    
    def generate_frames(self):
        """Generator for video frames"""
        # Set up video source
        if not self.using_webcam and self.video_path:
            if self.cap is not None:
                self.cap.release()
            self.cap = cv2.VideoCapture(self.video_path)
        
        # Check if video source is valid
        if not self.cap.isOpened():
            if self.using_webcam:
                self.cap = cv2.VideoCapture(Config.WEBCAM_INDEX)
                if not self.cap.isOpened():
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + 
                           cv2.imencode('.jpg', np.zeros((480, 640, 3), dtype=np.uint8))[1].tobytes() + 
                           b'\r\n')
                    return
            else:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + 
                       cv2.imencode('.jpg', np.zeros((480, 640, 3), dtype=np.uint8))[1].tobytes() + 
                       b'\r\n')
                return
        
        while True:
            success, frame = self.cap.read()
            
            # If end of video, loop back for uploaded videos
            if not success:
                if not self.using_webcam and self.video_path:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    success, frame = self.cap.read()
                    if not success:
                        break
                else:
                    continue
            
            # Process frame
            frame, _ = self.process_frame(frame)
            
            # Convert to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Add delay for uploaded videos
            if not self.using_webcam:
                time.sleep(Config.FRAME_DELAY)
    
    def get_people_count(self):
        """Get current people count"""
        return self.total_people_count
    
    def cleanup(self):
        """Release video capture resources"""
        if self.cap is not None:
            self.cap.release()