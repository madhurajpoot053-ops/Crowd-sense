"""
API routes for data endpoints
"""
from flask import jsonify, request
import cv2
import numpy as np
import base64
import time
from collections import deque
from config import Config

# Predictive modeling history buffer (stores timestamped people counts)
CROWD_HISTORY = deque(maxlen=60)

def calculate_predictive_metrics(current_count):
    """
    Calculate advanced crowd predictions using Exponential Moving Average (EMA)
    and linear trend velocity estimation.
    """
    now = time.time()
    CROWD_HISTORY.append((now, current_count))
    
    if len(CROWD_HISTORY) < 2:
        return {
            'next_minute_prediction': current_count,
            'trend': 'stable',
            'surge_rate': 0.0,
            'confidence': 95,
            'capacity_pct': round((current_count / max(1, Config.HIGH_THRESHOLD * 1.5)) * 100, 1),
            'risk_level': 'Low' if current_count < Config.LOW_THRESHOLD else ('Medium' if current_count < Config.MEDIUM_THRESHOLD else 'High')
        }
    
    # Calculate Rate of Change (people per minute)
    dt = CROWD_HISTORY[-1][0] - CROWD_HISTORY[0][0]
    dc = CROWD_HISTORY[-1][1] - CROWD_HISTORY[0][1]
    
    velocity_per_min = (dc / dt * 60) if dt > 0 else 0.0
    
    # Exponential Smoothing
    counts = [c for _, c in CROWD_HISTORY]
    alpha = 0.3
    ema = counts[0]
    for c in counts[1:]:
        ema = alpha * c + (1 - alpha) * ema
        
    # Project 1 minute ahead
    predicted_1min = max(0, int(round(ema + velocity_per_min)))
    
    if velocity_per_min > 3.0:
        trend = 'rapid_surge'
    elif velocity_per_min > 0.8:
        trend = 'rising'
    elif velocity_per_min < -3.0:
        trend = 'rapid_clearing'
    elif velocity_per_min < -0.8:
        trend = 'clearing'
    else:
        trend = 'stable'
        
    capacity_pct = min(100.0, round((current_count / max(1, Config.HIGH_THRESHOLD * 1.5)) * 100, 1))
    
    if current_count >= Config.HIGH_THRESHOLD or capacity_pct > 85:
        risk = 'Critical Surge'
    elif current_count >= Config.MEDIUM_THRESHOLD:
        risk = 'Elevated Risk'
    elif velocity_per_min > 5:
        risk = 'Surge Warning'
    else:
        risk = 'Normal Flow'
        
    return {
        'next_minute_prediction': predicted_1min,
        'trend': trend,
        'surge_rate': round(velocity_per_min, 2),
        'confidence': min(98, 70 + len(CROWD_HISTORY)),
        'capacity_pct': capacity_pct,
        'risk_level': risk
    }

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
        metrics = calculate_predictive_metrics(total_people_count)

        if total_people_count < Config.LOW_THRESHOLD:
            density_level = "low"
        elif total_people_count < Config.MEDIUM_THRESHOLD:
            density_level = "medium"
        else:
            density_level = "high"

        return jsonify({
            'grid': heatmap_generator.get_grid_data(),
            'people_count': total_people_count,
            'density_level': density_level,
            'predictive_metrics': metrics
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
        metrics = calculate_predictive_metrics(current_crowd)
        return jsonify(metrics)

    @app.route('/process_frame', methods=['POST'])
    def process_frame():
        """
        Accept a browser webcam frame (base64 JPEG), run YOLO detection,
        update heatmap/zone state, and return annotated frame + heatmap frame.
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

            # Generate synchronized heatmap image for browser webcam feed
            heatmap_img = heatmap_generator.generate_heatmap_image(
                zone_manager.get_zones(),
                people_count,
                zone_manager.get_recommendations()
            )

            # Encode annotated frame back to base64 JPEG
            ret1, buf1 = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            ret2, buf2 = cv2.imencode('.jpg', heatmap_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            if not ret1 or not ret2:
                return jsonify({'error': 'Failed to encode output frame'}), 500

            annotated_b64 = 'data:image/jpeg;base64,' + base64.b64encode(buf1).decode('utf-8')
            heatmap_b64 = 'data:image/jpeg;base64,' + base64.b64encode(buf2).decode('utf-8')

            # Determine density level
            if people_count < Config.LOW_THRESHOLD:
                density_level = 'low'
            elif people_count < Config.MEDIUM_THRESHOLD:
                density_level = 'medium'
            else:
                density_level = 'high'

            # Get enhanced predictive analytics
            predictive_metrics = calculate_predictive_metrics(people_count)

            return jsonify({
                'frame': annotated_b64,
                'heatmap': heatmap_b64,
                'people_count': people_count,
                'density_level': density_level,
                'predictive_metrics': predictive_metrics,
                'zones': zone_manager.get_zones(),
                'recommendations': zone_manager.get_recommendations()
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500
