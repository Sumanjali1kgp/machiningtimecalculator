import math
from .base_operation import BaseOperation

class DrillingOperation(BaseOperation):
    """Class for drilling operation calculations."""
    
    def calculate(self, inputs):
        """
        Calculate drilling operation parameters.
        
        Args:
            inputs (dict): Dictionary containing:
                - diameter (float): Drill bit diameter in mm
                - depth (float): Hole depth in mm
                
        Returns:
            dict: Dictionary containing all calculated parameters
        """
        try:
            diameter = float(inputs.get('diameter', 0))
            depth = float(inputs.get('depth', 0))
            
            if diameter <= 0 or depth <= 0:
                raise ValueError("Diameter and depth must be positive")
            
            # Get recommended parameters
            cutting_speed = self._get_cutting_speed()
            feed = self._get_feed_rate()
                
            # RPM calculation
            rpm = (cutting_speed * 1000) / (math.pi * diameter)
            
            # Drilling time (minutes)
            time_per_hole = (depth / (feed * rpm)) * 1.3  # 30% extra for chip clearing
            
            # Calculate cost
            cost = (time_per_hole / 60) * self.MACHINE_HOUR_RATE
            
            return {
                'operation': 'drilling',
                'cutting_speed': round(cutting_speed, 2),
                'feed_rate': round(feed, 3),
                'rpm': round(rpm, 2),
                'machining_time': round(time_per_hole, 2),
                'cost': round(cost, 2),
                'warnings': self._check_limits(rpm, feed, diameter/2)  # DOC is radius for drilling
            }
            
        except (ValueError, TypeError) as e:
            return {'error': f'Invalid input parameters: {str(e)}'}
