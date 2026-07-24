"""
API routes for data endpoints
"""
from flask import jsonify, request
import cv2
import numpy as np
import base64
from config import Config

def register_api_routes(app, video_processor, heatmap_generator, zone_manager):
    """
    Register API routes

    Args:
        app: Flask application instance
        video_processor: VideoProcessor instance
        heatmap_generator: HeatmapGenerator instance
        zone_manager: ZoneManager instance
    """

    @app.route('/zone_data')
    def zone_data():
        """Return zone-specific data as JSON"""
        zones = zone_manager.get_zones()
        total_people = video_processor.get_people_count()
        recommendations = zone_manager.get_recommendations()

        return jsonify({
            'zones': zones,
            'total_people': total_people,
            'recommendations': recommendations
        })

    @app.route('/heatmap_data')
    def heatmap_data():
        """Return heatmap data as JSON"""
        total_people_count = video_processor.get_people_count()

        if total_people_count < Config.LOW_THRESHOLD:
            density_level = "low"
        elif total_people_count < Config.MEDIUM_THRESHOLD:
            density_level = "medium"
        else:
            density_level = "high"

        return jsonify({
            'grid': heatmap_generator.get_grid_data(),
            'people_count': total_people_count,
            'density_level': density_level
        })

    @app.route('/update_zones', methods=['POST'])
    def update_zones():
        """Update zone configuration"""
        data = request.json
        if data and 'zones' in data:
            new_zones = data['zones']
            zone_manager.update_zones(new_zones)

        return jsonify({
            'success': True,
            'zones': zone_manager.get_zones()
        })

    @app.route('/predict', methods=['POST', 'GET'])
    def predict():
        """Return crowd density prediction as JSON"""
        data = request.get_json(silent=True) or {}
        current_crowd = data.get('current_crowd', video_processor.get_people_count())
        predicted_count = max(0, int(current_crowd * 1.05))
        return jsonify({
            'next_minute_prediction': predicted_count
        })

    @app.route('/process_frame', methods=['POST'])
    def process_frame():
        """
        Accept a browser webcam frame (base64 JPEG), run YOLO detection,
        update heatmap/zone state, and return the annotated frame.
        """
        try:
            data = request.get_json(silent=True) or {}
            frame_data = data.get('frame', '')

            # Decode base64 → numpy array
            if ',' in frame_data:
                frame_data = frame_data.split(',', 1)[1]
            img_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return jsonify({'error': 'Invalid frame data'}), 400

            # Run detection & update state (reuses existing VideoProcessor logic)
            annotated_frame, people_count = video_processor.process_frame(frame)

            # Encode annotated frame back to base64 JPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                return jsonify({'error': 'Failed to encode frame'}), 500

            annotated_b64 = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')

            # Also get density level
            if people_count < Config.LOW_THRESHOLD:
                density_level = 'low'
            elif people_count < Config.MEDIUM_THRESHOLD:
                density_level = 'medium'
            else:
                density_level = 'high'

            return jsonify({
                'frame': annotated_b64,
                'people_count': people_count,
                'density_level': density_level
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500