"""
Video feed routes
"""
from flask import Response, stream_with_context
import time
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
        return Response(
            stream_with_context(generate_video_stream()),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Accel-Buffering': 'no'
            }
        )
    
    @app.route('/heatmap_feed')
    def heatmap_feed():
        return Response(
            stream_with_context(generate_heatmap()),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Accel-Buffering': 'no'
            }
        )

    def generate_video_stream():
        """Safely stream MJPEG video frames to the browser."""
        try:
            for frame_bytes in video_processor.generate_frames():
                yield frame_bytes
        except (BrokenPipeError, ConnectionError, GeneratorExit):
            return

    def generate_heatmap():
        """Generator for heatmap frames"""
        blank_frame = cv2.imencode('.jpg', np.zeros((400, 400, 3), dtype=np.uint8))[1].tobytes()
        try:
            while True:
                time.sleep(0.1)
                
                if video_processor.cap is None or not video_processor.cap.isOpened():
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + blank_frame + b'\r\n')
                    continue

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
                if not ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + blank_frame + b'\r\n')
                    continue

                heatmap_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + heatmap_bytes + b'\r\n')
        except (BrokenPipeError, ConnectionError, GeneratorExit):
            return