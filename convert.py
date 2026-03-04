import os
import sys
import time

# Fix encoding issues on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except Exception:
        pass

def setup_environment():
    """
    Checks and installs necessary libraries.
    """
    print("Initializing 3DTRF Environment...")
    try:
        import trimesh
        import aspose.cad as cad
        import networkx
        import scipy
    except ImportError:
        print("Installing dependencies (trimesh, aspose-cad, networkx, scipy, pyrender, pillow, numpy, pyvista)...")
        os.system(f"{sys.executable} -m pip install trimesh aspose-cad networkx scipy pyrender pillow numpy pyvista")
        print("Dependencies installed successfully.")

def convert_mesh_to_step(input_path, output_path, status_callback=None):
    """
    Converts STL/OBJ to STEP if possible, else falls back to OBJ for Fusion 360.
    """
    import trimesh
    
    def log(msg, progress=None):
        if progress is not None:
             print(f"PROGRESS:{progress}", flush=True)
        print(msg, flush=True)
        if status_callback:
            status_callback(msg)

    log(f"[{time.strftime('%H:%M:%S')}] Loading mesh: {input_path}", 0.1)
    # Load the mesh
    mesh = trimesh.load(input_path)
    
    # Check if loaded as Scene, convert to single mesh if so
    if isinstance(mesh, trimesh.Scene):
        log(f"[{time.strftime('%H:%M:%S')}] Input is a Scene, dumping to single mesh...")
        mesh = getattr(mesh, 'dump', lambda: mesh.dump(concatenate=True))()
        if isinstance(mesh, list):
            # If dump returns a list of geometries, concatenate them
            mesh = trimesh.util.concatenate(mesh)

    log(f"[{time.strftime('%H:%M:%S')}] Mesh loaded. Faces: {len(mesh.faces)}")
    face_count = len(mesh.faces)
    if face_count > 40000:
        log(f"Mesh is too complex ({face_count} facets). Optimizing...", 0.3)
        try:
            # Use quadric decimation if available (common in newer trimesh)
            if hasattr(mesh, 'simplify_quadric_decimation'):
                mesh = mesh.simplify_quadric_decimation(40000)
            else:
                 # Fallback or older method name?
                 # Try 'simplify_quadratic_decimation' just in case, or skip
                 if hasattr(mesh, 'simplify_quadratic_decimation'):
                     mesh = mesh.simplify_quadratic_decimation(40000)
                 else:
                     log("Warning: No simplification method found. Skipping optimization.")
        except Exception as e:
            log(f"Optimization failed: {e}. Proceeding with original mesh.")
            
        log(f"Optimized to {len(mesh.faces)} facets.")

    log(f"[{time.strftime('%H:%M:%S')}] Repairing mesh...", 0.5)
    
    # Remove unreferenced vertices
    mesh.remove_unreferenced_vertices()
    
    # Optional: Keep only the largest connected component to remove "extra" floating meshes
    components = mesh.split(only_watertight=False)
    if len(components) > 1:
        log(f"[{time.strftime('%H:%M:%S')}] Found {len(components)} separate parts. Keeping the largest one to remove extra meshes...")
        # Sort components by number of faces and keep the largest
        components = sorted(components, key=lambda c: len(c.faces), reverse=True)
        mesh = components[0]
        log(f"[{time.strftime('%H:%M:%S')}] Kept largest part with {len(mesh.faces)} faces.")

    # Repair mesh
    # mesh.process() creates a new mesh, so we need to assign it back if it returns one, 
    # but trimesh.load() returns a Scene or Trimesh. 
    # If it is a Trimesh, process() is in-place? No, process() returns a new mesh usually or modifies?
    # Actually, trimesh.Trimesh.process() is not a method. 
    # Using specific repair functions from trimesh.repair
    trimesh.repair.fill_holes(mesh)
    log(f"[{time.strftime('%H:%M:%S')}] Holes filled.")
    trimesh.repair.fix_inversion(mesh)
    log(f"[{time.strftime('%H:%M:%S')}] Normals fixed.")
    trimesh.repair.fix_winding(mesh)
    log(f"[{time.strftime('%H:%M:%S')}] Winding fixed.")
    
    # Optional: Coplanar Decimation using PyVista/VTK
    try:
        import pyvista as pv
        import numpy as np
        log(f"[{time.strftime('%H:%M:%S')}] Applying coplanar decimation via PyVista...")
        # Convert trimesh to pyvista PolyData
        faces_pv = np.hstack([[3] + list(f) for f in mesh.faces])
        pv_mesh = pv.PolyData(mesh.vertices, faces_pv)
        
        # Optimize by decimating nearly flat regions
        # feature_angle=15 preserves sharp corners, while decimate removes coplanar triangles inside flat areas
        # Try decimate_pro for topology preservation
        optimized_pv = pv_mesh.decimate_pro(0.9, preserve_topology=True, feature_angle=15.0)
        
        # Update trimesh data
        faces = optimized_pv.faces.reshape(-1, 4)[:, 1:4]
        mesh = trimesh.Trimesh(vertices=optimized_pv.points, faces=faces)
        log(f"[{time.strftime('%H:%M:%S')}] Coplanar decimation complete! Faces reduced to {len(mesh.faces)}.")
    except Exception as e:
        log(f"[{time.strftime('%H:%M:%S')}] Coplanar decimation skipped (PyVista/VTK not ready): {e}")

    # Save cleaned mesh to a temporary file for Aspose.CAD to pick up
    temp_stl = "temp_optimized.stl"
    mesh.export(temp_stl)
    
    # Generate an interactive 3D viewer script
    try:
        log(f"[{time.strftime('%H:%M:%S')}] Creating interactive 3D viewer script...")
        base, ext = os.path.splitext(output_path)
        viewer_script_path = base + "_viewer.py"
        target_model_path = base + ".stl"  # We will default to opening the STL format
        
        # Create a small script the app will launch
        script_code = f"""import pyvista as pv
import sys

# Load model
mesh_path = r"{target_model_path}"
print(f"Loading {{mesh_path}}...")
mesh = pv.read(mesh_path)

# Show interactive window
plotter = pv.Plotter(title="3DTRF Interactive Mesh Preview")
plotter.background_color = "#0F172A"

# Draw the mesh surface WITHOUT the internal triangle edges
plotter.add_mesh(
    mesh, 
    color="#87CEEB", 
    show_edges=False, 
    opacity=0.9
)

# Extract and draw ONLY the sharp feature edges (hides coplanar triangle diagonals)
edges = mesh.extract_feature_edges(feature_angle=5.0)
plotter.add_mesh(
    edges,
    color="#333333",
    line_width=3.0
)

plotter.add_axes()
plotter.show()
"""
        with open(viewer_script_path, "w", encoding="utf-8") as f:
            f.write(script_code)
            
        log(f"[{time.strftime('%H:%M:%S')}] Viewer script created: {viewer_script_path}")
        if status_callback:
            status_callback(f"Viewer Generated: {viewer_script_path}")
            
    except Exception as e:
        log(f"Warning: Could not generate viewer script: {e}")

    con_success = False
    try:
        # Try Aspose.CAD
        import aspose.cad as cad
        from aspose.cad.imageoptions import StpOptions
        print("Converting to STEP format using Aspose.CAD...", flush=True)
        print("PROGRESS:0.7", flush=True)
        image = None
        try:
            image = cad.Image.load(temp_stl)
            options = StpOptions()
            image.save(output_path, options)
            print(f"Success! Saved to: {output_path}")
            con_success = True
        finally:
            if image:
                try:
                    if hasattr(image, 'dispose'):
                        image.dispose()
                    elif hasattr(image, 'close'):
                        image.close()
                except:
                    pass
                del image
    except ImportError:
        print("Aspose.CAD not found. Trying stl2step...")
        try:
            # Try stl2step (if installed)
            # hypothetical usage based on typical libs, 
            # but since we know it failed to install, this block is just future-proofing
            import stl2step
            # stl2step typically might have a run function
            # stl2step.convert(temp_stl, output_path)
            # print(f"Success! Saved to: {output_path}")
            # con_success = True
            raise ImportError("stl2step not installed (mock)") 
        except Exception as e:
            print(f"STEP conversion unavailable ({e}). Falling back to OBJ.")
    
    finally:
        # Force garbage collection to release file locks
        if 'image' in locals():
            del image
        import gc
        gc.collect()
        
        if os.path.exists(temp_stl):
            # Retry loop for deletion
            for i in range(5):
                try:
                    os.remove(temp_stl)
                    break
                except PermissionError:
                    time.sleep(1.0)
            else:
                print(f"Warning: Could not remove temporary file {temp_stl} (locked).")

    if not con_success:
        # Fallback to OBJ and STL
        base,ext = os.path.splitext(output_path)
        
        output_obj = base + ".obj"
        log(f"Exporting to OBJ: {output_obj}")
        mesh.export(output_obj)
        
        output_stl = base + ".stl"
        log(f"Exporting to STL: {output_stl}")
        mesh.export(output_stl)
        
        return output_stl # Return STL as primary for now, or just handle in UI
    
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert.py <input_file>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = os.path.splitext(input_file)[0] + ".step"
    
    setup_environment()
    real_output = convert_mesh_to_step(input_file, output_file)
    print(f"Final output: {real_output}")

