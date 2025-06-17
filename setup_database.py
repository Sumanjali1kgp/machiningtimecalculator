import os
import sqlite3
import shutil

def create_database():
    # Create database file
    conn = sqlite3.connect('instance/machining.db')
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.executescript('''
        DROP TABLE IF EXISTS MachiningParameters;
        DROP TABLE IF EXISTS MaterialProperties;
        DROP TABLE IF EXISTS Operations;
        DROP TABLE IF EXISTS Materials;
    ''')
    
    # Create tables
    cursor.executescript('''
        CREATE TABLE Materials (
            material_id INTEGER PRIMARY KEY,
            material_name VARCHAR(100) NOT NULL,
            machinability_rating FLOAT,
            recommended_tool VARCHAR(50),
            notes TEXT
        );

        CREATE TABLE Operations (
            operation_id INTEGER PRIMARY KEY,
            operation_name VARCHAR(100) NOT NULL,
            description TEXT
        );

        CREATE TABLE MaterialProperties (
            material_id INTEGER PRIMARY KEY,
            hardness VARCHAR(50),
            thermal_conductivity VARCHAR(50),
            specific_gravity VARCHAR(50),
            common_applications TEXT,
            FOREIGN KEY (material_id) REFERENCES Materials(material_id)
        );

        CREATE TABLE MachiningParameters (
            param_id INTEGER PRIMARY KEY,
            material_id INTEGER,
            operation_id INTEGER,
            spindle_speed_min INTEGER,
            spindle_speed_max INTEGER,
            feed_rate_min FLOAT,
            feed_rate_max FLOAT,
            depth_of_cut_min FLOAT,
            depth_of_cut_max FLOAT,
            notes TEXT,
            FOREIGN KEY (material_id) REFERENCES Materials(material_id),
            FOREIGN KEY (operation_id) REFERENCES Operations(operation_id)
        );
    ''')
    
    # Insert operations
    operations = [
        ('Facing', 'Operation to create a flat surface on the workpiece'),
        ('Turning', 'Operation to reduce the diameter of the workpiece'),
        ('Drilling', 'Operation to create holes in the workpiece'),
        ('Boring', 'Operation to enlarge existing holes'),
        ('Reaming', 'Operation to finish existing holes'),
        ('Threading', 'Operation to create threads on the workpiece'),
        ('Knurling', 'Operation to create patterns on the workpiece surface'),
        ('Parting', 'Operation to cut the workpiece into pieces'),
        ('Grooving', 'Operation to create grooves on the workpiece')
    ]
    
    cursor.executemany('INSERT INTO Operations (operation_name, description) VALUES (?, ?)', operations)
    
    # Insert materials
    materials = [
        ('Aluminum', 0.85, 'HSS', 'Soft material, high machinability'),
        ('Brass', 0.9, 'HSS', 'Excellent machinability, self-lubricating'),
        ('Copper', 0.75, 'HSS', 'Good machinability, good thermal conductivity'),
        ('Stainless Steel', 0.45, 'Solid Carbide', 'Difficult to machine, requires carbide tools'),
        ('Mild Steel', 0.7, 'HSS', 'Good machinability, suitable for general machining')
    ]
    
    cursor.executemany('''
        INSERT INTO Materials (material_name, machinability_rating, recommended_tool, notes) 
        VALUES (?, ?, ?, ?)
    ''', materials)
    
    # Insert material properties
    properties = [
        (1, 'Soft to Medium', 'Low', '7.85', 'General engineering, structural components'),
        (2, 'Hard', 'Low', '8.0', 'Corrosion resistant applications'),
        (3, 'Soft', 'High', '2.7', 'Aircraft parts, heat exchangers'),
        (4, 'Soft', 'High', '8.96', 'Electrical components, heat sinks'),
        (5, 'Soft', 'High', '8.5', 'Decorative parts, plumbing fixtures')
    ]
    
    cursor.executemany('''
        INSERT INTO MaterialProperties 
        (material_id, hardness, thermal_conductivity, specific_gravity, common_applications) 
        VALUES (?, ?, ?, ?, ?)
    ''', properties)
    
    # Insert machining parameters
    parameters = [
        # Facing
        (1, 3, 1, 170, 200, 0.1, 0.3, 0.5, 2.0, 'Rough cut'),
        (2, 3, 1, 170, 200, 0.05, 0.15, 0.1, 0.5, 'Finish cut'),
        
        # Turning
        (3, 3, 2, 170, 200, 0.15, 0.4, 0.5, 2.5, 'Rough cut'),
        (4, 3, 2, 170, 200, 0.05, 0.2, 0.1, 0.5, 'Finish cut'),
        
        # Drilling
        (5, 3, 3, 170, 200, 0.1, 0.3, 0.5, 2.0, 'Rough cut'),
        (6, 3, 3, 170, 200, 0.05, 0.15, 0.1, 0.5, 'Finish cut'),
        
        # Boring and Grooving
        (7, 3, 4, 100, 120, 0.1, 0.3, 0.5, 2.0, 'Rough cut'),
        (8, 3, 4, 100, 120, 0.05, 0.15, 0.1, 0.5, 'Finish cut'),
        (9, 3, 9, 100, 120, 0.1, 0.3, 0.5, 2.0, 'Rough cut'),
        (10, 3, 9, 100, 120, 0.05, 0.15, 0.1, 0.5, 'Finish cut'),
        
        # Knurling
        (11, 3, 7, 285, 300, 0.1, 0.3, 0.5, 2.0, 'Knurling operation'),
        
        # Threading
        (12, 3, 6, 600, 700, 0.1, 0.3, 0.5, 2.0, 'Threading operation'),
        
        # Parting
        (13, 3, 8, 150, 200, 0.05, 0.15, 0.5, 2.0, 'Parting operation'),
        
        # Reaming
        (14, 3, 5, 150, 200, 0.05, 0.15, 0.1, 0.5, 'Reaming operation'),
        
        # Brass Parameters
        (15, 5, 1, 250, 300, 0.1, 0.3, 0.5, 2.0, 'Rough cut'),
        (16, 5, 1, 250, 300, 0.05, 0.15, 0.1, 0.5, 'Finish cut'),
        (17, 5, 2, 250, 300, 0.15, 0.4, 0.5, 2.5, 'Rough cut'),
        (18, 5, 2, 250, 300, 0.05, 0.2, 0.1, 0.5, 'Finish cut')
    ]
    
    cursor.executemany('''
        INSERT INTO MachiningParameters 
        (param_id, material_id, operation_id, spindle_speed_min, spindle_speed_max, 
         feed_rate_min, feed_rate_max, depth_of_cut_min, depth_of_cut_max, notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', parameters)
    
    # Create indexes
    cursor.executescript('''
        CREATE INDEX idx_machining_params ON MachiningParameters(material_id, operation_id, notes);
        CREATE INDEX idx_materials_name ON Materials(material_name);
        CREATE INDEX idx_operations_name ON Operations(operation_name);
        CREATE INDEX idx_material_properties ON MaterialProperties(hardness, thermal_conductivity, specific_gravity);
    ''')
    
    conn.commit()
    conn.close()
    print("Database setup completed successfully!")

if __name__ == '__main__':
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    create_database()
