import trimesh
import numpy as np

try:
    mesh = trimesh.creation.box()
    print("Mesh type:", type(mesh))
    print("Available methods starting with 'simplify':")
    for method in dir(mesh):
        if 'simplify' in method:
            print(f" - {method}")
            
    if hasattr(mesh, 'simplify_quadratic_decimation'):
        print("simplify_quadratic_decimation is available")
    else:
        print("simplify_quadratic_decimation is MISSING")
        
except Exception as e:
    print(f"Error: {e}")
