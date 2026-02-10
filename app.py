import flet as ft
import os
import sys
import threading
import time
from convert import convert_mesh_to_step

class ThreeDTRFApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "3DTRF | 3D Transformer"
        self.page.window.width = 800
        self.page.window.height = 650
        self.page.bgcolor = "#0F172A"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.resizable = False
        self.page.fonts = {
            "Outfit": "https://github.com/google/fonts/raw/main/ofl/outfit/Outfit-VariableFont_wght.ttf"
        }
        self.page.theme = ft.Theme(font_family="Outfit")
        
        self.selected_file_path = None
        
        self.init_ui()

    def init_ui(self):
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.AUTO_AWESOME, color="#38BDF8", size=30),
                ft.Text("3DTRF", size=32, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                ft.Text("v1.0", size=14, color="#64748B", weight=ft.FontWeight.W_300),
            ], alignment=ft.MainAxisAlignment.CENTER),
            margin=ft.margin.only(top=20, bottom=20)
        )

        # File Picker
        self.file_picker = ft.FilePicker(on_result=self.on_file_result)
        self.page.overlay.append(self.file_picker)

        # Drop Zone / Main Card
        self.main_card = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.UPLOAD_FILE, size=80, color="#64748B"),
                ft.Text("Drag & Drop your STL/OBJ file here", size=18, color="#94A3B8"),
                ft.Text("or", size=14, color="#475569"),
                ft.ElevatedButton(
                    "Select Files", 
                    icon=ft.Icons.SEARCH,
                    on_click=lambda _: self.file_picker.pick_files(
                        allow_multiple=False,
                        allowed_extensions=["stl", "obj"]
                    ),
                    style=ft.ButtonStyle(
                        color="#F8FAFC",
                        bgcolor="#38BDF8",
                        padding=20
                    )
                )
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=650,
            height=300,
            bgcolor=ft.Colors.with_opacity(0.05, "#FFFFFF"),
            border=ft.border.all(1, "#334155"),
            border_radius=20,
            padding=20,
            alignment=ft.alignment.center,
        )

        self.status_text = ft.Text("", size=16, color="#38BDF8")
        self.progress_bar = ft.ProgressBar(width=600, color="#38BDF8", bgcolor="#1E293B", visible=False)

        self.convert_btn = ft.ElevatedButton(
            "START CONVERSION",
            icon=ft.Icons.PLAY_ARROW,
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

        # Tutorial/Help
        help_card = ft.Container(
            content=ft.Column([
                ft.Text("How to use in Fusion 360:", weight=ft.FontWeight.BOLD),
                ft.Text("1. Open Fusion 360", size=12),
                ft.Text("2. Insert -> Insert Derived or File -> Open", size=12),
                ft.Text("3. Choose the generated .STEP file", size=12),
                ft.Text("4. You can now perform Solid Boolean operations!", size=12),
            ], spacing=5),
            padding=20,
            bgcolor=ft.Colors.with_opacity(0.02, "#FFFFFF"),
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
                    self.convert_btn
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=30),
                help_card
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

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
        
        # Run in thread to not block UI
        threading.Thread(target=self.run_conversion_logic, daemon=True).start()

    def run_conversion_logic(self):
        try:
            output_path = os.path.splitext(self.selected_file_path)[0] + ".step"
            convert_mesh_to_step(self.selected_file_path, output_path)
            
            self.status_text.value = "Conversion Complete! Output saved."
            self.status_text.color = "#4ADE80"
            self.progress_bar.visible = False
            
            # Show success snacker
            self.page.snack_bar = ft.SnackBar(ft.Text(f"File saved: {os.path.basename(output_path)}"))
            self.page.snack_bar.open = True
            
        except Exception as ex:
            self.status_text.value = f"Error: {str(ex)}"
            self.status_text.color = "#F87171"
            self.progress_bar.visible = False
        
        self.convert_btn.disabled = False
        self.page.update()

def main(page: ft.Page):
    ThreeDTRFApp(page)

if __name__ == "__main__":
    ft.app(target=main)
