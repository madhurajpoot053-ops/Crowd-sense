"""
Video feed routes
"""
from flask import Response
import cv2
import numpy as np

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
        frame_bytes = video_processor.get_frame_snapshot()
        return Response(
            frame_bytes,
            mimetype='image/jpeg',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    
    @app.route('/heatmap_feed')
    def heatmap_feed():
        heatmap_bytes = generate_heatmap_snapshot()
        return Response(
            heatmap_bytes,
            mimetype='image/jpeg',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )

    def generate_heatmap_snapshot():
        """Return a single heatmap snapshot image."""
        blank_frame = cv2.imencode('.jpg', np.zeros((400, 400, 3), dtype=np.uint8))[1].tobytes()

        if video_processor.cap is None or not video_processor.cap.isOpened():
            return blank_frame

        zones = zone_manager.get_zones()
        total_people_count = video_processor.get_people_count()
        recommendations = zone_manager.get_recommendations()
        
        heatmap = heatmap_generator.generate_heatmap_image(
            zones,
            total_people_count,
            recommendations
        )
        
        ret, buffer = cv2.imencode('.jpg', heatmap)
        if not ret:
            return blank_frame

        return buffer.tobytes()