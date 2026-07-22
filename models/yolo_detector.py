"""
YOLO detector wrapper for person detection
"""
from ultralytics import YOLO
from config import Config

class YOLODetector:
    def __init__(self, model_path=None):
        """Initialize YOLO model"""
        if model_path is None:
            model_path = Config.YOLO_MODEL
        self.model = YOLO(model_path)
        self.person_class_id = Config.PERSON_CLASS_ID
    
    def detect(self, frame):
        """
        Detect objects in the frame
        
        Args:
            frame: Input frame (numpy array)
            
        Returns:
            results: YOLO detection results
        """
        return self.model(frame)
    
    def get_person_detections(self, results):
        """
        Filter detections to only include persons
        
        Args:
            results: YOLO detection results
            
        Returns:
            list: List of person bounding boxes with coordinates
        """
        person_detections = []
        
        if results and len(results) > 0:
            for box in results[0].boxes:
                # Only process if it's a person
                if int(box.cls.item()) == self.person_class_id:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    
                    # Calculate center
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    
                    person_detections.append({
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                        'center': (cx, cy)
                    })
        
        return person_detections