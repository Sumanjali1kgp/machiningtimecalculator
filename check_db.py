from app import app, db, Material, Operation

def check_database():
    with app.app_context():
        # Check materials
        materials = Material.query.all()
        print("\nMaterials in database:")
        for mat in materials:
            print(f"ID: {mat.material_id}, Name: {mat.material_name}")
        
        # Check operations
        operations = Operation.query.all()
        print("\nOperations in database:")
        for op in operations:
            print(f"ID: {op.operation_id}, Name: {op.operation_name}")

if __name__ == '__main__':
    check_database()
