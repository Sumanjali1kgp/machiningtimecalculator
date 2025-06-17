from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from machining_calculator import MachiningCalculator
import os
import logging
from datetime import datetime

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
        return jsonify([{
            'id': m.material_id,
            'name': m.material_name,
            'rating': m.machinability_rating,
            'tool': m.recommended_tool,
            'notes': m.notes
        } for m in materials])
    except Exception as e:
        logger.error(f"Error fetching materials: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch materials'}), 500

@app.route('/api/operations', methods=['GET'])
def get_operations():
    """Get all available operations"""
    try:
        operations = Operation.query.all()
        return jsonify([{
            'id': op.operation_id,
            'name': op.operation_name,
            'description': op.description
        } for op in operations])
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
                'message': 'Material not found'
            }), 404
            
        operation = Operation.query.get(data['operation_id'])
        if not operation:
            return jsonify({
                'status': 'error',
                'message': 'Operation not found'
            }), 404
        
        # Get machining parameters
        params = MachiningParameter.query.filter_by(
            material_id=data['material_id'],
            operation_id=data['operation_id']
        ).first()
        
        if not params:
            return jsonify({
                'status': 'error',
                'message': 'No parameters found for the given material and operation'
            }), 404
        
        # Initialize the appropriate operation class based on operation_name
        operation_name = data['operation_name'].lower()
        
        if operation_name == 'facing':
            from models.facing import FacingOperation
            # Pass database connection and material ID to get default parameters
            operation = FacingOperation(db.engine.raw_connection(), material.material_id, data['dimensions'])
            result = operation.calculate()
        else:
            # For other operations, use the calculator
            calculator = MachiningCalculator(
                db_params=params,
                material_rating=material.machinability_rating,
                material_id=material.material_id
            )
            result = calculator.calculate_machining_parameters(
                operation_name=operation_name,
                user_inputs=data['dimensions']
            )
        
        if 'error' in result:
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 400
        
        # Add metadata to result
        result.update({
            'material': material.material_name,
            'operation': result.get('operation', operation_name),  # Use operation from result or input
            'timestamp': datetime.utcnow().isoformat(),
            'machine_hour_rate': calculator.MACHINE_HOUR_RATE if 'calculator' in locals() else 0
        })
        
        # Return the time in the format expected by the frontend
        time_value = result.get('total_time_minutes', 0)
        logger.info(f"Calculation result: {result}")
        return jsonify({
            'status': 'success',
            'time': time_value,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error in calculation: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during calculation',
            'details': str(e)
        }), 500

# Frontend Routes
@app.route('/')
def index():
    return render_template('project.html')

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
