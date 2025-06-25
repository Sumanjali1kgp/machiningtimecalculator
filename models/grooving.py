from .base_operation import BaseOperation
import math

class GroovingOperation(BaseOperation):
    """Class for grooving operation calculations."""
    
    def __init__(self, db_conn, material_id, db_params=None, material_rating=1.0, input_dims=None, machine_hour_rate=50.0):
        super().__init__(db_conn, material_id, db_params, material_rating, input_dims, machine_hour_rate)
        self.operation_type = 'grooving'
        self.min_groove_width = 1.0  # Minimum groove width in mm
        
    def _get_machining_parameters(self, cut_type='rough'):
        """Get parameters from DB for the given cut type (rough or finish)."""
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT 
                feed_rate_min,
                feed_rate_max,
                spindle_speed_min,
                spindle_speed_max,
                depth_of_cut_min,
                depth_of_cut_max
            FROM MachiningParameters 
            WHERE material_id = ? AND operation_id = 9  -- Grooving operation
            ORDER BY CASE 
                WHEN ? = 'rough' AND notes LIKE '%Rough%' THEN 1
                WHEN ? = 'finish' AND notes LIKE '%Finish%' THEN 1
                ELSE 2
            END
            LIMIT 1
        ''', (self.material_id, cut_type, cut_type))
        
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"No parameters found for material_id={self.material_id} and grooving operation")
        
        (feed_min, feed_max, speed_min, speed_max, doc_min, doc_max) = result
        
        if cut_type == 'rough':
            return {'feed': feed_max * 0.7, 'spindle_speed': speed_min, 'depth_of_cut': doc_max}
        else:
            return {'feed': feed_min * 0.5, 'spindle_speed': speed_max * 0.8, 'depth_of_cut': doc_min}
    
    def calculate(self):
        """Calculate grooving operation time and cost."""
        try:
            # Get parameters for rough and finish passes
            rough_params = self._get_machining_parameters('rough')
            finish_params = self._get_machining_parameters('finish')
            
            # Calculate number of passes based on groove width and tool width
            tool_width = min(3.0, self.width * 0.9)  # Assume max tool width of 3mm or 90% of groove width
            num_passes = max(1, math.ceil(self.width / tool_width))
            
            # Calculate cutting time for each pass
            pass_length = self.diameter * math.pi  # Circumference for one rotation
            rough_time_per_pass = pass_length / (rough_params['feed'] * rough_params['spindle_speed'])
            finish_time_per_pass = pass_length / (finish_params['feed'] * finish_params['spindle_speed'])
            
            total_rough_time = rough_time_per_pass * num_passes
            total_finish_time = finish_time_per_pass * num_passes
            
            total_time = (total_rough_time + total_finish_time) * 1.3  # 30% buffer
            cost = (total_time / 60) * self.MACHINE_HOUR_RATE
            
            result = {
                'operation': 'grooving',
                'total_time_minutes': round(total_time, 3),
                'cost': round(cost, 2),
                'cut_parameters': {
                    'width': round(self.width, 2),
                    'depth': round(self.depth, 3),
                    'diameter': round(self.diameter, 2)
                },
                'rough_cut': {
                    'time': round(total_rough_time, 3),
                    'feed': round(rough_params['feed'], 3),
                    'spindle_speed': rough_params['spindle_speed'],
                    'depth_of_cut': round(rough_params['depth_of_cut'], 2),
                    'passes': num_passes
                },
                'finish_cut': {
                    'time': round(total_finish_time, 3),
                    'feed': round(finish_params['feed'], 3),
                    'spindle_speed': finish_params['spindle_speed'],
                    'depth_of_cut': round(finish_params['depth_of_cut'], 2),
                    'passes': num_passes
                },
                'warnings': []
            }
            
            if self.width < self.min_groove_width:
                result['warnings'].append(f"Groove width is below minimum recommended ({self.min_groove_width}mm)")
                
            return result
            
        except Exception as e:
            import traceback
            return {'error': f'Error in grooving calculation: {str(e)}\n{traceback.format_exc()}'}
