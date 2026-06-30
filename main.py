import customtkinter as ctk
import ui_roles
import ui_plan
import ui_generate
import ui_export

# --- Standard App Setup ---
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 

app = ctk.CTk()
app.title("Clinic Timetable Planner")
app.geometry("800x600") 

title_label = ctk.CTkLabel(app, text="Clinic Timetable Assistant", font=("Arial", 28, "bold"))
title_label.pack(pady=30) 

button_frame = ctk.CTkFrame(app)
button_frame.pack(pady=10, padx=50, fill="both", expand=True)

# --- The 4 Main Menu Buttons ---
btn_roles = ctk.CTkButton(button_frame, text="1. Edit Roles & Staff", width=250, height=50, command=lambda: ui_roles.open_roles_window(app))
btn_roles.pack(pady=15)

btn_plan = ctk.CTkButton(button_frame, text="2. Edit Monthly Plan", width=250, height=50, command=lambda: ui_plan.open_plan_window(app))
btn_plan.pack(pady=15)

btn_generate = ctk.CTkButton(button_frame, text="3. Generate Schedule", width=250, height=50, fg_color="#28a745", hover_color="#218838", command=lambda: ui_generate.open_generate_window(app))
btn_generate.pack(pady=15)

btn_export = ctk.CTkButton(button_frame, text="4. Finalize Timetable", width=250, height=50, command=lambda: ui_export.open_export_window(app))
btn_export.pack(pady=15)

app.mainloop()