import math
from .base_operation import BaseOperation

class BoringOperation(BaseOperation):
    """Class for boring operation calculations with rough and finish cuts."""

    def __init__(self, db_params, material_rating, input_dims=None):
        """
        Initialize BoringOperation.
        
        Args:
            db_params: SQLAlchemy model object containing machining parameters
            material_rating (float): Material machinability rating (0-1)
            input_dims (dict): Dictionary with:
                - initial_diameter (float): Starting bore diameter (mm)
                - final_diameter (float): Final bore diameter (mm)
                - depth (float): Bore depth (length of boring pass, mm)
        """
        super().__init__(db_params, material_rating)
        self.db_params = db_params
        self.material_rating = material_rating

        # Initialize with defaults
        self.initial_diameter = 0.0
        self.final_diameter = 0.0
        self.depth = 0.0
        self.finish_doc = 0.2  # Default finish pass in mm

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """
        Set bore dimensions from input.
        
        Supports two parameter naming conventions:
        1. initial_diameter, final_diameter, depth
        2. hole_diameter (initial_diameter), hole_depth (depth), cutting_depth (final_diameter - initial_diameter)
        """
        try:
            # Try to get values using both naming conventions
            initial_diameter = input_dims.get('initial_diameter') or input_dims.get('hole_diameter')
            depth = input_dims.get('depth') or input_dims.get('hole_depth')
            
            if 'final_diameter' in input_dims:
                final_diameter = input_dims['final_diameter']
            elif 'hole_diameter' in input_dims and 'cutting_depth' in input_dims:
                final_diameter = input_dims['hole_diameter'] + 2 * float(input_dims['cutting_depth'])
            else:
                raise KeyError("Missing required parameters")
                
            # Convert and validate
            self.initial_diameter = float(initial_diameter)
            self.final_diameter = float(final_diameter)
            self.depth = float(depth)
            
        except (KeyError, ValueError) as e:
            raise ValueError(
                "Must provide either (initial_diameter, final_diameter, depth) "
                "or (hole_diameter, hole_depth, cutting_depth)."
            ) from e

        # Validate dimensions
        if self.initial_diameter <= 0 or self.final_diameter <= 0:
            raise ValueError("Diameters must be positive numbers.")
            
        if self.initial_diameter >= self.final_diameter:
            raise ValueError("Final diameter must be greater than initial diameter.")
            
        if self.depth <= 0:
            raise ValueError("Depth must be a positive number.")

    def _get_machining_parameters(self, cut_type='rough'):
        """
        Retrieve machining parameters based on cut type.
        
        Args:
            cut_type (str): Type of cut ('rough' or 'finish')
            
        Returns:
            dict: Dictionary containing depth_of_cut, feed, and spindle_speed
            
        Raises:
            ValueError: If required parameters are missing or invalid
        """
        if not self.db_params:
            raise ValueError("No database parameters provided.")
            
        try:
            # Get base parameters
            params = {
                'depth_of_cut': float(getattr(self.db_params, f'depth_of_cut_{cut_type}', 0)),
                'feed': float(getattr(self.db_params, f'feed_rate_{cut_type}', 0)),
                'spindle_speed': float(getattr(self.db_params, f'spindle_speed_{cut_type}', 0)),
            }

            # Fallback to min/max if cut-specific values are missing
            if params['depth_of_cut'] <= 0:
                params['depth_of_cut'] = float(getattr(
                    self.db_params, 
                    'depth_of_cut_max' if cut_type == 'rough' else 'depth_of_cut_min', 
                    0
                ))
                
            if params['feed'] <= 0:
                params['feed'] = float(getattr(
                    self.db_params, 
                    'feed_rate_max' if cut_type == 'rough' else 'feed_rate_min', 
                    0
                ))
                
            if params['spindle_speed'] <= 0:
                params['spindle_speed'] = float(getattr(
                    self.db_params, 
                    'spindle_speed_min', 
                    0
                ))
                
            # Apply material rating to spindle speed (50-100% of calculated speed)
            if params['spindle_speed'] > 0:
                params['spindle_speed'] *= (0.5 + (self.material_rating * 0.5))
                
            return params
            
        except (AttributeError, ValueError) as e:
            raise ValueError(
                f"Invalid or missing machining parameters for {cut_type} cut. "
                f"Required: depth_of_cut, feed_rate, spindle_speed. Error: {str(e)}"
            ) from e

    def calculate(self, inputs=None):
        """
        Calculate boring operation time and cost.
        
        Returns:
            dict: Dictionary containing operation results including time, cost, and parameters
        """
        try:
            # Total radial stock to remove
            diameter_increase = self.final_diameter - self.initial_diameter
            if diameter_increase <= 0:
                raise ValueError("Final diameter must be greater than initial diameter.")
                
            radial_increase = diameter_increase / 2

            # Get machining parameters
            rough_params = self._get_machining_parameters('rough')
            finish_params = self._get_machining_parameters('finish')

            # Ensure finish cut doesn't exceed total stock
            finish_doc = min(finish_params['depth_of_cut'], radial_increase)
            rough_depth_total = max(0, radial_increase - finish_doc)
            
            # Calculate roughing passes
            max_rough_doc = max(rough_params['depth_of_cut'], 0.1)  # Ensure minimum DOC
            rough_passes = max(1, int(math.ceil(rough_depth_total / max_rough_doc)))
            actual_rough_doc = rough_depth_total / rough_passes if rough_passes > 0 else 0

            # Time calculations
            feed_rate_rough = rough_params['feed'] * rough_params['spindle_speed']  # mm/min
            rough_time_per_pass = self.depth / feed_rate_rough if feed_rate_rough > 0 else 0
            total_rough_time = rough_time_per_pass * rough_passes

            # Finish pass time
            finish_time = 0
            if finish_doc > 0:
                feed_rate_finish = finish_params['feed'] * finish_params['spindle_speed']
                finish_time = self.depth / feed_rate_finish if feed_rate_finish > 0 else 0

            # Total time with safety factor
            total_cutting_time = (total_rough_time + finish_time) * 1.1  # 10% safety

            # Cost calculation
            machine_hour_rate = getattr(self.db_params, 'machine_hour_rate', 150.0)
            cost = (total_cutting_time / 60) * machine_hour_rate

            # Generate warnings
            warnings = []
            if rough_passes > 3:
                warnings.append(f"High number of roughing passes ({rough_passes}) - consider increasing depth of cut.")
                
            if feed_rate_rough > 1000:
                warnings.append(f"High rough cut feed rate: {feed_rate_rough:.1f} mm/min")
                
            if finish_doc > 0 and finish_params['feed'] * finish_params['spindle_speed'] > 800:
                warnings.append("High finish cut feed rate.")
                
            if actual_rough_doc < 0.1:
                warnings.append("Very small roughing depth of cut - consider adjusting parameters.")

            # Prepare result
            result = {
                'operation': 'boring',
                'total_time_minutes': round(total_cutting_time, 3),
                'material_rating': self.material_rating,
                'machine_hour_rate': machine_hour_rate,
                'rough_cut': {
                    'passes': rough_passes,
                    'depth_per_pass_mm': round(actual_rough_doc, 3),
                    'feed_mm_per_rev': round(rough_params['feed'], 3),
                    'spindle_speed_rpm': round(rough_params['spindle_speed'], 0),
                    'feed_rate_mm_per_min': round(feed_rate_rough, 1),
                    'time_per_pass_min': round(rough_time_per_pass, 3),
                    'total_time_min': round(total_rough_time, 3),
                },
                'finish_cut': {
                    'depth_mm': round(finish_doc, 3),
                    'feed_mm_per_rev': round(finish_params['feed'], 3),
                    'spindle_speed_rpm': round(finish_params['spindle_speed'], 0),
                    'feed_rate_mm_per_min': round(finish_params['feed'] * finish_params['spindle_speed'], 1),
                    'time_min': round(finish_time, 3),
                },
                'cost': round(cost, 2),
                'warnings': warnings
            }
            
            return result

        except Exception as e:
            error_msg = f'Error in boring calculation: {str(e)}'
            import traceback
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return {
                'error': error_msg,
                'operation': 'boring',
                'parameters': {
                    'initial_diameter_mm': getattr(self, 'initial_diameter', 0),
                    'final_diameter_mm': getattr(self, 'final_diameter', 0),
                    'depth_mm': getattr(self, 'depth', 0)
                }
            }
