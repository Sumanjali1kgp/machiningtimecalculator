import math
from .base_operation import BaseOperation

class DrillingOperation(BaseOperation):
    """Class for drilling operation calculations with peck drilling support."""

    def __init__(self, db_params, material_rating, input_dims=None):
        """
        Initialize DrillingOperation.
        
        Args:
            db_params: SQLAlchemy model object containing machining parameters
            material_rating (float): Material machinability rating (0-1)
            input_dims (dict): Dictionary containing:
                - diameter (float): Drill diameter in mm (required)
                - depth (float): Hole depth in mm (required)
                - peck_depth (float, optional): Depth per peck in mm (default: 3x diameter)
        """
        super().__init__(db_params, material_rating)
        self.db_params = db_params
        self.material_rating = material_rating
        
        # Initialize with defaults
        self.diameter = 0.0
        self.depth = 0.0
        self.peck_depth = 0.0  # Will be set based on diameter if not provided
        self.retract_distance = 2.0  # Standard retract distance in mm
        
        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """
        Set drilling dimensions from input.
        
        Args:
            input_dims (dict): Dictionary containing:
                - diameter or hole_diameter (float): Drill diameter in mm
                - depth or hole_depth (float): Hole depth in mm
                - peck_depth (float, optional): Depth per peck in mm
        """
        try:
            # Support both 'diameter' and 'hole_diameter' for backward compatibility
            self.diameter = float(
                input_dims.get('diameter') or 
                input_dims.get('hole_diameter')
            )
            # Support both 'depth' and 'hole_depth' for backward compatibility
            self.depth = float(
                input_dims.get('depth') or 
                input_dims.get('hole_depth')
            )
            
            # Set peck depth to 3x diameter if not provided, but not more than 15mm
            default_peck = min(3 * self.diameter, 15.0)
            self.peck_depth = float(input_dims.get('peck_depth', default_peck))
            
            # Ensure retract distance is positive and reasonable
            self.retract_distance = max(1.0, min(5.0, float(input_dims.get('retract_distance', 2.0))))
            
        except (KeyError, ValueError) as e:
            required_keys = [
                'diameter', 'hole_diameter', 
                'depth', 'hole_depth'
            ]
            if any(key in str(e) for key in required_keys):
                raise ValueError(
                    "Both diameter (or hole_diameter) and depth (or hole_depth) "
                    "must be provided as positive numbers."
                ) from e
            raise ValueError("Invalid input values. Please check your dimensions.") from e

        # Validate all dimensions
        if self.diameter <= 0 or self.depth <= 0 or self.peck_depth <= 0:
            raise ValueError("Diameter, depth, and peck depth must be positive values.")
            
        if self.peck_depth < self.diameter * 0.5:
            raise ValueError(f"Peck depth ({self.peck_depth}mm) is too small for drill diameter {self.diameter}mm.")
            
        if self.peck_depth > 20.0:  # Safety limit
            raise ValueError(f"Peck depth ({self.peck_depth}mm) exceeds maximum allowed (20mm).")

    def _get_machining_parameters(self):
        """
        Retrieve feed and spindle speed for drilling.
        
        Returns:
            dict: Dictionary containing feed (mm/rev) and spindle_speed (RPM)
        """
        if not self.db_params:
            raise ValueError("No database parameters provided.")
            
        # Get feed rate in mm/rev
        feed = float(getattr(self.db_params, 'feed_rate_drill', 0))
        if feed <= 0:
            feed = float(getattr(self.db_params, 'feed_rate_min', 0.1))
            
        # Calculate spindle speed (RPM) using cutting speed if available
        cutting_speed = float(getattr(self.db_params, 'cutting_speed', 0))
        if cutting_speed > 0 and self.diameter > 0:
            # Calculate RPM from cutting speed: RPM = (Cutting Speed * 1000) / (π * Diameter)
            spindle_speed = (cutting_speed * 1000) / (math.pi * self.diameter)
            # Apply material rating (0-1) to adjust speed
            spindle_speed *= (0.5 + (self.material_rating * 0.5))  # Scale between 50-100% of calculated speed
        else:
            spindle_speed = float(getattr(self.db_params, 'spindle_speed_drill', 0))
            if spindle_speed <= 0:
                spindle_speed = float(getattr(self.db_params, 'spindle_speed_min', 500))
        
        return {
            'feed': round(feed, 3),  # mm/rev
            'spindle_speed': round(spindle_speed, 1)  # RPM
        }

    def calculate(self, inputs=None):
        """
        Calculate drilling time and cost.
        
        Returns:
            dict: Dictionary containing operation results including time, cost, and parameters
        """
        try:
            # Get machining parameters
            params = self._get_machining_parameters()
            feed = params['feed']  # mm/rev
            spindle_speed = params['spindle_speed']  # RPM
            
            # Calculate feed rate in mm/min
            feed_rate_mm_min = feed * spindle_speed
            
            # Calculate number of pecks needed
            peck_count = max(1, math.ceil(self.depth / self.peck_depth))
            
            # Calculate total travel distance (including retracts)
            total_travel = self.depth + (self.retract_distance * (peck_count - 1))
            
            # Calculate cutting time (minutes) = total travel / feed rate
            cutting_time = total_travel / feed_rate_mm_min
            
            # Add 10% safety factor
            total_time = cutting_time * 1.1
            
            # Calculate cost
            machine_hour_rate = getattr(self.db_params, 'machine_hour_rate', 150.0)
            cost = (total_time / 60) * machine_hour_rate
            
            # Generate warnings if needed
            warnings = []
            if feed_rate_mm_min > 1000:
                warnings.append(f"High feed rate: {feed_rate_mm_min:.1f} mm/min")
            if peck_count > 1:
                warnings.append(f"Using {peck_count} pecks with {self.retract_distance}mm retract")
            if self.diameter < 3.0 and feed > 0.1:
                warnings.append("Consider reducing feed rate for small diameter drills")
                
            # Prepare result
            result = {
                'operation': 'drilling',
                'total_time_minutes': round(total_time, 3),
                'cost': round(cost, 2),
                'material_rating': self.material_rating,
                'machine_hour_rate': machine_hour_rate,
                'parameters': {
                    'diameter_mm': round(self.diameter, 2),
                    'depth_mm': round(self.depth, 2),
                    'peck_depth_mm': round(self.peck_depth, 2),
                    'feed_mm_per_rev': round(feed, 3),
                    'spindle_speed_rpm': round(spindle_speed, 1),
                    'feed_rate_mm_per_min': round(feed_rate_mm_min, 1),
                    'peck_count': peck_count,
                    'total_travel_mm': round(total_travel, 2)
                },
                'warnings': warnings
            }
            
            return result
            
        except Exception as e:
            error_msg = f'Error in drilling calculation: {str(e)}'
            import traceback
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return {
                'error': error_msg,
                'operation': 'drilling',
                'parameters': {
                    'diameter_mm': getattr(self, 'diameter', 0),
                    'depth_mm': getattr(self, 'depth', 0)
                }
            }
