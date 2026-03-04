import flet as ft
import os
import sys
import threading
import time
import io

# Fix encoding issues on Windows (CP950/UTF-8)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except Exception:
        pass

from convert import convert_mesh_to_step
import tkinter as tk
from tkinter import filedialog


class ThreeDTRFApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "3DTRF | 3D Transformer"
        self.page.window.width = 1000
        self.page.window.height = 850
        self.page.bgcolor = "#0F172A"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.resizable = True
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.fonts = {
            "Outfit": "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit-VariableFont_wght.ttf"
        }
        self.page.theme = ft.Theme(font_family="Outfit")
        
        self.selected_file_path = None
        
        self.init_ui()

    def init_ui(self):
        # Check for portable Python (STEP support)
        portable_python = os.path.join(os.getcwd(), "deps", "python310", "python.exe")
        step_ready = os.path.exists(portable_python)
        step_status_text = "Step Engine: READY" if step_ready else "Step Engine: NOT FOUND"
        step_status_color = "#4ADE80" if step_ready else "#F87171"
        # Header
        header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_AWESOME, color="#38BDF8", size=30),
                    ft.Text("3DTRF", size=32, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.Container(
                        content=ft.Text(step_status_text, size=10, color="#1E293B", weight=ft.FontWeight.BOLD),
                        bgcolor=step_status_color,
                        padding=5,
                        border_radius=5,
                        margin=ft.Margin.only(left=10)
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("v1.1 | Auto-Optimized for Fusion 360", size=12, color="#64748B", weight=ft.FontWeight.W_300)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=ft.Margin.only(top=20, bottom=20)
        )

        # File Picker (Disabled due to Flet 0.80.5/Py3.14 issue)
        # self.file_picker = ft.FilePicker()
        # self.file_picker.on_result = self.on_file_result
        # self.page.overlay.append(self.file_picker)

        # Enable Drag & Drop
        self.page.on_file_drop = self.on_file_drop

        self.manual_input = ft.TextField(
            label="Paste File Path", 
            text_size=12, 
            height=40, 
            expand=True, 
            border_color="#334155",
            color="#F8FAFC",
            on_submit=self.on_manual_path
        )


        # Drop Zone / Main Card
        self.main_card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.UPLOAD_FILE, size=80, color="#64748B"),
                ft.Text("Drag & Drop your STL/OBJ file here", size=18, color="#94A3B8"),
                ft.Text("or", size=14, color="#475569"),
                ft.ElevatedButton(
                    "Select Files", 
                    icon=ft.Icons.SEARCH,
                    on_click=self.open_file_dialog, 
                    disabled=False,
                    style=ft.ButtonStyle(
                        color="#F8FAFC",
                        bgcolor="#38BDF8",
                        padding=20
                    )
                ),
                ft.Container(height=10),
                ft.Text("--- OR ---", size=12, color="#475569"),
                ft.Container(height=10),
                ft.Row([
                    self.manual_input,
                    ft.IconButton(
                        icon=ft.Icons.CHECK_CIRCLE, 
                        icon_color="#38BDF8", 
                        on_click=self.on_manual_path
                    )
                ], width=500, alignment=ft.MainAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=650,
            height=400,
            bgcolor="#0DFFFFFF",


            border=ft.Border.all(1, "#334155"),
            border_radius=20,
            padding=20,
            alignment=ft.Alignment(0, 0),
        )

        self.status_text = ft.Text("", size=16, color="#38BDF8")
        self.progress_bar = ft.ProgressBar(width=600, color="#38BDF8", bgcolor="#1E293B", visible=False)

        self.convert_btn = ft.ElevatedButton(
            "OPTIMIZE & REPAIR",
            icon=ft.Icons.BUILD,
            disabled=True,
            on_click=self.start_conversion,
            width=300,
            height=50,
            style=ft.ButtonStyle(
                color="#F8FAFC",
                bgcolor={
                    ft.ControlState.DEFAULT: "#38BDF8",
                    ft.ControlState.DISABLED: "#1E293B"
                }
            )
        )
        
        self.folder_btn = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN, 
            tooltip="Open Output Folder", 
            on_click=self.open_output_folder, 
            visible=False, 
            icon_color="#38BDF8"
        )

        # Tutorial/Help
        help_card = ft.Container(
            content=ft.Column([
                ft.Text("Why use this tool?", weight=ft.FontWeight.BOLD),
                ft.Text("1. Reduces high-poly meshes (<40k faces) for performance", size=12),
                ft.Text("2. Repairs geometry (holes/normals) for Boolean operations", size=12),
                ft.Text("3. Exports .STL (for Paint 3D/Slicers) and .OBJ (for CAD)", size=12),
                ft.Text("4. Fusion 360: Insert > Insert Mesh > Select the optimized .OBJ", size=12, color="#FACC15"),
                ft.Text("   (Then 'Mesh to Body' will work much faster!)", size=12, color="#FACC15"),
            ], spacing=5),
            padding=20,
            bgcolor="#05FFFFFF",


            border_radius=10,
            width=650
        )

        self.page.add(
            ft.Column([
                header,
                ft.Divider(height=1, color="#1E293B"),
                ft.Container(height=20),
                self.main_card,
                ft.Container(height=20),
                ft.Column([
                    self.status_text,
                    self.progress_bar,
                    ft.Row([
                        self.convert_btn,
                        self.folder_btn
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=30),
                help_card
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        self.page.update()


    def on_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_file_path = e.files[0].path
            filename = e.files[0].name
            self.status_text.value = f"Selected: {filename}"
            self.convert_btn.disabled = False
            self.main_card.content.controls[0].color = "#38BDF8"
            self.main_card.content.controls[1].value = filename
            self.main_card.content.controls[1].color = "#F8FAFC"
            self.page.update()

    def start_conversion(self, e):
        self.convert_btn.disabled = True
        self.progress_bar.visible = True
        self.status_text.value = "Processing mesh... please wait."
        self.page.update()
        
        # Run conversion in a separate thread to keep UI responsive
        threading.Thread(target=self.run_conversion_logic, daemon=True).start()
        
    def on_manual_path(self, e):
        print("DEBUG: Manual path check triggered")
        try:
            path = self.manual_input.value
            print(f"DEBUG: Input value: '{path}'")
            if not path:
                print("DEBUG: Path is empty")
                return
                
            exists_check = os.path.exists(path)
            print(f"DEBUG: os.path.exists('{path}') -> {exists_check}")
            if exists_check:
                if os.path.isfile(path):
                     print(f"DEBUG: File '{path}' found. Updating UI...")
                     filename = os.path.basename(path)
                     ext = os.path.splitext(filename)[1].lower()
                     if ext not in ['.stl', '.obj']:
                         print(f"DEBUG: Invalid extension: {ext}")
                         self.status_text.value = f"Error: Unsupported file type '{ext}' (Need .stl/.obj)"
                         self.status_text.color = "#F87171"
                         self.page.update()
                         return
                     
                     print("DEBUG: Valid extension. Setting UI values...")
                     self.selected_file_path = path
                     self.status_text.value = f"Selected: {filename}"
                     self.convert_btn.disabled = False
                     try:
                        self.main_card.content.controls[0].color = "#38BDF8"
                        self.main_card.content.controls[1].value = filename
                        self.main_card.content.controls[1].color = "#F8FAFC"
                        print("DEBUG: Main card controls updated locally.")
                     except Exception as ui_ex:
                        print(f"DEBUG: Error updating main card controls: {ui_ex}")

                     self.page.update()
                     print("DEBUG: page.update() called.")
                else:
                    self.status_text.value = "Error: Input is a directory, not a file."
                    self.status_text.color = "#F87171"
                    self.page.update()
            else:
                 self.status_text.value = "Error: File not found!"
                 self.status_text.color = "#F87171"
                 self.page.update()
        except Exception as e:
            print(f"ERROR in on_manual_path: {e}")
            self.status_text.value = f"Error: {e}"
            self.status_text.color = "#F87171"
            self.page.update()

    def open_file_dialog(self, e):
        # Use tkinter for file dialog as fallback
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            path = filedialog.askopenfilename(
                title="Select 3D Model",
                filetypes=[("3D Models", "*.stl *.obj"), ("All Files", "*.*")]
            )
            root.destroy()
            
            if path:
                self.manual_input.value = path
                self.on_manual_path(None) # Reuse validation logic
                self.page.update()
        except Exception as ex:
            print(f"Error opening file dialog: {ex}")

    def on_file_drop(self, e: ft.FileDropEvent):
        print("DEBUG: File dropped event fired!")
        print(f"DEBUG: Files: {e.files}")
        if e.files:
            # e.files is a list of FileDropEvent objects? No, it's usually a list of paths or objects
            # In Flet, e.files is a list of ft.FileDropEventFile
            file_path = e.files[0].path
            filename = e.files[0].name
            
            # Filter extension
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.stl', '.obj']:
                self.status_text.value = f"Error: Unsupported file type {ext}"
                self.status_text.color = "#F87171"
                self.page.update()
                return

            self.selected_file_path = file_path
            self.status_text.value = f"Selected: {filename}"
            self.convert_btn.disabled = False
            self.main_card.content.controls[0].color = "#38BDF8"
            self.main_card.content.controls[1].value = filename
            self.main_card.content.controls[1].color = "#F8FAFC"
            self.page.update()

    def run_conversion_logic(self):
        def update_status(msg):
             self.status_text.value = msg
             self.page.update()

        try:
            output_path = os.path.splitext(self.selected_file_path)[0] + "_optimized.step"
            
            # Check for portable Python with Aspose.CAD support
            portable_python = os.path.join(os.getcwd(), "deps", "python310", "python.exe")
            use_subprocess = os.path.exists(portable_python)
            
            if use_subprocess:
                update_status(f"Using portable Python env for BETTER conversion...")
                import subprocess
                
                # Run convert.py as a subprocess
                # We need to capture stdout to update status
                # Use -u for unbuffered output to get real-time updates
                cmd = [portable_python, "-u", "convert.py", self.selected_file_path]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8', # Force UTF-8 communication
                    errors='replace',  # Replace invalid bytes
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                real_path = ""
                
                # Read stdout line by line
                while True:
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        line = line.strip()
                        if line.startswith("Final output: "):
                            real_path = line.replace("Final output: ", "").strip()
                            self.progress_bar.value = 1.0
                            self.page.update()
                        elif line.startswith("PROGRESS:"):
                            try:
                                prog_val = float(line.split(":")[1])
                                self.progress_bar.value = prog_val
                                self.page.update()
                            except:
                                pass
                        else:
                            # Forward log messages to UI
                            update_status(line)
                            print(f"Subprocess: {line}")
                            
                rc = process.poll()
                if rc != 0:
                    err = process.stderr.read()
                    raise Exception(f"Conversion process failed: {err}")
                    
                if not real_path:
                    # Fallback if final output wasn't caught
                    real_path = output_path
                    
            else:
                # Fallback to internal method (limited functionality on Py3.14)
                update_status("Portable env not found. Using internal conversion (limited)...")
                # Pass our callback directly
                real_path = convert_mesh_to_step(self.selected_file_path, output_path, status_callback=update_status)
            
            ext = os.path.splitext(real_path)[1].upper()
            if ext == ".STEP":
                 self.status_text.value = f"Success! Converted to STEP."
            else:
                 self.status_text.value = f"Done! Saved as {ext} (Optimized)."
                 
            self.status_text.color = "#4ADE80"
            self.progress_bar.visible = False
            
            # Automatically launch the interactive viewer script if it exists
            viewer_script = os.path.splitext(self.selected_file_path)[0] + "_viewer.py"
            if os.path.exists(viewer_script):
                try:
                    import subprocess
                    portable_python = os.path.join(os.getcwd(), "deps", "python310", "python.exe")
                    if not os.path.exists(portable_python):
                        portable_python = "python" # fallback to system python
                        
                    subprocess.Popen(
                        [portable_python, viewer_script],
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                except Exception as e:
                    print(f"Warning: Could not launch viewer script {viewer_script}: {e}")
            
            self.folder_btn.visible = True
            
            # Show success snacker
            self.page.snack_bar = ft.SnackBar(ft.Text(f"File saved: {os.path.basename(real_path)}"))
            self.page.snack_bar.open = True

        except Exception as ex:
            self.status_text.value = f"Error: {str(ex)}"
            self.status_text.color = "#F87171"
            self.progress_bar.visible = False
        
        self.convert_btn.disabled = False
        self.page.update()

    def open_output_folder(self, e):
        if self.selected_file_path:
            folder = os.path.dirname(self.selected_file_path)
            try:
                os.startfile(folder)
            except Exception as ex:
                print(f"Error opening folder: {ex}")

    def close_preview_dialog(self, dlg):
        self.page.close(dlg)

def main(page: ft.Page):
    ThreeDTRFApp(page)

if __name__ == "__main__":
    ft.app(target=main)
