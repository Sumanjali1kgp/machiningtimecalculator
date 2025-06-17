from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from models import (
    TurningOperation, FacingOperation, 
    DrillingOperation, MillingOperation
)

class MachiningCalculator:
    """
    Main calculator class that delegates to specific operation classes.
    This follows the Strategy design pattern where each operation is a strategy.
    """
    
    def __init__(self, db_params, material_rating, material_id=None):
        """
        Initializes the calculator with parameters from the database.
        
        Args:
            db_params (MachiningParameter): The SQLAlchemy object with machining parameters.
            material_rating (float): The machinability rating of the material (0-1).
            material_id (int, optional): The ID of the material in the database.
        """
        self.params = db_params
        self.material_rating = material_rating
        self.material_id = material_id or 1  # Default to 1 if not provided
        
        # Initialize operation handlers with required parameters
        self.operations = {
            'turning': TurningOperation(db_params, self.material_id, material_rating, None, None),
            'facing': FacingOperation(db_params, self.material_id, material_rating, None, None),
            'drilling': DrillingOperation(db_params, self.material_id, material_rating, None, None),
            'milling': MillingOperation(db_params, self.material_id, material_rating, None, None)
        }

    def calculate_machining_parameters(self, operation_name, user_inputs):
        """
        Calculate all machining parameters including time and cost.
        
        Args:
            operation_name (str): Name of the operation (e.g., 'turning', 'drilling')
            user_inputs (dict): Dictionary containing user inputs like dimensions
            
        Returns:
            dict: Dictionary containing all calculated parameters
            
        Raises:
            ValueError: If the operation is not supported
        """
        op_name = operation_name.lower()
        
        if op_name not in self.operations:
            raise ValueError(f"Unsupported operation: {operation_name}")
            
        # Delegate to the appropriate operation handler
        operation = self.operations[op_name]
        return operation.calculate(user_inputs)
    
    def calculate_time(self, operation_name, user_inputs):
        """
        Calculate machining time for the specified operation.
        
        Args:
            operation_name (str): Name of the operation (e.g., 'turning', 'drilling')
            user_inputs (dict): Dictionary containing user inputs like dimensions
            
        Returns:
            tuple: A tuple containing the raw machining time and total time
            
        Note:
            This is a simplified version that uses the main calculation method
            and extracts the time from the result. In a real application, you might
            want to implement more specific time calculations.
        """
        result = self.calculate_machining_parameters(operation_name, user_inputs)
        if 'error' in result:
            raise ValueError(result['error'])
            
        machining_time = result.get('machining_time', 0)
        total_time = machining_time * (1 + self.material_rating * 0.1)  # Add material factor
        
        return machining_time, total_time
