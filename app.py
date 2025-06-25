from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from machining_calculator import MachiningCalculator
import os
from typing import Optional, Any, Tuple, Dict, Union
import logging
import importlib
from datetime import datetime
from typing import Dict, Type, Any, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-please-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///machining.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Database Models
class Material(db.Model):
    __tablename__ = 'Materials'
    material_id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(100), nullable=False)
    machinability_rating = db.Column(db.Float)
    recommended_tool = db.Column(db.String(100))
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'material_id': self.material_id,
            'material_name': self.material_name,
            'machinability_rating': self.machinability_rating,
            'recommended_tool': self.recommended_tool,
            'notes': self.notes
        }

class Operation(db.Model):
    __tablename__ = 'Operations'
    operation_id = db.Column(db.Integer, primary_key=True)
    operation_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'operation_id': self.operation_id,
            'operation_name': self.operation_name,
            'description': self.description
        }

class MachiningParameter(db.Model):
    __tablename__ = 'MachiningParameters'
    param_id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('Materials.material_id'))
    operation_id = db.Column(db.Integer, db.ForeignKey('Operations.operation_id'))
    spindle_speed_min = db.Column(db.Integer)
    spindle_speed_max = db.Column(db.Integer)
    feed_rate_min = db.Column(db.Float)
    feed_rate_max = db.Column(db.Float)
    depth_of_cut_min = db.Column(db.Float)
    depth_of_cut_max = db.Column(db.Float)
    notes = db.Column(db.Text)

class OperationExtraTime(db.Model):
    __tablename__ = 'OperationExtraTimes'
    operation_id = db.Column(db.Integer, primary_key=True)
    setup_time_min = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'operation_id': self.operation_id,
            'setup_time_min': self.setup_time_min
        }

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {str(error)}")
    return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500

