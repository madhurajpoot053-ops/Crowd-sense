"""
API routes for data endpoints
"""
from flask import jsonify, request
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
        
        # Determine crowd density level
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