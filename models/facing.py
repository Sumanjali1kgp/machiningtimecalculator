import math
from .base_operation import BaseOperation

class FacingOperation(BaseOperation):
    def __init__(self, db_params, material_rating, input_dims=None):
        """
        Args:
            db_params: SQLAlchemy model object containing machining parameters
            material_rating (float): Material machinability rating (0-1)
            input_dims (dict): Dictionary containing 'diameter' and 'depth_of_cut'
        """
        super().__init__(db_params, material_rating)
        
        # Store parameters
        self.db_params = db_params
        self.material_rating = material_rating
        self.db = db_params.query.session  # Get SQLAlchemy session
        
        # Initialize dimensions
        self.diameter = 0.0
        self.depth_of_cut = 0.0
        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        self.diameter = float(input_dims.get('diameter'))
        self.depth_of_cut = float(input_dims.get('depth_of_cut'))
        if self.diameter <= 0 or self.depth_of_cut <= 0:
            raise ValueError("Diameter and depth_of_cut must be positive numbers.")

    def _get_parameters(self, material_id, operation_id, cut_type):
        """Helper method to fetch parameters for a specific cut type"""
        from app import MachiningParameter  # Import here to avoid circular imports
        
        params = self.db.query(MachiningParameter).filter(
            MachiningParameter.material_id == material_id,
            MachiningParameter.operation_id == operation_id,
            MachiningParameter.notes.like(f'%{cut_type}%')
        ).first()
        
        if not params:
            raise ValueError(f"No {cut_type.lower()} parameters found for material_id={material_id}, operation_id={operation_id}")
            
        return params

    def calculate(self, inputs=None):
        # Length of cut
        length_of_cut = self.diameter / 2.0

        # Get material_id and operation_id from the request or use defaults
        material_id = getattr(self, 'material_id', 1)  # Default to 1 if not set
        operation_id = 1  # Assuming 1 is the operation_id for facing

        try:
            # Get rough cut parameters
            rough_params = self._get_parameters(material_id, operation_id, 'Rough cut')
            rough_speed = float(rough_params.spindle_speed_min)
            rough_feed = float(rough_params.feed_rate_min)
            rough_doc = float(rough_params.depth_of_cut_max)

            # Get finish cut parameters
            finish_params = self._get_parameters(material_id, operation_id, 'Finish cut')
            finish_speed = float(finish_params.spindle_speed_max)
            finish_feed = float(finish_params.feed_rate_max)
            finish_doc = float(finish_params.depth_of_cut_min)

            # Calculate semi-finish as average
            semi_speed = (rough_speed + finish_speed) / 2.0
            semi_feed = (rough_feed + finish_feed) / 2.0
            semi_doc = (rough_doc + finish_doc) / 2.0

            # Store params for cost calculation
            self.rough_params = rough_params
            self.finish_params = finish_params
            
        except Exception as e:
            # Fallback to default values if there's an error fetching parameters
            logger = logging.getLogger(__name__)
            logger.error(f"Error fetching parameters: {str(e)}")
            
            # Default values as fallback
            rough_speed = 100.0
            rough_feed = 0.2
            rough_doc = 2.0
            finish_speed = 200.0
            finish_feed = 0.05
            finish_doc = 0.1
            semi_speed = 150.0
            semi_feed = 0.125
            semi_doc = 1.05
            
            logger.warning("Using default machining parameters due to error")

        # Depth and passes
        total_rough_depth = max(0, self.depth_of_cut - semi_doc - finish_doc)
        rough_passes = math.ceil(total_rough_depth / rough_doc) if rough_doc else 0
        actual_rough_doc = total_rough_depth / rough_passes if rough_passes else 0

        semi_passes = 1 if semi_doc > 0 else 0
        finish_passes = 1 if finish_doc > 0 else 0

        # Time per pass
        rough_time = length_of_cut / (rough_speed * rough_feed) if rough_speed and rough_feed else 0
        semi_time = length_of_cut / (semi_speed * semi_feed) if semi_speed and semi_feed else 0
        finish_time = length_of_cut / (finish_speed * finish_feed) if finish_speed and finish_feed else 0

        total_time = ((rough_time * rough_passes) + (semi_time * semi_passes) + (finish_time * finish_passes)) * 1.1
        cost = (total_time / 60.0) * float(getattr(self.db_params, 'machine_hour_rate', 150.0))

        return {
            'operation': 'facing',
            'total_time_minutes': round(total_time, 3),
            'rough_cut': {
                'passes': rough_passes,
                'depth_per_pass': round(actual_rough_doc, 3),
                'spindle_speed': rough_speed,
                'feed': rough_feed,
                'time_per_pass': round(rough_time, 3),
                'total_time': round(rough_time * rough_passes, 3),
            },
            'semi_finish_cut': {
                'passes': semi_passes,
                'depth': round(semi_doc, 3),
                'spindle_speed': semi_speed,
                'feed': semi_feed,
                'time': round(semi_time * semi_passes, 3),
            },
            'finish_cut': {
                'passes': finish_passes,
                'depth': round(finish_doc, 3),
                'spindle_speed': finish_speed,
                'feed': finish_feed,
                'time': round(finish_time * finish_passes, 3),
            },
            'cost': round(cost, 2),
            'warnings': [
                f"{rough_passes} rough passes",
                f"{semi_passes} semi-finish pass",
                f"{finish_passes} finish pass",
            ]
        }
