import math
from abc import ABC, abstractmethod

class BaseOperation(ABC):
    """Base class for all machining operations."""
    
    MACHINE_HOUR_RATE = 1500  # INR per hour
    APPROACH = 10  # mm
    OVERRUN = 10   # mm
    SAFETY_FACTOR = 1.2  # 20% safety factor for time estimation
    
    def __init__(self, db_params, material_rating):
        """
        Initialize the operation with database parameters and material rating.
        
        Args:
            db_params: Database parameters for the operation
            material_rating (float): Material machinability rating (0-1)
        """
        self.params = db_params
        self.material_rating = material_rating
    
    @abstractmethod
    def calculate(self, inputs):
        """
        Calculate operation parameters.
        
        Args:
            inputs (dict): User inputs for the operation
            
        Returns:
            dict: Calculated parameters
        """
        pass
    
    def _get_cutting_speed(self):
        """Get recommended cutting speed based on material."""
        base_speed = (self.params.spindle_speed_min + self.params.spindle_speed_max) / 2
        return base_speed * self.material_rating
    
    def _get_feed_rate(self):
        """Get recommended feed rate based on material."""
        base_feed = (self.params.feed_rate_min + self.params.feed_rate_max) / 2
        return base_feed * (0.5 + self.material_rating / 2)
    
    def _check_limits(self, rpm, feed, depth_of_cut):
        """Check if parameters are within machine limits."""
        warnings = []
        
        if rpm > self.params.spindle_speed_max:
            warnings.append(f"RPM ({rpm:.0f}) exceeds maximum recommended ({self.params.spindle_speed_max:.0f})")
        if feed > self.params.feed_rate_max:
            warnings.append(f"Feed rate ({feed:.2f}) exceeds maximum recommended ({self.params.feed_rate_max:.2f})")
        if depth_of_cut > self.params.depth_of_cut_max:
            warnings.append(f"Depth of cut ({depth_of_cut:.2f}mm) exceeds maximum recommended ({self.params.depth_of_cut_max:.2f}mm)")
            
        return warnings if warnings else ["All parameters within recommended limits"]
