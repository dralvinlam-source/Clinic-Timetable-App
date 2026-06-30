import customtkinter as ctk
import database
import calendar
from datetime import date

def open_plan_window(app):
    plan_window = ctk.CTkToplevel(app)
    plan_window.title("Edit Monthly Plan (Demand & Leave)")
    plan_window.geometry("1280x700") 
    
    # --- NEW: Pop to front, then unlock ---
    plan_window.attributes('-topmost', True)
    plan_window.after(100, lambda: plan_window.attributes('-topmost', False))
    plan_window.focus_force()
    # --------------------------------------

    if "DEMAND_PLAN" not in database.memory or isinstance(database.memory["DEMAND_PLAN"], list): database.memory["DEMAND_PLAN"] = {}
    if "STAFF_PLAN" not in database.memory: database.memory["STAFF_PLAN"] = {}

    top_frame = ctk.CTkFrame(plan_window, fg_color="transparent")
    top_frame.pack(pady=10, padx=20, fill="x")
    left_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
    left_frame.pack(side="left")
    ctk.CTkLabel(left_frame, text="Monthly Plan Setup", font=("Arial", 20, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 5))

    current_year = date.today().year
    
    month_var = ctk.StringVar(value=database.memory.get("ACTIVE_MONTH", list(calendar.month_name)[date.today().month]))
    year_var = ctk.StringVar(value=database.memory.get("ACTIVE_YEAR", str(current_year)))

    ctk.CTkLabel(left_frame, text="Month:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=(0, 5))
    ctk.CTkOptionMenu(left_frame, values=list(calendar.month_name)[1:], variable=month_var, width=100).grid(row=1, column=1, padx=(0, 15))
    ctk.CTkLabel(left_frame, text="Year:", font=("Arial", 12, "bold")).grid(row=1, column=2, padx=(0, 5))
    ctk.CTkOptionMenu(left_frame, values=[str(y) for y in range(current_year - 1, current_year + 10)], variable=year_var, width=80).grid(row=1, column=3)

    right_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
    right_frame.pack(side="right")
    ctk.CTkLabel(right_frame, text="Default Need:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5)
    default_fill_var = ctk.StringVar(value="1")
    ctk.CTkEntry(right_frame, textvariable=default_fill_var, width=30).grid(row=0, column=1, padx=5)
    
    demand_rows = [] 
    current_staff_entries = {} 
    last_staff_viewed = [""]   

    def run_auto_fill():
        fill_val = default_fill_var.get()
        holidays = database.memory.get("HOLIDAYS", {}).get(f"{month_var.get()}_{year_var.get()}", [])

        for r_data in demand_rows:
            if r_data["lock_checkbox"].get() == 1: continue 
            if r_data["task_entry"].get().strip() != "":
                for d_idx, d_ent in enumerate(r_data["day_entries"]):
                    d_num = d_idx + 1
                    # 💡 NO MORE HARDCODED WEEKENDS: Only checks if the day is ticked in the locks
                    if d_num not in holidays:
                        d_ent.delete(0, 'end')
                        d_ent.insert(0, fill_val)

    def save_monthly_plan():
        m_key = f"{month_var.get()}_{year_var.get()}"
        demand_data = {}
        for r_data in demand_rows:
            t_name = r_data["task_entry"].get()
            if t_name.strip() != "": demand_data[t_name] = [e.get() for e in r_data["day_entries"]]
        database.memory["DEMAND_PLAN"][m_key] = demand_data

        if last_staff_viewed[0]:
            staff_data = {}
            for d_key, (am_ent, pm_ent) in current_staff_entries.items(): staff_data[str(d_key)] = {"AM": am_ent.get(), "PM": pm_ent.get()}
            if m_key not in database.memory["STAFF_PLAN"]: database.memory["STAFF_PLAN"][m_key] = {}
            database.memory["STAFF_PLAN"][m_key][last_staff_viewed[0]] = staff_data

        database.memory["ACTIVE_MONTH"] = month_var.get()
        database.memory["ACTIVE_YEAR"] = year_var.get()
        database.save_memory(database.memory)
        save_btn.configure(text="✅ Saved!", fg_color="#28a745")
        plan_window.after(2000, lambda: save_btn.configure(text="💾 Save Plan", fg_color="#007bff"))

    ctk.CTkButton(right_frame, text="⚡ Auto-Fill", fg_color="#f39c12", hover_color="#d68910", text_color="black", font=("Arial", 12, "bold"), command=run_auto_fill, width=80).grid(row=0, column=2, padx=(10, 10))
    save_btn = ctk.CTkButton(right_frame, text="💾 Save Plan", fg_color="#007bff", hover_color="#0056b3", font=("Arial", 12, "bold"), command=save_monthly_plan, width=100)
    save_btn.grid(row=0, column=3)

    tabview = ctk.CTkTabview(plan_window, width=1250, height=550)
    tabview.pack(pady=5, padx=10, fill="both", expand=True)
    tab_demand = tabview.add("1. Clinic Demand")
    tab_leave = tabview.add("2. Staff Leave")

    def build_grids(*args):
        database.memory["ACTIVE_MONTH"] = month_var.get()
        database.memory["ACTIVE_YEAR"] = year_var.get()
        database.save_memory(database.memory)

        for widget in tab_demand.winfo_children(): widget.destroy()
        for widget in tab_leave.winfo_children(): widget.destroy()
        demand_rows.clear() 

        m_idx = list(calendar.month_name).index(month_var.get())
        y_num = int(year_var.get())
        num_days = calendar.monthrange(y_num, m_idx)[1]
        m_key = f"{month_var.get()}_{year_var.get()}"
        
        if "HOLIDAYS" not in database.memory: database.memory["HOLIDAYS"] = {}
        if m_key not in database.memory["HOLIDAYS"]: 
            # 💡 AUTO-TICK WEEKENDS BY DEFAULT FOR NEW MONTHS
            database.memory["HOLIDAYS"][m_key] = [d for d in range(1, num_days + 1) if date(y_num, m_idx, d).weekday() >= 5]
            
        holidays = database.memory["HOLIDAYS"][m_key]
        saved_demand = database.memory.get("DEMAND_PLAN", {}).get(m_key, {})

        # TAB 1 (DEMAND)
        scroll_demand = ctk.CTkScrollableFrame(tab_demand)
        scroll_demand.pack(fill="both", expand=True)
        ctk.CTkLabel(scroll_demand, text="🔒", font=("Arial", 12)).grid(row=0, column=0, padx=2, pady=5)
        ctk.CTkLabel(scroll_demand, text="Task / Shift", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        for day in range(1, num_days + 1): ctk.CTkLabel(scroll_demand, text=str(day), font=("Arial", 11, "bold")).grid(row=0, column=day + 1, padx=1, pady=5)

        ctk.CTkLabel(scroll_demand, text="🌴", font=("Arial", 12)).grid(row=1, column=0)
        
        # 💡 NEW BUTTONS: Block / Unblock Weekends easily
        btn_frame = ctk.CTkFrame(scroll_demand, fg_color="transparent")
        btn_frame.grid(row=1, column=1, sticky="e")
        
        def auto_block_weekends():
            weekends = [d for d in range(1, num_days + 1) if date(y_num, m_idx, d).weekday() >= 5]
            for w in weekends:
                if w not in database.memory["HOLIDAYS"][m_key]: database.memory["HOLIDAYS"][m_key].append(w)
            database.save_memory(database.memory)
            build_grids()

        def unblock_weekends():
            weekends = [d for d in range(1, num_days + 1) if date(y_num, m_idx, d).weekday() >= 5]
            database.memory["HOLIDAYS"][m_key] = [d for d in database.memory["HOLIDAYS"][m_key] if d not in weekends]
            database.save_memory(database.memory)
            build_grids()

        ctk.CTkButton(btn_frame, text="Unblock Wknds", width=90, height=20, font=("Arial", 10, "bold"), fg_color="#17a2b8", command=unblock_weekends).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Block Wknds", width=80, height=20, font=("Arial", 10, "bold"), fg_color="#d9534f", command=auto_block_weekends).pack(side="left", padx=2)
        ctk.CTkLabel(btn_frame, text="Locks ➔", font=("Arial", 11, "bold"), text_color="#d9534f").pack(side="left", padx=(5,0))

        def make_hol_toggle(d):
            def toggle():
                database.memory["HOLIDAYS"][m_key].remove(d) if d in database.memory["HOLIDAYS"][m_key] else database.memory["HOLIDAYS"][m_key].append(d)
                database.save_memory(database.memory)
                build_grids() 
            return toggle

        for day in range(1, num_days + 1):
            hol_cb = ctk.CTkCheckBox(scroll_demand, text="", width=20, checkbox_width=18, checkbox_height=18, fg_color="#d9534f", command=make_hol_toggle(day))
            if day in holidays: hol_cb.select()
            hol_cb.grid(row=1, column=day + 1, padx=2, pady=2)

        row_labels = [f"{r[2]} ({r[3]})" if r[3].strip() else r[2] for r in database.memory.get("TASK_TABLE", []) if len(r) > 3 and r[2].strip() != ""]
        if len(row_labels) < 15: row_labels.extend([""] * (15 - len(row_labels)))

        for row_idx, label_text in enumerate(row_labels, start=2):
            lock_cb = ctk.CTkCheckBox(scroll_demand, text="", width=20, checkbox_width=20, checkbox_height=20)
            lock_cb.grid(row=row_idx, column=0, padx=5, pady=1)

            name_entry = ctk.CTkEntry(scroll_demand, width=130)
            name_entry.grid(row=row_idx, column=1, padx=5, pady=1)
            if label_text:
                name_entry.insert(0, label_text)
                name_entry.configure(state="disabled") 
            
            day_entries = []
            saved_day_vals = saved_demand.get(label_text, [])
            
            for day in range(1, num_days + 1):
                day_entry = ctk.CTkEntry(scroll_demand, width=26)
                
                # 💡 RELY ONLY ON TICKBOXES
                is_blocked = day in holidays
                
                if is_blocked:
                    day_entry.insert(0, "X")
                    day_entry.configure(state="disabled", fg_color="#444444")
                else:
                    day_entry.insert(0, saved_day_vals[day - 1] if (day - 1) < len(saved_day_vals) else "")

                day_entry.grid(row=row_idx, column=day + 1, padx=1, pady=1)
                day_entries.append(day_entry)
            
            demand_rows.append({"task_entry": name_entry, "day_entries": day_entries, "lock_checkbox": lock_cb})

        # TAB 2 (STAFF)
        staff_names = [r[2] for r in database.memory.get("STAFF_TABLE", []) if len(r) > 2 and r[2].strip() != ""]
        if not staff_names: staff_names = ["No Staff Found"]
        last_staff_viewed[0] = staff_names[0]

        top_bar = ctk.CTkFrame(tab_leave, fg_color="transparent")
        top_bar.pack(fill="x", pady=5)
        ctk.CTkLabel(top_bar, text="Select Staff:", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        selected_staff = ctk.StringVar(value=staff_names[0])

        scroll_staff = ctk.CTkScrollableFrame(tab_leave)
        scroll_staff.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(scroll_staff, text="Date", font=("Arial", 14, "bold"), width=120, anchor="w").grid(row=0, column=0, padx=10, pady=5)
        ctk.CTkLabel(scroll_staff, text="AM Shift / Task", font=("Arial", 14, "bold"), width=300).grid(row=0, column=1, padx=10, pady=5)
        ctk.CTkLabel(scroll_staff, text="PM Shift / Task", font=("Arial", 14, "bold"), width=300).grid(row=0, column=2, padx=10, pady=5)

        def draw_staff_grid(new_staff=None):
            if new_staff is not None and last_staff_viewed[0] != "":
                staff_data = {str(k): {"AM": am.get(), "PM": pm.get()} for k, (am, pm) in current_staff_entries.items()}
                if m_key not in database.memory["STAFF_PLAN"]: database.memory["STAFF_PLAN"][m_key] = {}
                database.memory["STAFF_PLAN"][m_key][last_staff_viewed[0]] = staff_data
                last_staff_viewed[0] = new_staff

            for widget in scroll_staff.winfo_children():
                if int(widget.grid_info().get("row")) > 0: widget.destroy()
            current_staff_entries.clear()

            saved_plan = database.memory.get("STAFF_PLAN", {}).get(m_key, {}).get(last_staff_viewed[0], {})

            current_staff = last_staff_viewed[0]
            staff_roles = {r[2]: r[0] for r in database.memory.get("STAFF_TABLE", []) if len(r) > 2 and r[2].strip() != ""}
            role = staff_roles.get(current_staff, "")
            role_tasks = [r[2] for r in database.memory.get("TASK_TABLE", []) if r[0] == role and len(r)>2 and r[2].strip()]
            dropdown_options = [""] + sorted(list(set(role_tasks)))

            for day in range(1, num_days + 1):
                cur_date = date(y_num, m_idx, day)
                is_blocked = day in holidays

                ctk.CTkLabel(scroll_staff, text=f"{day} ({cur_date.strftime('%a')})", font=("Arial", 13, "bold"), width=120, anchor="w", text_color="#d9534f" if is_blocked else "white").grid(row=day, column=0, padx=10, pady=2)
                
                if is_blocked:
                    am_ent = ctk.CTkEntry(scroll_staff, width=300, font=("Arial", 12))
                    pm_ent = ctk.CTkEntry(scroll_staff, width=300, font=("Arial", 12))
                    msg = "Blocked" 
                    am_ent.insert(0, msg); pm_ent.insert(0, msg)
                    am_ent.configure(state="disabled", fg_color="#444444")
                    pm_ent.configure(state="disabled", fg_color="#444444")
                else:
                    am_ent = ctk.CTkComboBox(scroll_staff, width=300, font=("Arial", 12), values=dropdown_options, fg_color=("white", "gray20"), button_color=("white", "gray20"), button_hover_color=("gray85", "gray30"))
                    pm_ent = ctk.CTkComboBox(scroll_staff, width=300, font=("Arial", 12), values=dropdown_options, fg_color=("white", "gray20"), button_color=("white", "gray20"), button_hover_color=("gray85", "gray30"))
                    am_ent.set(saved_plan.get(str(day), {}).get("AM", ""))
                    pm_ent.set(saved_plan.get(str(day), {}).get("PM", ""))

                am_ent.grid(row=day, column=1, padx=10, pady=2)
                pm_ent.grid(row=day, column=2, padx=10, pady=2)
                current_staff_entries[day] = (am_ent, pm_ent)

        draw_staff_grid()
        ctk.CTkOptionMenu(top_bar, values=staff_names, variable=selected_staff, width=200, command=draw_staff_grid).pack(side="left")

    build_grids()
    month_var.trace_add("write", build_grids)
    year_var.trace_add("write", build_grids)