# API Endpoints
@app.route('/api/materials', methods=['GET'])
def get_materials():
    """Get all available materials"""
    try:
        materials = Material.query.all()
        return jsonify([mat.to_dict() for mat in materials])
    except Exception as e:
        logger.error(f"Error fetching materials: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch materials'}), 500

@app.route('/api/operations', methods=['GET'])
def get_operations():
    """Get all available operations"""
    try:
        operations = Operation.query.all()
        return jsonify([op.to_dict() for op in operations])
    except Exception as e:
        logger.error(f"Error fetching operations: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch operations'}), 500

@app.route('/api/parameters/<int:material_id>/<int:operation_id>', methods=['GET'])
def get_parameters(material_id, operation_id):
    """Get machining parameters for a specific material and operation"""
    try:
        params = MachiningParameter.query.filter_by(
            material_id=material_id,
            operation_id=operation_id
        ).first()
        
        if not params:
            return jsonify({
                'status': 'error',
                'message': 'No parameters found for the given material and operation'
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': params.to_dict()
        })
    except Exception as e:
        logger.error(f"Error fetching parameters: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch parameters'}), 500

@app.route('/get_setup_time')
def get_setup_time():
    operation_id = request.args.get('operation_id')
    if not operation_id:
        return jsonify({'error': 'No operation_id provided'}), 400

    try:
        operation_id = int(operation_id)
        extra_time = OperationExtraTime.query.get(operation_id)
        if extra_time and extra_time.setup_time_min is not None:
            return jsonify({'setup_time': extra_time.setup_time_min})
        return jsonify({'setup_time': 15.0})  # Default setup time of 15 minutes if not specified
    except ValueError:
        return jsonify({'error': 'Invalid operation_id'}), 400
    except Exception as e:
        app.logger.error(f"Error fetching setup time: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """
    Calculate machining parameters, time, and cost
    
    Expected JSON payload:
    {
        'material_id': int,
        'operation_id': int,
        'operation_name': str,
        'dimensions': {
            'diameter': float,  // for turning, facing, drilling
            'length': float,    // for turning, milling
            'width': float,     // for milling
            'depth': float,     // for drilling, milling
            'depth_of_cut': float,  // optional, will use default if not provided
            'total_depth': float    // optional, for multiple passes
        }
    }
    """
    try:
        data = request.get_json()
        logger.info(f"Calculation request: {data}")
        
        # Validate required fields
        required_fields = ['material_id', 'operation_id', 'operation_name', 'dimensions']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Get material and operation
        material = Material.query.get(data['material_id'])
        if not material:
            return jsonify({
                'status': 'error',
                'message': f'Material with ID {data["material_id"]} not found in database. Please select a valid material.'
            }), 404
            
        operation = Operation.query.get(data['operation_id'])
        if not operation:
            return jsonify({
                'status': 'error',
                'message': f'Operation with ID {data["operation_id"]} not found in database.'
            }), 404
        
        # Get machining parameters
        params = MachiningParameter.query.filter_by(
            material_id=data['material_id'],
            operation_id=data['operation_id']
        ).first()
        
        if not params:
            # Get available materials for this operation to suggest alternatives
            available_materials = db.session.query(Material.material_name)\
                .join(MachiningParameter, MachiningParameter.material_id == Material.material_id)\
                .filter(MachiningParameter.operation_id == data['operation_id'])\
                .all()
                
            available_materials = [m[0] for m in available_materials]
            
            suggestion = ''
            if available_materials:
                suggestion = f' Available materials for this operation: {", ".join(available_materials)}.'
            
            return jsonify({
                'status': 'error',
                'message': f'No machining parameters found for {material.material_name} with {operation.operation_name}.{suggestion}'
            }), 404
        
        # Initialize the appropriate operation class based on operation_name
        operation_name = data['operation_name'].lower()
        
        # Dictionary mapping operation names to their respective operation classes
        operation_classes = {
            'facing': ('models.facing', 'FacingOperation'),
            'turning': ('models.turning', 'TurningOperation'),
            'drilling': ('models.drilling', 'DrillingOperation'),
            'boring': ('models.boring', 'BoringOperation'),
            'reaming': ('models.reaming', 'ReamingOperation'),
            'grooving': ('models.grooving', 'GroovingOperation'),
            'threading': ('models.threading', 'ThreadingOperation'),
            'knurling': ('models.knurling', 'KnurlingOperation'),
            'parting': ('models.parting', 'PartingOperation')
        }
        
        # Check if we have a specialized operation class
        if operation_name in operation_classes:
            module_path, class_name = operation_classes[operation_name]
            try:
                # Dynamically import the module and get the class
                module = __import__(module_path, fromlist=[class_name])
                operation_class = getattr(module, class_name)
                # Initialize and calculate
                operation = operation_class(params, material.machinability_rating or 0.5, data['dimensions'])
                result = operation.calculate()
            except (ImportError, AttributeError) as e:
                logger.error(f"Error initializing {class_name}: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to initialize {operation_name} operation',
                    'field': 'operation'
                }), 500
        else:
            # Default to generic calculator for operations without a specialized class
            calculator = MachiningCalculator(params, material.machinability_rating or 0.5)
            result = calculator.calculate_machining_parameters(
                operation_name=operation_name,
                user_inputs=data['dimensions']
            )
            
        if 'error' in result:
            return jsonify({
                'status': 'error',
                'message': result['error'],
                'field': 'calculation'
            }), 400
            
        # Add metadata to result
        result.update({
            'material': material.material_name,
            'operation': operation_name,
            'timestamp': datetime.utcnow().isoformat(),
            'machine_hour_rate': getattr(calculator, 'MACHINE_HOUR_RATE', 0) if 'calculator' in locals() else 0
            })
            
        # Return the time in the format expected by the frontend
        time_value = result.get('total_time_minutes', 0)
        logger.info(f"Calculation successful: {result}")
            
        return jsonify({
            'status': 'success',
            'time': time_value,
            'data': result
            })
            
    except Exception as e:
        logger.error(f"Error in calculation: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Calculation error: {str(e)}',
            'field': 'calculation'
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing calculation request: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'An error occurred while processing your request: {str(e)}',
            'field': 'server_error'
        }), 500
    

# Frontend Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lathe')
def lathe():
    return render_template('lathe.html')

@app.route('/milling')
def milling():
    return render_template('milling.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
    app.run(debug=True)
