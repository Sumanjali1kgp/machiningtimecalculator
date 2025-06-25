import math
from .base_operation import BaseOperation

class ThreadingOperation(BaseOperation):
    """Class for threading operation calculations (internal and external)."""

    def __init__(self, db_params, material_rating, input_dims=None):
        """
        Initialize ThreadingOperation.
        
        Args:
            db_params: SQLAlchemy model object containing threading parameters
            material_rating (float): Material machinability rating (0-1)
            input_dims (dict): Dictionary with:
                - diameter (float): Major diameter of the thread in mm
                - length (float): Length of the thread in mm
                - pitch (float): Thread pitch in mm
                - type (str): 'internal' or 'external'
        """
        super().__init__(db_params, material_rating)
        self.diameter = 0.0
        self.length = 0.0
        self.pitch = 0.0
        self.type = 'external'

        if input_dims:
            self.set_dimensions(input_dims)

    def set_dimensions(self, input_dims):
        """
        Set threading parameters from input.
        
        Args:
            input_dims (dict): Dictionary containing thread dimensions with either:
                - Standard names: diameter, length, pitch
                - Alternative names: thread_diameter, thread_length, thread_pitch
                
        Required parameters:
            - diameter/thread_diameter: Thread major diameter in mm
            - length/thread_length: Thread length in mm
            - pitch/thread_pitch: Thread pitch in mm
            
        Optional parameters:
            - type: 'internal' or 'external' (default: 'external')
            - threads_per_pass: Number of passes (default: from DB or 7)
        """
        if not input_dims:
            raise ValueError("No dimensions provided")
            
        # Get values with clear error messages
        diameter = input_dims.get('diameter') or input_dims.get('thread_diameter')
        length = input_dims.get('length') or input_dims.get('thread_length')
        pitch = input_dims.get('pitch') or input_dims.get('thread_pitch')
        
        # Check for missing required parameters
        missing = []
        if diameter is None:
            missing.append("diameter/thread_diameter")
        if length is None:
            missing.append("length/thread_length")
        if pitch is None:
            missing.append("pitch/thread_pitch")
            
        if missing:
            raise ValueError(
                f"Missing required parameters: {', '.join(missing)}. "
                "Please provide either standard (diameter, length, pitch) or "
                "alternative (thread_diameter, thread_length, thread_pitch) parameters."
            )
            
        try:
            # Convert and set values
            self.diameter = float(diameter)
            self.length = float(length)
            self.pitch = float(pitch)
            self.type = input_dims.get('type', 'external').lower()
            
            # Get threads per pass if provided, otherwise use default from DB or fallback to 7
            self.threads_per_pass = int(
                input_dims.get('threads_per_pass') or 
                getattr(self.db_params, 'threading_passes', 7)
            )
            
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Invalid parameter values. "
                "diameter, length, and pitch must be valid numbers. "
                f"Got: diameter={diameter}, length={length}, pitch={pitch}"
            ) from e

        # Validate values
        if self.diameter <= 0 or self.length <= 0 or self.pitch <= 0:
            raise ValueError("All dimensions (diameter, length, pitch) must be positive.")
            
        if self.threads_per_pass <= 0:
            raise ValueError("Threads per pass must be a positive integer.")
            
        if self.type not in ('internal', 'external'):
            raise ValueError("Thread type must be 'internal' or 'external'.")

    def _get_machining_parameters(self):
        """Get feed and spindle speed for threading."""
        feed = float(getattr(self.db_params, 'feed_rate_thread', 0)) or self.pitch
        spindle_speed = float(getattr(self.db_params, 'spindle_speed_thread', 0)) or float(self.db_params.spindle_speed_min)
        passes = int(getattr(self.db_params, 'threading_passes', 7))  # Default 7 passes

        return {
            'feed': feed,  # Usually equals pitch
            'spindle_speed': spindle_speed,
            'passes': passes
        }

    def calculate(self, inputs=None):
        try:
            params = self._get_machining_parameters()
            feed = params['feed']
            spindle_speed = params['spindle_speed']
            passes = params['passes']

            # Threading is usually done at pitch feed rate
            single_pass_time = self.length / (feed * spindle_speed)
            total_time = single_pass_time * passes
            total_time *= 1.1  # 10% safety margin

            # Cost calculation
            self.MACHINE_HOUR_RATE = getattr(self.db_params, 'machine_hour_rate', 150.0)
            cost = (total_time / 60) * self.MACHINE_HOUR_RATE

            # Warnings
            warnings = []
            if feed != self.pitch:
                warnings.append(f"Thread feed ({feed} mm) does not match pitch ({self.pitch} mm).")
            if spindle_speed > 800:
                warnings.append("Spindle speed for threading is unusually high.")

            return {
                'operation': 'threading',
                'thread_type': self.type,
                'total_time_minutes': round(total_time, 3),
                'parameters': {
                    'diameter': self.diameter,
                    'length': self.length,
                    'pitch': self.pitch,
                    'passes': passes,
                    'feed': round(feed, 3),
                    'spindle_speed': round(spindle_speed, 0),
                    'time_per_pass': round(single_pass_time, 3)
                },
                'cost': round(cost, 2),
                'warnings': warnings
            }

        except Exception as e:
            import traceback
            return {'error': f'Error in threading calculation: {str(e)}\n{traceback.format_exc()}'}
