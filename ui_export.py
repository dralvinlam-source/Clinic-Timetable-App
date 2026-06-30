import customtkinter as ctk
from tkinter import filedialog, messagebox
import database
import pandas as pd
import calendar
from datetime import date

def open_export_window(app):
    active_m = database.memory.get("ACTIVE_MONTH", "January")
    active_y = database.memory.get("ACTIVE_YEAR", "2026")
    month_key = f"{active_m}_{active_y}"

    master_schedule = database.memory.get("SAVED_SCHEDULE", {}).get(month_key)
    if not master_schedule:
        messagebox.showerror("Export Error", "No saved schedule found for this month. Please generate and save first.")
        return

    task_table = database.memory.get("TASK_TABLE", [])
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        initialfile=f"Timetable_{active_m}_{active_y}.xlsx",
        title="Save Timetable Excel",
        filetypes=[("Excel Files", "*.xlsx")]
    )
    
    if not file_path:
        return

    try:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for role, days_data in master_schedule.items():
                
                ordered_tasks = []
                for r in task_table:
                    if len(r) > 2 and r[0].strip() == role.strip() and r[2].strip():
                        shift = r[3].strip() if len(r) > 3 else ""
                        t_name = f"{r[2]} ({shift})" if shift else r[2]
                        if t_name not in ordered_tasks:
                            ordered_tasks.append(t_name)
                
                for d_num, d_data in days_data.items():
                    if isinstance(d_data, dict):
                        for t_name in d_data.keys():
                            if t_name not in ordered_tasks and not str(t_name).startswith("Other") and not str(t_name).startswith("Reten"):
                                ordered_tasks.append(t_name)

                headers = ["Task", "Shift", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
                rows = []
                
                m_idx = list(calendar.month_name).index(active_m)
                y_num = int(active_y)
                cal_matrix = calendar.Calendar(firstweekday=6).monthdayscalendar(y_num, m_idx)

                for week_idx, week in enumerate(cal_matrix):
                    
                    # A. Add the Week & Dates Row
                    week_row = [f"WEEK {week_idx + 1}", "Date ➔"]
                    for d in week:
                        week_row.append(str(d) if d != 0 else "")
                    rows.append(week_row)

                    # B. Add the standard Clinic Tasks
                    for t_full in ordered_tasks:
                        t_base = t_full.split(" (")[0]
                        t_shift = "AM" if "(AM)" in t_full else "PM" if "(PM)" in t_full else ""
                        
                        task_row = [t_base, t_shift]
                        for d in week:
                            if d == 0:
                                task_row.append("")
                            else:
                                day_tasks = days_data.get(str(d), days_data.get(d, {}))
                                assigned_staff = day_tasks.get(t_full, [])
                                clean_staff = [s for s in assigned_staff if s not in ["SHORTAGE", "Empty", "Empty (Postponed)"]]
                                task_row.append(", ".join(clean_staff))
                        rows.append(task_row)
                        
                    # C. Add the "Other" Rows
                    for other_t in ["Other (AM)", "Other (PM)"]:
                        sh = "AM" if "AM" in other_t else "PM"
                        other_row = ["Other", sh]
                        for d in week:
                            if d == 0:
                                other_row.append("")
                            else:
                                day_tasks = days_data.get(str(d), days_data.get(d, {}))
                                assigned_staff = day_tasks.get(other_t, [])
                                clean_staff = [s for s in assigned_staff if s not in ["SHORTAGE", "Empty", "Empty (Postponed)"]]
                                other_row.append(", ".join(clean_staff))
                        rows.append(other_row)
                        
                    # D. Add the "Reten" Rows
                    for reten_t in ["Reten (AM)", "Reten (PM)"]:
                        sh = "AM" if "AM" in reten_t else "PM"
                        reten_row = ["Reten", sh]
                        for d in week:
                            if d == 0:
                                reten_row.append("")
                            else:
                                day_tasks = days_data.get(str(d), days_data.get(d, {}))
                                assigned_staff = day_tasks.get(reten_t, [])
                                clean_staff = [s for s in assigned_staff if s not in ["SHORTAGE", "Empty", "Empty (Postponed)"]]
                                reten_row.append(", ".join(clean_staff))
                        rows.append(reten_row)
                        
                    # E. Add an empty row space between weeks
                    rows.append([""] * 9)

                df = pd.DataFrame(rows, columns=headers)
                df.to_excel(writer, sheet_name=role[:31], index=False) 
                
        messagebox.showinfo("Success", f"Timetable exported successfully to:\n{file_path}")
        
    except Exception as e:
        messagebox.showerror("Export Error", f"CRITICAL FAILURE saving Excel file. Make sure the file is CLOSED!\n\nError: {e}")

