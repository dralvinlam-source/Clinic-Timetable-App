import customtkinter as ctk
import database

def open_roles_window(app):
    roles_window = ctk.CTkToplevel(app)
    roles_window.title("Master Data Setup")
    roles_window.geometry("900x550")
    
    # --- NEW: Pop to front, then unlock ---
    roles_window.attributes('-topmost', True)
    roles_window.after(100, lambda: roles_window.attributes('-topmost', False))
    roles_window.focus_force()
    # --------------------------------------

    top_frame = ctk.CTkFrame(roles_window, fg_color="transparent")
    top_frame.pack(pady=10, padx=20, fill="x")
    title_label = ctk.CTkLabel(top_frame, text="Staff & Task Database", font=("Arial", 20, "bold"))
    title_label.pack(side="left")

    all_staff_entries = []
    all_task_entries = []
    is_locked = True 

    def toggle_lock():
        nonlocal is_locked
        if is_locked:
            for entry in all_staff_entries + all_task_entries: entry.configure(state="normal")
            lock_btn.configure(text="🔓 Unlocked (Click to Save & Lock)", fg_color="#d9534f", hover_color="#c9302c")
            is_locked = False
        else:
            database.memory["STAFF_HEADERS"] = [all_staff_entries[i].get() for i in range(5)]
            new_staff_data = []
            for i in range(5, len(all_staff_entries), 5):
                row_data = [all_staff_entries[i+j].get().strip() for j in range(5)]
                if row_data[0] != "" or row_data[2] != "": new_staff_data.append(row_data)
            database.memory["STAFF_TABLE"] = new_staff_data

            database.memory["TASK_HEADERS"] = [all_task_entries[i].get() for i in range(5)]
            new_task_data = []
            for i in range(5, len(all_task_entries), 5):
                row_data = [all_task_entries[i+j].get().strip() for j in range(5)]
                if row_data[2] != "": new_task_data.append(row_data)
            database.memory["TASK_TABLE"] = new_task_data

            database.save_memory(database.memory)
            for entry in all_staff_entries + all_task_entries: entry.configure(state="disabled")
            lock_btn.configure(text="🔒 Locked", fg_color="#28a745", hover_color="#218838")
            is_locked = True

    lock_btn = ctk.CTkButton(top_frame, text="🔒 Locked", fg_color="#28a745", hover_color="#218838", command=toggle_lock)
    lock_btn.pack(side="right")

    tabview = ctk.CTkTabview(roles_window, width=850, height=400)
    tabview.pack(pady=5, padx=20, fill="both", expand=True)
    tab_staff = tabview.add("1. Staff List")
    tab_tasks = tabview.add("2. Task List")

    def build_master_grid(parent_tab, headers_key, table_key, entries_list, is_task_tab=False):
        scroll_frame = ctk.CTkScrollableFrame(parent_tab)
        scroll_frame.pack(fill="both", expand=True, pady=5)
        
        current_headers = database.memory.get(headers_key, ["Col1", "Col2", "Col3", "Col4", "Col5"])
        for col_index in range(5):
            entry = ctk.CTkEntry(scroll_frame, width=150, font=("Arial", 13, "bold"), text_color="#3498db")
            entry.grid(row=0, column=col_index, padx=2, pady=(5, 10)) 
            entry.insert(0, current_headers[col_index])
            entry.configure(state="disabled")
            entries_list.append(entry)

        current_data = database.memory.get(table_key, [])
        for row_index in range(30):
            for col_index in range(5):
                val = current_data[row_index][col_index] if row_index < len(current_data) and col_index < len(current_data[row_index]) else ""
                
                if col_index == 1: 
                    entry = ctk.CTkOptionMenu(scroll_frame, width=150, values=[" ", "Permanent", "Contract"])
                    entry.set(val if val in [" ", "Permanent", "Contract"] else " ")
                elif is_task_tab and col_index == 3: 
                    entry = ctk.CTkOptionMenu(scroll_frame, width=150, values=[" ", "AM", "PM", "All Day"])
                    entry.set(val if val in [" ", "AM", "PM", "All Day"] else " ")
                else: 
                    entry = ctk.CTkEntry(scroll_frame, width=150)
                    entry.insert(0, val)

                entry.grid(row=row_index+1, column=col_index, padx=2, pady=2)
                entry.configure(state="disabled")
                entries_list.append(entry)

    build_master_grid(tab_staff, "STAFF_HEADERS", "STAFF_TABLE", all_staff_entries, False)
    build_master_grid(tab_tasks, "TASK_HEADERS", "TASK_TABLE", all_task_entries, True)