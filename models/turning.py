import math
from .base_operation import BaseOperation

class TurningOperation(BaseOperation):
    """Class for turning operation calculations with rough and finish cuts."""

    def __init__(self, db_params, material_rating, input_dims=None):
        """
        Initialize TurningOperation.
        
        Args:
            db_params: SQLAlchemy model object containing machining parameters
            material_rating (float): Material machinability rating (0-1)
            input_dims (dict, optional): Dictionary containing:
                - start_diameter or initial_diameter (float): Initial workpiece diameter in mm
                - end_diameter or final_diameter (float): Final workpiece diameter in mm
                - length (float): Length of the turning cut in mm
        """
        # Initialize the base class with required parameters
        super().__init__(db_params, material_rating)
        
        # Store parameters
        self.db_params = db_params
        self.material_rating = material_rating
        
        # Initialize dimensions with default values
        self.initial_diameter = 0
        self.final_diameter = 0
        self.length = 0
        self.finish_doc = 0.2  # mm default finish depth of cut
        
        # Set dimensions if provided
        if input_dims is not None:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """Set the turning dimensions from user input."""
        try:
            # Handle both 'start_diameter'/'end_diameter' and 'initial_diameter'/'final_diameter' formats
            self.initial_diameter = float(input_dims.get('start_diameter') or input_dims['initial_diameter'])
            self.final_diameter = float(input_dims.get('end_diameter') or input_dims['final_diameter'])
            self.length = float(input_dims['length'])
        except (KeyError, ValueError) as e:
            raise ValueError("start_diameter/end_diameter (or initial_diameter/final_diameter) and length are required and must be numbers.") from e
        
        if self.initial_diameter <= self.final_diameter:
            raise ValueError("Initial/start diameter must be larger than final/end diameter.")
        if self.length <= 0:
            raise ValueError("Length must be a positive number.")
            
        # Update input_dims for consistency
        input_dims.update({
            'start_diameter': self.initial_diameter,
            'end_diameter': self.final_diameter,
            'initial_diameter': self.initial_diameter,
            'final_diameter': self.final_diameter
        })
    
    def _get_machining_parameters(self, cut_type='rough'):
        if not self.db_params:
            raise ValueError("No machining params in db_params")

        if cut_type == 'rough':
            params = {
            'depth_of_cut': float(getattr(self.db_params, 'depth_of_cut_max', 0)),
            'spindle_speed': float(getattr(self.db_params, 'spindle_speed_min', 0)),
            'feed': float(getattr(self.db_params, 'feed_rate_max', 0))
        }
        elif cut_type == 'finish':
            params = {
            'depth_of_cut': float(getattr(self.db_params, 'depth_of_cut_min', 0)),
            'spindle_speed': float(getattr(self.db_params, 'spindle_speed_max', 0)),
            'feed': float(getattr(self.db_params, 'feed_rate_min', 0))
        }
        else:
            raise ValueError(f"Unknown cut_type: {cut_type}")

        return params

    def calculate(self, inputs=None):
        try:
            # Compute radial reduction
            diameter_reduction = self.initial_diameter - self.final_diameter
            radial_reduction = diameter_reduction / 2

            # Get machining parameters (based on new logic)
            rough_params = self._get_machining_parameters('rough')
            finish_params = self._get_machining_parameters('finish')
        
            # Compute total roughing depth (leaving some stock for finish cut)
            rough_depth_total = max(0, radial_reduction - finish_params['depth_of_cut'])

            # Compute number of passes and depth per pass for roughing
            rough_passes = max(1, math.ceil(rough_depth_total / rough_params['depth_of_cut']))
            actual_rough_doc = rough_depth_total / rough_passes if rough_passes > 0 else 0

            # Time per pass and total roughing time
            rough_time_per_pass = self.length / (rough_params['feed'] * rough_params['spindle_speed'])
            total_rough_time = rough_time_per_pass * rough_passes

            # Time for finish cut
            finish_time = 0
            if finish_params['depth_of_cut'] > 0:
                finish_time = self.length / (finish_params['feed'] * finish_params['spindle_speed'])

            # Total time + 10% safety factor
            total_cutting_time = (total_rough_time + finish_time) * 1.1

            # Cost calculation
            self.MACHINE_HOUR_RATE = getattr(self.db_params, 'machine_hour_rate', 150.0)
            cost = (total_cutting_time / 60) * self.MACHINE_HOUR_RATE

            # Generate warnings
            warnings = []
            if rough_passes > 1:
                warnings.append(f"Multiple rough passes ({rough_passes}) used.")
            if rough_params['feed'] * rough_params['spindle_speed'] > 1000:
                warnings.append(f"Rough cut feed rate is high ({rough_params['feed'] * rough_params['spindle_speed']} mm/min).")
            if finish_params['feed'] * finish_params['spindle_speed'] > 1000:
                warnings.append(f"Finish cut feed rate is high ({finish_params['feed'] * finish_params['spindle_speed']} mm/min).")

            # Return all results
            return {
                'operation': 'turning',
                'total_time_minutes': round(total_cutting_time, 3),
                'rough_cut': {
                    'passes': rough_passes,
                    'depth_per_pass': round(actual_rough_doc, 3),
                    'feed': round(rough_params['feed'], 3),
                    'spindle_speed': round(rough_params['spindle_speed'], 0),
                    'time_per_pass': round(rough_time_per_pass, 3),
                    'total_time': round(total_rough_time, 3)
                },
                'finish_cut': {
                    'depth': round(finish_params['depth_of_cut'], 3),
                    'feed': round(finish_params['feed'], 3),
                    'spindle_speed': round(finish_params['spindle_speed'], 0),
                    'time': round(finish_time, 3)
                },
                'cost': round(cost, 2),
                'warnings': warnings,
                'machine_hour_rate': self.MACHINE_HOUR_RATE,
                'initial_diameter': self.initial_diameter,
                'final_diameter': self.final_diameter,
                'length': self.length,
            }

        except Exception as e:
            import traceback
            return {'error': f'Error in turning calculation: {str(e)}\n{traceback.format_exc()}'}
