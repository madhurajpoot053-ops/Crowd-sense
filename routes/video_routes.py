"""
Video feed routes
"""
from flask import Response
import cv2
import numpy as np
import time

def register_video_routes(app, video_processor, heatmap_generator, zone_manager):
    """
    Register video feed routes
    
    Args:
        app: Flask application instance
        video_processor: VideoProcessor instance
        heatmap_generator: HeatmapGenerator instance
        zone_manager: ZoneManager instance
    """
    
    @app.route('/video_feed')
    def video_feed():
        return Response(
            video_processor.generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    
    @app.route('/heatmap_feed')
    def heatmap_feed():
        return Response(
            generate_heatmap_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    def generate_heatmap_frames():
        """Generator for live heatmap frames."""
        blank_frame = cv2.imencode('.jpg', np.zeros((400, 400, 3), dtype=np.uint8))[1].tobytes()

        while True:
            zones = zone_manager.get_zones()
            total_people_count = video_processor.get_people_count()
            recommendations = zone_manager.get_recommendations()

            heatmap = heatmap_generator.generate_heatmap_image(
                zones,
                total_people_count,
                recommendations
            )

            ret, buffer = cv2.imencode('.jpg', heatmap)
            if ret:
                frame_bytes = buffer.tobytes()
            else:
                frame_bytes = blank_frame

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.05)