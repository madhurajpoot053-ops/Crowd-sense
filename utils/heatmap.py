"""
Heatmap generation and visualization
"""
import numpy as np
import cv2
from config import Config

class HeatmapGenerator:
    def __init__(self):
        """Initialize heatmap generator"""
        self.grid_counts = [[0 for _ in range(Config.GRID_COLS)] for _ in range(Config.GRID_ROWS)]
        self.smoothed_grid = [[0 for _ in range(Config.GRID_COLS)] for _ in range(Config.GRID_ROWS)]
    
    def reset_grid(self):
        """Reset grid counts for new frame"""
        self.grid_counts = [[0 for _ in range(Config.GRID_COLS)] for _ in range(Config.GRID_ROWS)]
    
    def add_person_to_grid(self, cx, cy, frame_height, frame_width):
        """
        Add person to grid
        
        Args:
            cx, cy: Center coordinates of person
            frame_height, frame_width: Frame dimensions
        """
        cell_h = frame_height // Config.GRID_ROWS
        cell_w = frame_width // Config.GRID_COLS
        
        # Determine which grid cell the center falls into
        row = min(cy // cell_h, Config.GRID_ROWS - 1)
        col = min(cx // cell_w, Config.GRID_COLS - 1)
        
        # Increment count for that cell
        self.grid_counts[row][col] += 1
    
    def update_smoothed_grid(self):
        """Update smoothed grid using exponential moving average"""
        for r in range(Config.GRID_ROWS):
            for c in range(Config.GRID_COLS):
                self.smoothed_grid[r][c] = (Config.SMOOTHING_FACTOR * self.grid_counts[r][c] + 
                                           (1 - Config.SMOOTHING_FACTOR) * self.smoothed_grid[r][c])
    
    def generate_heatmap_image(self, zones, total_people_count, movement_recommendations):
        """
        Generate heatmap visualization
        
        Args:
            zones: Zone configuration
            total_people_count: Total number of people detected
            movement_recommendations: List of movement recommendations
            
        Returns:
            numpy array: Heatmap image
        """
        heatmap_width = 400
        heatmap_height = 400
        heatmap = np.zeros((heatmap_height, heatmap_width, 3), dtype=np.uint8)
        
        # Calculate cell dimensions
        cell_h = heatmap_height // Config.GRID_ROWS
        cell_w = heatmap_width // Config.GRID_COLS
        
        # Find maximum value for normalization
        max_count = max(max(row) for row in self.smoothed_grid) if any(any(row) for row in self.smoothed_grid) else 1
        if max_count < 0.1:
            max_count = 0.1
        
        # Fill with dark blue background
        heatmap[:, :] = (100, 0, 0)
        
        # Create base heatmap with intensity values
        base_heatmap = np.zeros((heatmap_height, heatmap_width), dtype=np.float32)
        
        for row in range(Config.GRID_ROWS):
            for col in range(Config.GRID_COLS):
                if self.smoothed_grid[row][col] > 0.01:
                    y_center = int((row + 0.5) * cell_h)
                    x_center = int((col + 0.5) * cell_w)
                    
                    intensity = min(1.0, self.smoothed_grid[row][col] / max_count)
                    
                    # Apply Gaussian blob
                    sigma = max(cell_h, cell_w) * 0.5
                    y, x = np.ogrid[-y_center:heatmap_height-y_center, -x_center:heatmap_width-x_center]
                    mask = np.exp(-(x*x + y*y) / (2*sigma*sigma))
                    
                    base_heatmap = np.maximum(base_heatmap, mask * intensity)
        
        # Apply colormap
        heatmap = self._apply_colormap(base_heatmap, heatmap_height, heatmap_width)
        
        # Apply Gaussian blur
        heatmap = cv2.GaussianBlur(heatmap, (5, 5), 0)
        
        # Add title
        cv2.putText(heatmap, "Activity Heatmap", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Draw zone boundaries
        self._draw_zones(heatmap, zones, heatmap_width, heatmap_height)
        
        # Add people count box
        self._draw_count_box(heatmap, total_people_count, heatmap_width, heatmap_height)
        
        # Add gradient legend
        self._draw_legend(heatmap, heatmap_width, heatmap_height)
        
        # Add movement recommendations
        self._draw_recommendations(heatmap, movement_recommendations, heatmap_width)
        
        return heatmap
    
    def _apply_colormap(self, base_heatmap, height, width):
        """Apply color gradient to heatmap"""
        heatmap = np.zeros((height, width, 3), dtype=np.uint8)
        heatmap[:, :] = (100, 0, 0)  # Dark blue background
        
        for y in range(height):
            for x in range(width):
                intensity = base_heatmap[y, x]
                if intensity > 0.01:
                    color = self._get_gradient_color(intensity)
                    heatmap[y, x] = color
        
        return heatmap
    
    def _get_gradient_color(self, intensity):
        """Get color for given intensity (BGR format)"""
        if intensity < 0.25:
            # Blue to Cyan
            g_value = int(255 * (intensity / 0.25))
            return (255, g_value, 0)
        elif intensity < 0.5:
            # Cyan to Green
            b_value = int(255 - 255 * ((intensity - 0.25) / 0.25))
            return (b_value, 255, 0)
        elif intensity < 0.75:
            # Green to Yellow
            r_value = int(255 * ((intensity - 0.5) / 0.25))
            return (0, 255, r_value)
        else:
            # Yellow to Red
            g_value = int(255 - 255 * ((intensity - 0.75) / 0.25))
            return (0, g_value, 255)
    
    def _draw_zones(self, heatmap, zones, width, height):
        """Draw zone boundaries on heatmap"""
        for zone_id, zone_info in zones.items():
            x1 = int(zone_info['coords'][0] * width)
            y1 = int(zone_info['coords'][1] * height)
            x2 = int(zone_info['coords'][2] * width)
            y2 = int(zone_info['coords'][3] * height)
            
            cv2.rectangle(heatmap, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.putText(heatmap, f"Zone {zone_id}", (x1 + 5, y1 + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def _draw_count_box(self, heatmap, total_people_count, width, height):
        """Draw people count box with density indicator"""
        if total_people_count < Config.LOW_THRESHOLD:
            density_text = "Low Overall Density"
            count_color = (0, 255, 0)
        elif total_people_count < Config.MEDIUM_THRESHOLD:
            density_text = "Medium Overall Density"
            count_color = (0, 165, 255)
        else:
            density_text = "High Overall Density"
            count_color = (0, 0, 255)
        
        count_box_y1 = height - 80
        count_box_y2 = height - 20
        count_box_x1 = width // 2 - 100
        count_box_x2 = width // 2 + 100
        
        overlay = heatmap.copy()
        cv2.rectangle(overlay, (count_box_x1, count_box_y1), (count_box_x2, count_box_y2), count_color, -1)
        cv2.addWeighted(overlay, 0.7, heatmap, 0.3, 0, heatmap)
        
        cv2.rectangle(heatmap, (count_box_x1, count_box_y1), (count_box_x2, count_box_y2), (255, 255, 255), 2)
        
        cv2.putText(heatmap, f"Total People: {total_people_count}", 
                   (count_box_x1 + 10, count_box_y1 + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(heatmap, density_text, 
                   (count_box_x1 + 10, count_box_y1 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def _draw_legend(self, heatmap, width, height):
        """Draw gradient legend"""
        legend_height = 20
        legend_width = 200
        legend_x = 20
        legend_y = height - 120
        
        legend = np.zeros((legend_height, legend_width, 3), dtype=np.uint8)
        for x in range(legend_width):
            ratio = x / legend_width
            color = self._get_gradient_color(ratio)
            legend[:, x] = color
        
        heatmap[legend_y:legend_y+legend_height, legend_x:legend_x+legend_width] = legend
        
        cv2.putText(heatmap, "Low", (legend_x, legend_y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(heatmap, "High", (legend_x + legend_width - 30, legend_y - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    def _draw_recommendations(self, heatmap, recommendations, width):
        """Draw movement recommendations box"""
        if recommendations:
            recommend_box_y1 = 60
            recommend_box_x1 = 20
            recommend_box_width = width - 40
            recommend_box_height = 30 + (len(recommendations) * 25)
            recommend_box_y2 = recommend_box_y1 + recommend_box_height
            recommend_box_x2 = recommend_box_x1 + recommend_box_width
            
            overlay = heatmap.copy()
            cv2.rectangle(overlay, (recommend_box_x1, recommend_box_y1), 
                         (recommend_box_x2, recommend_box_y2), (0, 0, 128), -1)
            cv2.addWeighted(overlay, 0.7, heatmap, 0.3, 0, heatmap)
            
            cv2.rectangle(heatmap, (recommend_box_x1, recommend_box_y1), 
                         (recommend_box_x2, recommend_box_y2), (255, 255, 255), 2)
            
            cv2.putText(heatmap, "Movement Recommendations:", 
                       (recommend_box_x1 + 10, recommend_box_y1 + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            for i, recommendation in enumerate(recommendations):
                cv2.putText(heatmap, recommendation, 
                           (recommend_box_x1 + 10, recommend_box_y1 + 50 + (i * 25)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def get_grid_data(self):
        """Get current grid data"""
        return self.smoothed_grid