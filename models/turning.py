import math
from .base_operation import BaseOperation

class TurningOperation(BaseOperation):
    """Class for turning operation calculations with automatic rough and finish cuts.
    
    This class automatically calculates both roughing and finishing passes based on
    material properties and operation requirements.
    """
    
    def __init__(self, db_params, material_id, material_rating, input_dims=None, db_conn=None):
        """
        Initialize TurningOperation.
        
        Args:
            db_params: SQLAlchemy model instance with machining parameters
            material_id (int): ID of the material from the database
            material_rating (float): Material's machinability rating (0-1)
            input_dims (dict, optional): Dictionary containing:
                - start_dia (float): Starting diameter in mm (required)
                - end_dia (float): Ending diameter in mm (required)
                - length (float): Length to turn in mm (required)
                - feed (float, optional): Feed rate in mm/rev
                - spindle_speed (float, optional): Spindle speed in RPM
            db_conn: Database connection object (optional)
        """
        self.db_params = db_params
        self.material_id = material_id
        self.material_rating = material_rating
        self.db_conn = db_conn
        
        # Default values
        self.start_dia = 0
        self.end_dia = 0
        self.length = 0
        self.feed = 0
        self.spindle_speed = 0
        self.approach = 5.0  # approach distance in mm
        self.overrun = 5.0   # overrun distance in mm
        
        # If input dimensions are provided, process them
        if input_dims:
            self.set_dimensions(input_dims)
    
    def _get_default_parameters(self):
        """Get default feed and spindle speed from the database.
        
        Returns:
            dict: Dictionary containing default feed and spindle speed
        """
        if self.db_conn:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute('''
                    SELECT 
                        (feed_rate_min + feed_rate_max) / 2 as default_feed,
                        (spindle_speed_min + spindle_speed_max) / 2 as default_speed,
                        (depth_of_cut_min + depth_of_cut_max) / 2 as default_doc
                    FROM MachiningParameters 
                    WHERE material_id = ? AND operation_id = 2  -- operation_id 2 is for Turning
                    LIMIT 1
                ''', (self.material_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'feed': result[0],
                        'spindle_speed': result[1],
                        'depth_of_cut': result[2]
                    }
            except Exception as e:
                print(f"Error getting default parameters: {e}")
        
        # Fallback to using db_params if available
        if self.db_params:
            return {
                'feed': (self.db_params.feed_rate_min + self.db_params.feed_rate_max) / 2,
                'spindle_speed': (self.db_params.spindle_speed_min + self.db_params.spindle_speed_max) / 2,
                'depth_of_cut': (self.db_params.depth_of_cut_min + self.db_params.depth_of_cut_max) / 2
            }
        
        # Final fallback defaults
        return {
            'feed': 0.2,  # mm/rev
            'spindle_speed': 150,  # RPM
            'depth_of_cut': 1.0  # mm
        }

    def set_dimensions(self, input_dims):
        """Set the dimensions for the turning operation.
        
        Args:
            input_dims (dict): Dictionary containing operation dimensions
        """
        # Get default parameters from database
        defaults = self._get_default_parameters()
        
        # Get input values with defaults from database if not provided
        self.start_dia = float(input_dims.get('start_dia', 0))
        self.end_dia = float(input_dims.get('end_dia', 0))
        self.length = float(input_dims.get('length', 0))
        self.feed = float(input_dims.get('feed', defaults['feed']))
        self.spindle_speed = float(input_dims.get('spindle_speed', defaults['spindle_speed']))
        
        # Validate inputs
        if self.start_dia <= 0 or self.end_dia <= 0 or self.length <= 0:
            raise ValueError("Start diameter, end diameter, and length must be positive numbers")
            
        if self.start_dia <= self.end_dia:
            raise ValueError("Start diameter must be greater than end diameter for external turning")
    
    def _get_machining_parameters(self, cut_type='rough'):
        """
        Get machining parameters for rough or finish cut from the database parameters.
        
        For rough cuts, we use maximum feed rate, minimum spindle speed, and maximum depth of cut.
        For finish cuts, we use minimum feed rate, maximum spindle speed, and minimum depth of cut.
        
        Args:
            cut_type (str): 'rough' or 'finish'
            
        Returns:
            dict: Dictionary containing feed (mm/rev), spindle_speed (RPM), and depth_of_cut (mm)
            
        Raises:
            ValueError: If no parameters are available or invalid cut type
        """
        if not self.db_params:
            # Default values if no parameters are available
            defaults = {
                'rough': {
                    'feed': 0.3,  # mm/rev
                    'spindle_speed': 500,  # RPM
                    'depth_of_cut': 2.0  # mm
                },
                'finish': {
                    'feed': 0.1,  # mm/rev
                    'spindle_speed': 1000,  # RPM
                    'depth_of_cut': 0.5  # mm
                }
            }
            return defaults.get(cut_type, defaults['rough'])
        
        # Apply material rating adjustment (higher rating = better machinability)
        material_factor = 0.8 + (self.material_rating * 0.4)  # 0.8 to 1.2 range
        
        if cut_type == 'rough':
            return {
                'feed': self.db_params.feed_rate_max * material_factor,  # Higher feed for roughing
                'spindle_speed': max(
                    self.db_params.spindle_speed_min,
                    self.db_params.spindle_speed_max * (0.8 / material_factor)  # Lower speed for roughing
                ),
                'depth_of_cut': min(
                    self.db_params.depth_of_cut_max * material_factor,
                    self.start_dia / 4  # Safety limit: don't exceed 25% of diameter
                )
            }
        elif cut_type == 'finish':
            return {
                'feed': self.db_params.feed_rate_min * material_factor,  # Lower feed for finishing
                'spindle_speed': self.db_params.spindle_speed_max * material_factor,  # Higher speed for finishing
                'depth_of_cut': max(
                    self.db_params.depth_of_cut_min,
                    0.1  # Minimum depth of cut for finishing
                )
            }
        else:
            raise ValueError(f"Invalid cut type: {cut_type}. Must be 'rough' or 'finish'.")
    
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
            
        # Calculate number of passes needed
        num_passes = max(1, int(math.ceil(total_depth / depth)))
        
        # Calculate time per pass in minutes
        # Feed rate in mm/min = feed (mm/rev) * rpm (rev/min)
        feed_rate_mm_per_min = feed * rpm
        
        # Time per pass in minutes = length (mm) / feed_rate (mm/min)
        # Add approach and overrun to the length
        time_per_pass = (length + self.approach + self.overrun) / feed_rate_mm_per_min if feed_rate_mm_per_min > 0 else 0
        
        # Total time is time per pass multiplied by number of passes
        total_time = time_per_pass * num_passes
        
        return total_time, num_passes
    
    def calculate(self, inputs=None):
        """
        Calculate turning operation time using automatic rough and finish cut parameters.
        
        This method automatically calculates the number of rough passes needed based on
        the total material to remove and the maximum depth of cut. It then adds a single
        finish pass for the final dimensions.
        
        Args:
            inputs (dict, optional): Additional input parameters (not used, kept for compatibility)
            
        Returns:
            dict: Dictionary containing all calculated parameters including:
                - operation: Operation type ('turning')
                - total_time_minutes: Total machining time in minutes
                - rough_cut: Details about roughing passes
                - finish_cut: Details about finishing pass
                - cut_parameters: Input dimensions
                - cost: Estimated cost
                - warnings: List of any warnings
        """
        try:
            # Validate inputs
            if self.start_dia <= 0 or self.end_dia <= 0 or self.length <= 0:
                raise ValueError("Start diameter, end diameter, and length must be positive numbers")
            
            # Calculate total depth to remove (radius difference)
            total_depth = (self.start_dia - self.end_dia) / 2
            if total_depth <= 0:
                raise ValueError("Start diameter must be greater than end diameter")
            
            # Get parameters for rough and finish cuts
            rough_params = self._get_machining_parameters('rough')
            finish_params = self._get_machining_parameters('finish')
            
            # Calculate material to remove with roughing (leave finish allowance)
            finish_allowance = finish_params['depth_of_cut']
            rough_depth = max(0, total_depth - finish_allowance)
            
            # Calculate number of rough passes needed
            rough_passes = max(1, math.ceil(rough_depth / rough_params['depth_of_cut']))
            actual_rough_doc = rough_depth / rough_passes
            
            # Calculate cutting time for rough passes
            cutting_length = self.length + self.approach + self.overrun
            rough_feed_rate = rough_params['feed'] * rough_params['spindle_speed']  # mm/min
            time_per_rough_pass = cutting_length / rough_feed_rate if rough_feed_rate > 0 else 0
            total_rough_time = time_per_rough_pass * rough_passes
            
            # Calculate finish pass time
            finish_feed_rate = finish_params['feed'] * finish_params['spindle_speed']  # mm/min
            finish_time = cutting_length / finish_feed_rate if finish_feed_rate > 0 else 0
            
            # Apply safety factor to total time
            total_time = (total_rough_time + finish_time) * self.SAFETY_FACTOR
            
            # Calculate cost based on machine hour rate
            cost = (total_time / 60) * self.MACHINE_HOUR_RATE
            
            # Prepare detailed result dictionary
            result = {
                'operation': 'turning',
                'total_time_minutes': round(total_time, 3),
                'rough_cut': {
                    'time': round(total_rough_time, 3),
                    'passes': rough_passes,
                    'feed': round(rough_params['feed'], 3),  # mm/rev
                    'feed_rate': round(rough_feed_rate, 1),  # mm/min
                    'spindle_speed': round(rough_params['spindle_speed']),  # RPM
                    'depth_per_pass': round(actual_rough_doc, 3),  # mm
                    'total_depth': round(rough_depth, 3)  # mm
                },
                'finish_cut': {
                    'time': round(finish_time, 3),  # minutes
                    'passes': 1,
                    'feed': round(finish_params['feed'], 3),  # mm/rev
                    'feed_rate': round(finish_feed_rate, 1),  # mm/min
                    'spindle_speed': round(finish_params['spindle_speed']),  # RPM
                    'depth': round(finish_params['depth_of_cut'], 3)  # mm
                },
                'cut_parameters': {
                    'start_dia': round(self.start_dia, 2),  # mm
                    'end_dia': round(self.end_dia, 2),  # mm
                    'length': round(self.length, 2),  # mm
                    'total_depth': round(total_depth, 3)  # mm
                },
                'cost': round(cost, 2),  # INR
                'warnings': []
            }
            
            # Add warnings if needed
            if rough_passes > 3:
                result['warnings'].append(
                    f'High number of roughing passes ({rough_passes}) needed. '
                    'Consider using multiple operations or different tooling.'
                )
                
            if rough_feed_rate > 1000:  # mm/min
                result['warnings'].append(
                    f'High roughing feed rate ({rough_feed_rate:.1f} mm/min). '
                    'Check machine and tool capabilities.'
                )
            
            if finish_feed_rate > 800:  # mm/min
                result['warnings'].append(
                    f'High finishing feed rate ({finish_feed_rate:.1f} mm/min). '
                    'Check surface finish requirements.'
                )
                
            # Add material-specific notes
            if self.material_rating < 0.4:
                result['warnings'].append(
                    'Material has low machinability. Consider using specialized tooling or coatings.'
                )
                
            return result
            
        except Exception as e:
            import traceback
            return {
                'error': f'Error in turning calculation: {str(e)}',
                'traceback': traceback.format_exc()
            }
