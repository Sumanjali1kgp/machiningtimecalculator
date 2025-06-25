from .base_operation import BaseOperation
import math

class PartingOperation(BaseOperation):
    """Class for parting operation calculations."""
    
    def __init__(self, db_conn, material_id, db_params=None, material_rating=1.0, input_dims=None, machine_hour_rate=50.0):
        super().__init__(db_conn, material_id, db_params, material_rating, input_dims, machine_hour_rate)
        self.operation_type = 'parting'
        self.min_diameter = 5.0  # Minimum diameter for parting in mm
        
    def _get_machining_parameters(self):
        """Get parameters from DB for parting operation."""
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT 
                feed_rate_min,
                feed_rate_max,
                spindle_speed_min,
                spindle_speed_max
            FROM MachiningParameters 
            WHERE material_id = ? AND operation_id = 8  -- Parting operation
            LIMIT 1
        ''', (self.material_id,))
        
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"No parameters found for material_id={self.material_id} and parting operation")
        
        feed_min, feed_max, speed_min, speed_max = result
        
        # For parting, use lower feed and speed for better control
        return {
            'feed': feed_min * 0.7,
            'spindle_speed': speed_min * 0.6
        }
    
    def calculate(self):
        """Calculate parting operation time and cost."""
        try:
            # Get parting parameters
            self.depth = float(self.input_dims.get('depth', 0))  # Parting depth in mm
            self.width = float(self.input_dims.get('width', 3.0))  # Parting tool width in mm
            
            if self.depth <= 0:
                raise ValueError("Parting depth must be a positive value")
                
            params = self._get_machining_parameters()
            
            # Calculate number of passes (based on tool width and depth)
            max_pass_depth = self.width * 3  # Max depth per pass is 3x tool width
            num_passes = max(1, math.ceil(self.depth / max_pass_depth))
            
            # Calculate cutting time per pass
            # For parting, we calculate based on the radius
            cutting_distance = self.diameter / 2  # Parting from OD to center
            time_per_pass = (cutting_distance / (params['feed'] * params['spindle_speed'])) * 1.5  # 50% slower for parting
            
            # Total cutting time with 25% buffer
            total_time = (time_per_pass * num_passes) * 1.25
            cost = total_time * (self.MACHINE_HOUR_RATE / 60)  # Convert to hourly rate
            
            result = {
                'operation': 'parting',
                'total_time_minutes': round(total_time, 3),
                'cost': round(cost, 2),
                'cut_parameters': {
                    'diameter': round(self.diameter, 2),
                    'depth': round(self.depth, 3),
                    'tool_width': round(self.width, 2)
                },
                'machining_parameters': {
                    'feed': round(params['feed'], 3),
                    'spindle_speed': params['spindle_speed'],
                    'passes': num_passes
                },
                'warnings': []
            }
            
            if self.diameter < self.min_diameter:
                result['warnings'].append(f"Diameter is below minimum recommended for parting ({self.min_diameter}mm)")
                
            return result
            
        except Exception as e:
            import traceback
            return {'error': f'Error in parting calculation: {str(e)}\n{traceback.format_exc()}'}
