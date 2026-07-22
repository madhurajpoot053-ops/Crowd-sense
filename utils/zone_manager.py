"""
Zone management and density calculation
"""
import copy
from config import Config

class ZoneManager:
    def __init__(self):
        """Initialize zone manager with default zones"""
        self.zones = copy.deepcopy(Config.ZONES)
        self.movement_recommendations = []
    
    def reset_counts(self):
        """Reset zone counts for new frame"""
        for zone_id in self.zones:
            self.zones[zone_id]['count'] = 0
    
    def add_person_to_zone(self, cx, cy, width, height):
        """
        Check which zone a person belongs to and increment count
        
        Args:
            cx, cy: Center coordinates of person
            width, height: Frame dimensions
            
        Returns:
            bool: True if person was added to a zone
        """
        for zone_id, zone_info in self.zones.items():
            # Convert normalized coordinates to actual pixel values
            zone_x1 = int(zone_info['coords'][0] * width)
            zone_y1 = int(zone_info['coords'][1] * height)
            zone_x2 = int(zone_info['coords'][2] * width)
            zone_y2 = int(zone_info['coords'][3] * height)
            
            # Check if person center is within this zone
            if zone_x1 <= cx <= zone_x2 and zone_y1 <= cy <= zone_y2:
                self.zones[zone_id]['count'] += 1
                return True
        
        return False
    
    def calculate_densities(self):
        """Calculate crowd density for each zone and generate movement recommendations"""
        self.movement_recommendations = []
        
        # Determine density levels for each zone
        for zone_id, zone in self.zones.items():
            people_count = zone['count']
            if people_count < Config.LOW_THRESHOLD:
                zone['density'] = 'low'
            elif people_count < Config.MEDIUM_THRESHOLD:
                zone['density'] = 'medium'
            else:
                zone['density'] = 'high'
        
        # Generate movement recommendations
        high_density_zones = []
        low_density_zones = []
        
        for zone_id, zone in self.zones.items():
            if zone['density'] == 'high':
                high_density_zones.append(zone_id)
            elif zone['density'] == 'low':
                low_density_zones.append(zone_id)
        
        # Generate recommendations from high to low density zones
        for high_zone in high_density_zones:
            for low_zone in low_density_zones:
                if high_zone != low_zone:
                    recommendation = f"Move from Zone {high_zone} to Zone {low_zone}"
                    self.movement_recommendations.append(recommendation)
        
        # If no clear recommendations
        if not self.movement_recommendations:
            if all(zone['density'] == 'high' for zone in self.zones.values()):
                self.movement_recommendations.append("All zones at capacity. Consider opening new areas.")
            elif all(zone['density'] == 'low' for zone in self.zones.values()):
                self.movement_recommendations.append("All zones have low occupancy. No movement needed.")
            else:
                self.movement_recommendations.append("Crowd distribution is balanced across zones.")
    
    def update_zones(self, new_zones):
        """
        Update zone configuration
        
        Args:
            new_zones: Dictionary with new zone configurations
            
        Returns:
            bool: True if update was successful
        """
        for zone_id, zone_info in new_zones.items():
            if zone_id in self.zones and 'coords' in zone_info:
                # Update coordinates if provided
                if all(0 <= x <= 1 for x in zone_info['coords']):
                    self.zones[zone_id]['coords'] = zone_info['coords']
                
                # Update color if provided
                if 'color' in zone_info and len(zone_info['color']) == 3:
                    self.zones[zone_id]['color'] = zone_info['color']
        
        return True
    
    def get_zones(self):
        """Get current zone configuration"""
        return self.zones
    
    def get_recommendations(self):
        """Get movement recommendations"""
        return self.movement_recommendations