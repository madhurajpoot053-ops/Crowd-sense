"""
Video feed routes
"""
from flask import Response
import time
import cv2

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
        return Response(video_processor.generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/heatmap_feed')
    def heatmap_feed():
        return Response(generate_heatmap(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    def generate_heatmap():
        """Generator for heatmap frames"""
        while True:
            time.sleep(0.1)
            
            # Get current data
            zones = zone_manager.get_zones()
            total_people_count = video_processor.get_people_count()
            recommendations = zone_manager.get_recommendations()
            
            # Generate heatmap image
            heatmap = heatmap_generator.generate_heatmap_image(
                zones, 
                total_people_count, 
                recommendations
            )
            
            # Convert to JPEG
            ret, buffer = cv2.imencode('.jpg', heatmap)
            heatmap_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + heatmap_bytes + b'\r\n')