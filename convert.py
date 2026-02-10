import os
import sys

def setup_environment():
    """
    Checks and installs necessary libraries.
    """
    print("Initializing 3DTRF Environment...")
    try:
        import trimesh
        import aspose.cad as cad
    except ImportError:
        print("Installing dependencies (trimesh, aspose-cad)...")
        os.system(f"{sys.executable} -m pip install trimesh aspose-cad")
        print("Dependencies installed successfully.")

def convert_mesh_to_step(input_path, output_path):
    """
    Converts STL/OBJ to STEP while optimizing for Fusion 360.
    """
    import trimesh
    try:
        import aspose.cad as cad
        from aspose.cad.imageoptions import StpOptions
    except ImportError:
        print("Error: aspose-cad is required for STEP export.")
        raise ImportError("aspose-cad not found")

    print(f"Loading mesh: {input_path}")
    mesh = trimesh.load(input_path)

    # Fusion 360 B-Rep limit is around 50k facets. 
    # We target 20k-40k for stability.
    face_count = len(mesh.faces)
    if face_count > 40000:
        print(f"Mesh is too complex ({face_count} facets). Optimizing...")
        mesh = mesh.simplify_quadratic_decimation(40000)
        print(f"Optimized to {len(mesh.faces)} facets.")

    # Repair mesh
    mesh.fill_holes()
    mesh.remove_duplicate_faces()
    mesh.remove_infinite_values()
    
    # Save cleaned mesh to a temporary file for Aspose.CAD to pick up
    temp_stl = "temp_optimized.stl"
    mesh.export(temp_stl)

    try:
        # Aspose.CAD handles the heavy lifting of Mesh to B-Rep conversion during export
        print("Converting to STEP format...")
        image = cad.Image.load(temp_stl)
        options = StpOptions()
        image.save(output_path, options)
        print(f"Success! Saved to: {output_path}")
    finally:
        if os.path.exists(temp_stl):
            os.remove(temp_stl)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert.py <input_file>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = os.path.splitext(input_file)[0] + ".step"
    
    setup_environment()
    convert_mesh_to_step(input_file, output_file)
