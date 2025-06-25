from .base_operation import BaseOperation
import math

class ReamingOperation(BaseOperation):
    """Class for reaming operation calculations."""
    
    def __init__(self, db_conn, material_id, db_params=None, material_rating=1.0, input_dims=None, machine_hour_rate=50.0):
        super().__init__(db_conn, material_id, db_params, material_rating, input_dims, machine_hour_rate)
        self.operation_type = 'reaming'
        self.min_diameter = 3.0  # Minimum reamer diameter in mm
        
    def _get_machining_parameters(self):
        """Get parameters from DB for reaming operation."""
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT 
                feed_rate_min,
                feed_rate_max,
                spindle_speed_min,
                spindle_speed_max
            FROM MachiningParameters 
            WHERE material_id = ? AND operation_id = 5  -- Reaming operation
            LIMIT 1
        ''', (self.material_id,))
        
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"No parameters found for material_id={self.material_id} and reaming operation")
        
        feed_min, feed_max, speed_min, speed_max = result
        
        # For reaming, use lower feed and higher speed for better finish
        return {
            'feed': feed_min * 0.5,  # Slower feed for better finish
            'spindle_speed': speed_max * 0.8  # Slightly reduced speed
        }
    
    def calculate(self):
        """Calculate reaming operation time and cost."""
        try:
            params = self._get_machining_parameters()
            
            # Calculate cutting time (reaming is usually done in one pass)
            cutting_time = self._calculate_cutting_time(
                self.depth,
                params['feed'],
                params['spindle_speed']
            )
            
            # Add approach and overrun
            total_time = cutting_time * 1.1  # 10% buffer
            cost = (total_time / 60) * self.MACHINE_HOUR_RATE
            
            result = {
                'operation': 'reaming',
                'total_time_minutes': round(total_time, 3),
                'cost': round(cost, 2),
                'cut_parameters': {
                    'diameter': round(self.diameter, 2),
                    'depth': round(self.depth, 3)
                },
                'machining_parameters': {
                    'feed': round(params['feed'], 3),
                    'spindle_speed': params['spindle_speed']
                },
                'warnings': []
            }
            
            if self.diameter < self.min_diameter:
                result['warnings'].append(f"Reamer diameter is below minimum recommended ({self.min_diameter}mm)")
                
            return result
            
        except Exception as e:
            import traceback
            return {'error': f'Error in reaming calculation: {str(e)}\n{traceback.format_exc()}'}
