import math
from .base_operation import BaseOperation

class KnurlingOperation(BaseOperation):
    """Class for knurling operation calculations."""

    def __init__(self, db_params, material_rating, input_dims=None):
        """
        Initialize KnurlingOperation.

        Args:
            db_params: SQLAlchemy model object containing machining parameters
            material_rating (float): Material machinability rating (0-1)
            input_dims (dict): Dictionary with:
                - knurling_length/length (float): Length of knurling surface (mm)
                - workpiece_diameter/diameter (float): Workpiece diameter (mm)
                - knurl_pitch/pitch (float): Knurl pitch (mm)
                - pattern (str, optional): 'straight' or 'diamond' (default: 'straight')
        """
        super().__init__(db_params, material_rating)
        self.knurling_length = 0.0
        self.workpiece_diameter = 0.0
        self.knurl_pitch = 0.0
        self.pattern = 'straight'

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """Set knurling dimensions from input with flexible parameter names."""
        if not input_dims:
            raise ValueError("No dimensions provided")
            
        try:
            # Support both naming conventions
            self.knurling_length = float(
                input_dims.get('knurling_length') or 
                input_dims.get('length')
            )
            self.workpiece_diameter = float(
                input_dims.get('workpiece_diameter') or 
                input_dims.get('diameter')
            )
            self.knurl_pitch = float(
                input_dims.get('knurl_pitch') or 
                input_dims.get('pitch', 1.0)  # Default pitch if not specified
            )
            self.pattern = input_dims.get('pattern', 'straight').lower()
            
        except (TypeError, ValueError) as e:
            raise ValueError(
                "Must provide either (knurling_length, workpiece_diameter, knurl_pitch) or "
                "(length, diameter, pitch). All values must be valid numbers."
            ) from e

        # Validate values
        if self.knurling_length <= 0 or self.workpiece_diameter <= 0 or self.knurl_pitch <= 0:
            raise ValueError("All dimensions must be positive numbers.")
            
        if self.pattern not in ('straight', 'diamond'):
            raise ValueError("Pattern must be 'straight' or 'diamond'.")

    def _get_machining_parameters(self):
        """Return feed and spindle speed for knurling."""
        feed = float(getattr(self.db_params, 'feed_rate_knurl', 0)) or 0.2  # mm/rev
        spindle_speed = float(getattr(self.db_params, 'spindle_speed_knurl', 0)) or 100  # rpm
        passes = int(getattr(self.db_params, 'knurling_passes', 2))  # default 2 passes

        return {
            'feed': feed,
            'spindle_speed': spindle_speed,
            'passes': passes
        }

    def calculate(self, inputs=None):
        """
        Calculate knurling time and cost.
        
        Returns:
            dict: Dictionary containing operation results including time, cost, and parameters
        """
        try:
            # Get machining parameters
            feed = float(getattr(self.params, 'feed_rate_knurling', 0)) or 0.1  # mm/rev
            spindle_speed = float(getattr(self.params, 'spindle_speed_knurling', 0)) or 200.0  # rpm
            
            # Calculate time per pass (minutes) = length / (feed * rpm)
            time_per_pass = self.knurling_length / (feed * spindle_speed)
            
            # For knurling, we typically do 2-4 passes
            passes = 3  # Default number of passes for knurling
            total_time = time_per_pass * passes * 1.1  # 10% safety factor
            
            # Calculate cost
            machine_hour_rate = float(getattr(self.params, 'machine_hour_rate', 150.0))
            cost = (total_time / 60) * machine_hour_rate
            
            # Generate warnings if needed
            warnings = []
            if spindle_speed > 200:
                warnings.append("Spindle speed is relatively high for knurling.")
            if feed > 0.5:
                warnings.append("Feed rate is high; check for tool damage risk.")
            
            return {
                'operation': 'knurling',
                'total_time_minutes': round(total_time, 3),
                'cost': round(cost, 2),
                'material_rating': self.material_rating,
                'parameters': {
                    'knurling_length_mm': round(self.knurling_length, 3),
                    'workpiece_diameter_mm': round(self.workpiece_diameter, 3),
                    'knurl_pitch_mm': round(self.knurl_pitch, 3),
                    'pattern': self.pattern,
                    'feed_mm_rev': round(feed, 3),
                    'spindle_speed_rpm': round(spindle_speed, 1),
                    'passes': passes
                },
                'warnings': warnings
            }

        except Exception as e:
            import traceback
            return {'error': f'Error in knurling calculation: {str(e)}\n{traceback.format_exc()}'}
