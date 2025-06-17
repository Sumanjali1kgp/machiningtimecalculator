import math
from .base_operation import BaseOperation

class FacingOperation(BaseOperation):
    """Class for facing operation calculations with rough and finish cuts."""
    
    def __init__(self, db_params, material_rating, input_dims=None):
        """
        Initialize FacingOperation.
        
        Args:
            db_params: SQLAlchemy model instance with machining parameters
            material_rating (float): Material's machinability rating (0-1)
            input_dims (dict, optional): Dictionary containing:
                - diameter (float): Diameter in mm (required)
                - depth_of_cut (float): Depth of cut in mm (required)
                - feed (float, optional): Feed rate in mm/rev
                - spindle_speed (float, optional): Spindle speed in RPM
        """
        self.db_params = db_params
        self.material_rating = material_rating
        
        # Default values
        self.diameter = 0
        self.depth_of_cut = 0
        self.feed = 0
        self.spindle_speed = 0
        self.finish_doc = 0.1  # de25fault finish cut (mm)
        self.approach = 5.0  # approach distance in mm
        self.overrun = 5.0   # overrun distance in mm
        
        # If input dimensions are provided, process them
        if input_dims:
            self.set_dimensions(input_dims)
    
    def _get_default_parameters(self):
        """Get default feed and spindle speed from the database parameters.
        
        Returns:
            dict: Dictionary containing default feed and spindle speed
        """
        if not self.db_params:
            return {'feed': 0.2, 'spindle_speed': 150}
            
        return {
            'feed': (self.db_params.feed_rate_min + self.db_params.feed_rate_max) / 2,
            'spindle_speed': (self.db_params.spindle_speed_min + self.db_params.spindle_speed_max) / 2
        }
    
    def _get_default_parameters(self):
        """Get default feed and spindle speed from the database.
        
        Returns:
            dict: Dictionary containing default feed and spindle speed
        """
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT 
                (feed_rate_min + feed_rate_max) / 2 as default_feed,
                (spindle_speed_min + spindle_speed_max) / 2 as default_speed
            FROM MachiningParameters 
            WHERE material_id = ? AND operation_id = 1  -- operation_id 1 is for Facing
            LIMIT 1
        ''', (self.material_id,))
        
        result = cursor.fetchone()
        if result:
            return {
                'feed': result[0],
                'spindle_speed': result[1]
            }
        return {'feed': 0.2, 'spindle_speed': 150}  # Fallback defaults

    def set_dimensions(self, input_dims):
        """Set the dimensions for the facing operation.
        
        Args:
            input_dims (dict): Dictionary containing operation dimensions
        """
        # Get default parameters from database
        defaults = self._get_default_parameters()
        
        # Get input values with defaults from database if not provided
        self.diameter = float(input_dims.get('diameter', 0))
        self.depth_of_cut = float(input_dims.get('depth_of_cut', 0))
        self.feed = float(input_dims.get('feed', defaults['feed']))
        self.spindle_speed = float(input_dims.get('spindle_speed', defaults['spindle_speed']))
        
        # Validate inputs
        if self.diameter <= 0 or self.depth_of_cut <= 0:
            raise ValueError("Diameter and depth of cut must be positive numbers")
            
        if self.feed <= 0 or self.spindle_speed <= 0:
            raise ValueError("Feed rate and spindle speed must be positive numbers")
    
    def _get_machining_parameters(self, cut_type='rough'):
        """
        Get machining parameters for rough or finish cut from the database.
        
        Args:
            cut_type (str): 'rough' or 'finish'
            
        Returns:
            dict: Dictionary containing feed, spindle_speed, and depth_of_cut
            
        Raises:
            ValueError: If no parameters found in the database
        """
        cursor = self.db_conn.cursor()
        
        # First try to get parameters based on operation notes
        cursor.execute('''
            SELECT 
                feed_rate_min,
                feed_rate_max,
                spindle_speed_min,
                spindle_speed_max,
                depth_of_cut_min,
                depth_of_cut_max
            FROM MachiningParameters 
            WHERE material_id = ? AND operation_id = 1
            ORDER BY CASE 
                WHEN ? = 'rough' AND notes LIKE '%Rough%' THEN 1
                WHEN ? = 'finish' AND notes LIKE '%Finish%' THEN 1
                ELSE 2
            END
            LIMIT 1
        ''', (self.material_id, cut_type, cut_type))
        
        result = cursor.fetchone()
        
        # If no specific cut type found, get any available parameters
        if not result:
            cursor.execute('''
                SELECT 
                    feed_rate_min,
                    feed_rate_max,
                    spindle_speed_min,
                    spindle_speed_max,
                    depth_of_cut_min,
                    depth_of_cut_max
                FROM MachiningParameters 
                WHERE material_id = ? AND operation_id = 1
                LIMIT 1
            ''', (self.material_id,))
            result = cursor.fetchone()
        
        if not result:
            raise ValueError(
                f"No machining parameters found for material_id={self.material_id} and operation_id=1. "
                "Please ensure the database is properly populated with machining parameters."
            )
        
        # Unpack the result
        (
            feed_rate_min,
            feed_rate_max,
            spindle_speed_min,
            spindle_speed_max,
            depth_of_cut_min,
            depth_of_cut_max
        ) = result
        
        # Return appropriate values based on cut type
        if cut_type == 'rough':
            return {
                'feed': feed_rate_max,  # Higher feed for roughing
                'spindle_speed': spindle_speed_min,  # Lower speed for roughing
                'depth_of_cut': depth_of_cut_max  # Deeper cut for roughing
            }
        else:  # finish cut
            return {
                'feed': feed_rate_min,  # Lower feed for finishing
                'spindle_speed': spindle_speed_max,  # Higher speed for finishing
                'depth_of_cut': depth_of_cut_min  # Lighter cut for finishing
            }
    
    def get_parameters(self, cut_type='rough'):
        """
        Get machining parameters for rough or finish cut.
        
        Args:
            cut_type (str): 'rough' or 'finish'
            
        Returns:
            dict: Dictionary containing spindle_speed, feed_rate, and doc
        """
        return self._get_machining_parameters(cut_type)
    
    def _calculate_cutting_time(self, length, feed, rpm, depth, total_depth):
        """Calculate cutting time for given parameters.
        
        Args:
            length (float): Length of cut in mm
            feed (float): Feed rate in mm/rev
            rpm (float): Spindle speed in RPM
            depth (float): Depth of cut per pass in mm
            total_depth (float): Total depth to be removed in mm
            
        Returns:
            tuple: (total_time, num_passes)
        """
        if depth <= 0 or total_depth <= 0 or feed <= 0 or rpm <= 0:
            return 0.0, 0
            
        num_passes = max(1, int(math.ceil(total_depth / depth)))
        time_per_pass = length / (feed * rpm) if (feed * rpm) > 0 else 0
        total_time = time_per_pass * num_passes
        
        return total_time, num_passes
    
    def calculate(self, inputs=None):
        """
        Calculate facing operation time using rough and finish cut parameters.
        
        Args:
            inputs (dict, optional): Additional input parameters (not used, kept for compatibility)
            
        Returns:
            dict: Dictionary containing all calculated parameters
        """
        try:
            # Validate inputs
            if self.diameter <= 0 or self.depth_of_cut <= 0:
                raise ValueError("Diameter and depth of cut must be positive numbers")
            
            # Get parameters for rough and finish cuts from database
            rough_params = self._get_machining_parameters('rough')
            finish_params = self._get_machining_parameters('finish')
            
            # Calculate length of cut (radius + approach + overrun)
            length_of_cut = (self.diameter / 2) + self.approach + self.overrun
            
            # Calculate rough cut time and passes
            rough_depth = max(0, self.depth_of_cut - finish_params['depth_of_cut'])
            rough_time, rough_passes = self._calculate_cutting_time(
                length_of_cut,
                rough_params['feed'],
                rough_params['spindle_speed'],
                rough_params['depth_of_cut'],
                rough_depth
            )
            
            # Calculate finish cut time (always 1 pass)
            finish_depth = min(finish_params['depth_of_cut'], self.depth_of_cut)
            finish_time, finish_passes = self._calculate_cutting_time(
                length_of_cut,
                finish_params['feed'],
                finish_params['spindle_speed'],
                finish_params['depth_of_cut'],
                finish_depth
            )
            
            # Total time with 10% safety factor
            total_time = (rough_time + finish_time) * 1.1
            
            # Calculate cost based on machine hour rate
            cost = (total_time / 60) * self.MACHINE_HOUR_RATE
            
            # Prepare detailed result dictionary
            result = {
                'operation': 'facing',
                'total_time_minutes': round(total_time, 3),
                'rough_cut': {
                    'time': round(rough_time, 3),
                    'passes': rough_passes,
                    'feed': round(rough_params['feed'], 3),
                    'spindle_speed': round(rough_params['spindle_speed'], 2),
                    'depth_per_pass': round(rough_params['depth_of_cut'], 3),
                    'total_depth': round(rough_depth, 3)
                },
                'finish_cut': {
                    'time': round(finish_time, 3),
                    'passes': finish_passes,
                    'feed': round(finish_params['feed'], 3),
                    'spindle_speed': round(finish_params['spindle_speed'], 2),
                    'depth': round(finish_params['depth_of_cut'], 3)
                },
                'cut_parameters': {
                    'diameter': round(self.diameter, 2),
                    'total_depth': round(self.depth_of_cut, 3),
                    'length_of_cut': round(length_of_cut, 3)
                },
                'cost': round(cost, 2),
                'warnings': []
            }
            
            # Add warnings if needed
            if rough_passes > 1:
                result['warnings'].append(f'Multiple rough passes ({rough_passes}) needed for the specified depth')
                
            rough_feed_rate = rough_params['feed'] * rough_params['spindle_speed']
            if rough_feed_rate > 1000:  # mm/min
                result['warnings'].append(f'Rough cut feed rate ({rough_feed_rate:.1f} mm/min) is relatively high')
            
            finish_feed_rate = finish_params['feed'] * finish_params['spindle_speed']
            if finish_feed_rate > 800:  # mm/min
                result['warnings'].append(f'Finish cut feed rate ({finish_feed_rate:.1f} mm/min) is relatively high')
                
            return result
            
        except Exception as e:
            import traceback
            return {'error': f'Error in facing calculation: {str(e)}\n{traceback.format_exc()}'}
