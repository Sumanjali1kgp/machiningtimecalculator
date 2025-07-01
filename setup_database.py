import os
import sqlite3




def create_database():
    # Create database file
    conn = sqlite3.connect('instance/machining.db')
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.executescript('''
        DROP TABLE IF EXISTS MachiningParameters;
        DROP TABLE IF EXISTS Operations;
        DROP TABLE IF EXISTS Materials;
        DROP TABLE IF EXISTS operation_extra_times;
        DROP TABLE IF EXISTS setup_time_table;
        DROP TABLE IF EXISTS material_costs;
        DROP TABLE IF EXISTS cost_rates;    
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

        CREATE TABLE MachiningParameters (
            param_id INTEGER PRIMARY KEY AUTOINCREMENT,
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

     
        
        CREATE TABLE material_costs (
            material_id INTEGER PRIMARY KEY,
            rate_per_kg REAL NOT NULL DEFAULT 0.0,
            density_kg_mm3 REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (material_id) REFERENCES Materials(material_id) ON DELETE CASCADE
        );
        CREATE TABLE cost_rates (
            id INTEGER PRIMARY KEY,
            labor_rate_per_hr REAL NOT NULL DEFAULT 0.0,
            overhead_factor REAL NOT NULL DEFAULT 1.4
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
        ('Grooving', 'Operation to create grooves on the workpiece'),
        ('Idle', 'Non-machining operation such as tool movement or setup')
    ]
    
    cursor.executemany('INSERT INTO Operations (operation_name, description) VALUES (?, ?)', operations)
    
    # Insert materials with specified IDs and order
    materials = [
        (1, 'Aluminum', 0.9, 'HSS', 'Soft material, high machinability'),
        (2, 'Brass', 0.8, 'HSS', 'Excellent machinability, self-lubricating'),
        (3, 'Copper', 0.6, 'HSS', 'Good machinability, good thermal conductivity'),
        (4, 'Stainless Steel', 0.5, 'Solid Carbide', 'Difficult to machine, requires carbide tools'),
        (5, 'Mild Steel', 0.7, 'HSS', 'Good machinability, suitable for general machining')
    ]
    
    cursor.executemany('''
        INSERT INTO Materials (material_id, material_name, machinability_rating, recommended_tool, notes) 
        VALUES (?, ?, ?, ?, ?)
    ''', materials)
    
    # Insert machining parameters - All set for Aluminum (material_id: 1)
    parameters = [
        # Facing
        (1, 1, 170, 200, 0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 1, 170, 285, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Turning
        (1, 2, 170, 200,0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 2, 200, 285, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Drilling
        (1, 3, 100, 100,0.16, 0.18, 1, 2,'Rough cut'),
        (1, 3, 100, 100,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Boring
        (1, 4, 170, 200, 0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 4, 170, 200,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Reaming
        (1, 5, 170, 200, 0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 5, 170, 200,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Grooving
        (1, 6, 170, 200,0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 6, 170, 200,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Threading
        (1, 7,60,60,0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 7, 60,60, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Knurling
        (1, 8, 170, 200, 0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 8, 170, 200, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Parting
        (1, 9, 170, 200,0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 9, 170, 200,0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Insert machining parameters - All set for Brass (material_id: 2)
        # Facing
        ( 2, 1, 170, 480,0.16, 0.18, 1, 2, 'Rough cut'),
        ( 2, 1, 170, 480,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Turning
        (2, 2, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 2, 170, 480,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Drilling
        (2, 3, 100, 100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 3, 100, 100,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Boring
         ( 2, 4, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 4, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Reaming
        (2, 5, 100,100,0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 5, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Grooving
        (2, 6, 100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 6,100,100 ,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Threading
        (2, 7, 60 , 60 ,0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 7, 60 , 60 , 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Knurling
        (2, 8, 100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 8, 100,100,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Parting
        (2, 9,  100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 9, 100,100 ,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Insert machining parameters - All set for copper (material_id: 3)
        # Facing
         (3, 1, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 1, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Turning
        (3, 2, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 2, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Drilling
         (3, 3, 100,100 , 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 3, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Boring
         (3, 4, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 4, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Reaming
        (3, 5, 100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 5, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Grooving
        (3, 6,  100,100,0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 6, 100,100,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Threading
        (3, 7, 60 , 60 ,0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 7, 60 , 60 , 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Knurling
        (3, 8,  100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 8,  100,100,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Parting
        (3, 9,  100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 9, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
         # Insert machining parameters - All set for stainless steel (material_id: 4)
        # Facing
        (4, 1, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 1, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Turning 
        (4, 2, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 2, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Drilling
         (4, 3, 100,100 ,0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 3, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Boring
         (4, 4, 170, 480,0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 4, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Reaming
        (4, 5, 100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 5, 100,100, 0.14, 0.12, 0.05, 0.1,'Finish cut'),
        
        # Grooving
        (4, 6,  100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 6, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Threading
        (4, 7, 60 , 60 ,0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 7, 60 , 60 , 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Knurling
        (4, 8,  100,100,0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 8,  100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Parting
        (4, 9,  100,100,0.16, 0.18, 1, 2, 'Rough cut'),
        (4, 9, 100,100,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        
         # Insert machining parameters - All set for mild steel (material_id: 5)
        # Facing
        (5, 1, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 1, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Turning
        (5, 2, 170, 480,0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 2, 170, 480,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Drilling
         (5, 3, 100,100 ,0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 3, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Boring
         (5, 4, 170, 480,0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 4, 170, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Reaming
        (5, 5, 100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 5, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Grooving
        (5, 6,  100,100,0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 6, 100,100,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Threading
        (5, 7, 60 , 60 , 0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 7, 60 , 60 ,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Knurling
        (5, 8,  100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 8,  100,100,0.14, 0.12, 0.05, 0.1, 'Finish cut'),
        
        # Parting
        (5, 9,  100,100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 9, 100,100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),
         
      
    ]

    
    cursor.executemany('''
        INSERT INTO MachiningParameters 
        (material_id, operation_id, spindle_speed_min, spindle_speed_max, 
         feed_rate_min, feed_rate_max, depth_of_cut_min, depth_of_cut_max, notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', parameters)

    
    cursor.execute('''
        INSERT INTO cost_rates (id, labor_rate_per_hr, overhead_factor) 
        VALUES (1, 500.0, 1.4)
    ''')

    # Create indexes
    cursor.executescript('''
        CREATE INDEX idx_machining_params ON MachiningParameters(material_id, operation_id, notes);
        CREATE INDEX idx_materials_name ON Materials(material_name);
        CREATE INDEX idx_operations_name ON Operations(operation_name);
    ''')
    
    conn.commit()
    conn.close()
    print("Database setup completed successfully!")

if __name__ == '__main__':
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    create_database()
