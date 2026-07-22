"""
Configuration settings for the Crowd Monitoring System
"""
import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max upload size
    
    # YOLO model settings
    YOLO_MODEL = "yolov8n.pt"
    PERSON_CLASS_ID = 0  # Class index for 'person' in COCO dataset
    
    # Heatmap configuration
    GRID_ROWS = 32  # Increased for smoother gradient
    GRID_COLS = 32  # Increased for smoother gradient
    SMOOTHING_FACTOR = 0.3  # Lower values = more smoothing
    
    # Crowd density thresholds
    LOW_THRESHOLD = 8
    MEDIUM_THRESHOLD = 12
    HIGH_THRESHOLD = 14
    
    # Zone definitions - normalized coordinates (0.0-1.0)
    ZONES = {
        'A': {
            'coords': [0.0, 0.0, 0.33, 1.0],
            'color': (0, 0, 255),  # Red (BGR)
            'count': 0,
            'density': 'low'
        },
        'B': {
            'coords': [0.33, 0.0, 0.66, 1.0],
            'color': (0, 255, 0),  # Green (BGR)
            'count': 0,
            'density': 'low'
        },
        'C': {
            'coords': [0.66, 0.0, 1.0, 1.0],
            'color': (255, 0, 0),  # Blue (BGR)
            'count': 0,
            'density': 'low'
        }
    }
    
    # Video settings
    DEFAULT_VIDEO_PATH = "uploads/videoplayback (1).mp4"
    WEBCAM_INDEX = 0
    VIDEO_FPS = 30
    FRAME_DELAY = 0.03  # For uploaded videos (~30fps)