"""
Main Flask application entry point
"""
from flask import Flask
import os
from config import Config
from models import YOLODetector
from utils import HeatmapGenerator, ZoneManager, VideoProcessor
from routes.main_routes import register_main_routes
from routes.video_routes import register_video_routes
from routes.api_routes import register_api_routes

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Create uploads directory if it doesn't exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Initialize components
detector = YOLODetector()
heatmap_generator = HeatmapGenerator()
zone_manager = ZoneManager()
video_processor = VideoProcessor(detector, zone_manager, heatmap_generator)

# Register routes
register_main_routes(app, video_processor)
register_video_routes(app, video_processor, heatmap_generator, zone_manager)
register_api_routes(app, video_processor, heatmap_generator, zone_manager)

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        # Cleanup resources
        video_processor.cleanup()