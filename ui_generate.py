import customtkinter as ctk
import database
import calendar
from datetime import date
import random

def open_generate_window(app):
    gen_window = ctk.CTkToplevel(app)
    gen_window.title("AI Timetable Generation")
    gen_window.geometry("1280x750")

    gen_window.attributes('-topmost', True)
    gen_window.after(100, lambda: gen_window.attributes('-topmost', False))
    gen_window.after(0, lambda: gen_window.state("zoomed"))
    gen_window.focus_force()

    active_m = database.memory.get("ACTIVE_MONTH", "January")
    active_y = database.memory.get("ACTIVE_YEAR", "2026")
    month_key = f"{active_m}_{active_y}"

    if "WORKLOAD_OFFSETS" not in database.memory: database.memory["WORKLOAD_OFFSETS"] = {}
    if "SAVED_SCHEDULE" not in database.memory: database.memory["SAVED_SCHEDULE"] = {}

    top_frame = ctk.CTkFrame(gen_window, fg_color="transparent")
    top_frame.pack(pady=5, padx=20, fill="x")
    ctk.CTkLabel(top_frame, text="AI Planner & Workload Dashboard", font=("Arial", 20, "bold")).pack(side="left")
    ctk.CTkLabel(top_frame, text=f"Target Month: {active_m} {active_y}", font=("Arial", 16, "bold"), text_color="#3498db").pack(side="right", padx=20)

    content_frame = ctk.CTkFrame(gen_window, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, padx=10, pady=5)

    left_panel = ctk.CTkFrame(content_frame)
    left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

    right_panel = ctk.CTkFrame(content_frame, width=320)
    right_panel.pack(side="right", fill="y", padx=(5, 0))

    gen_btn = ctk.CTkButton(right_panel, text="🧠 GENERATE AI TIMETABLE", font=("Arial", 14, "bold"), height=50, fg_color="#28a745", hover_color="#218838")
    gen_btn.pack(pady=(10, 5), fill="x", padx=10)

    save_btn = ctk.CTkButton(right_panel, text="💾 SAVE TIMETABLE", font=("Arial", 14, "bold"), height=50, fg_color="#007bff", hover_color="#0056b3")
    save_btn.pack(pady=(5, 10), fill="x", padx=10)

    ctk.CTkLabel(right_panel, text="📊 Finalized Workload Counter", font=("Arial", 14, "bold")).pack(pady=(15, 0))
    workload_frame = ctk.CTkScrollableFrame(right_panel)
    workload_frame.pack(fill="both", expand=True, padx=10, pady=5)

    staff_roles = {r[2]: r[0] for r in database.memory.get("STAFF_TABLE", []) if len(r)>2 and r[2].strip()}
    roles_with_staff = list(set(staff_roles.values()))
    if not roles_with_staff: roles_with_staff = ["Dentist"]

    m_idx = list(calendar.month_name).index(active_m)
    y_num = int(active_y)
    num_days = calendar.monthrange(y_num, m_idx)[1]

    task_table = database.memory.get("TASK_TABLE", [])
    
    raw_demand = database.memory.get("DEMAND_PLAN", {}).get(month_key, {})
    demand_plan = {str(k).strip(): v for k, v in raw_demand.items()}
    
    staff_plan = database.memory.get("STAFF_PLAN", {}).get(month_key, {})

    master_schedule = {role: {} for role in roles_with_staff}
    has_generated = False
    
    tabview = ctk.CTkTabview(left_panel)
    tabview.pack(fill="both", expand=True, padx=10, pady=5)
    ui_tabs = {role: tabview.add(f"{role} Timetable") for role in roles_with_staff}
    cal_matrix = calendar.Calendar(firstweekday=6).monthdayscalendar(y_num, m_idx)
    days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    def get_current_totals():
        current_shifts = {s: 0 for s in staff_roles.keys()}
        for role, days in master_schedule.items():
            for d, tasks in days.items():
                for t, assignments in tasks.items():
                    if "Reten" in t: continue 
                    for a in assignments:
                        if a in current_shifts: 
                            current_shifts[a] += 1
                        elif " [" in a:
                            name_part = a.split(" [")[0]
                            if name_part in current_shifts: current_shifts[name_part] += 1
        return current_shifts, {s: current_shifts[s] + int(database.memory["WORKLOAD_OFFSETS"].get(s, 0)) for s in staff_roles.keys()}

    def update_workload_ui():
        cur, fin = get_current_totals()
        for w in workload_frame.winfo_children(): w.destroy()
        for s, total in sorted(fin.items(), key=lambda x: x[1], reverse=True):
            f = ctk.CTkFrame(workload_frame, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"{s[:10]}: {cur[s]} + ").pack(side="left")
            e = ctk.CTkEntry(f, width=35, height=22); e.insert(0, str(database.memory["WORKLOAD_OFFSETS"].get(s, 0))); e.pack(side="left")
            ctk.CTkLabel(f, text=f" = {total}", font=("Arial", 12, "bold")).pack(side="left", padx=5)
            e.bind("<Return>", lambda ev, sn=s, en=e: [database.memory["WORKLOAD_OFFSETS"].update({sn: int(en.get())}), database.save_memory(database.memory), update_workload_ui()])

    def open_assignment_popup(role, day, t_name, shift, slot_index):
        current_assignee = master_schedule[role][day][t_name][slot_index]
        
        popup = ctk.CTkToplevel(gen_window)
        popup.title("Modify Assignment & Resolve Conflicts")
        popup.geometry("600x650")
        popup.attributes('-topmost', True)
        popup.after(0, lambda: popup.state("zoomed"))
        
        header_color = "#d9534f" if current_assignee == "SHORTAGE" else "#4285F4"
        if "Reten" in t_name: header_color = "#9b59b6"
        ctk.CTkLabel(popup, text=f"Modifying Day {day} - {t_name}", font=("Arial", 16, "bold"), text_color=header_color).pack(pady=(15, 5))
        ctk.CTkLabel(popup, text=f"Currently Assigned: {current_assignee}", font=("Arial", 14)).pack(pady=5)

        _, finalized_totals = get_current_totals()
        eligible_staff = [s for s, r in staff_roles.items() if r == role]
        
        all_base_tasks = [r[2].strip() for r in task_table if r[0] == role and r[2].strip()]
        
        free_staff = []
        leave_staff = []
        busy_staff = {} 

        day_tasks = master_schedule[role].get(day, {})
        target_sh = "AM" if "AM" in shift else "PM" if "PM" in shift else ""

        for s in eligible_staff:
            if s == current_assignee: continue 
            
            s_leave = staff_plan.get(s, {}).get(str(day), {})
            reason = s_leave.get(target_sh, "").strip() if target_sh else ""
            
            is_base_task = any(reason.upper() == b.upper() for b in all_base_tasks)

            if reason and reason not in ["X", "Weekend", "Holiday", "None", "Blocked"] and not is_base_task:
                leave_staff.append((s, reason))
                continue
            
            is_busy = False
            for other_t, assignments in day_tasks.items():
                if "Other" not in other_t and "Reten" not in other_t and s in assignments:
                    idx = assignments.index(s)
                    other_sh = "AM" if "AM" in other_t else "PM" if "PM" in other_t else ""
                    if other_sh == target_sh or not target_sh:
                        busy_staff[s] = (other_t, idx)
                        is_busy = True
                        break
            
            if not is_busy:
                free_staff.append(s)

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def apply_resolution(new_val, swap_info=None, pull_info=None, double_book=False):
            if swap_info and not double_book:
                old_task, old_idx = swap_info
                master_schedule[role][day][old_task][old_idx] = current_assignee 
            
            if pull_info and not double_book:
                old_task, old_idx = pull_info
                master_schedule[role][day][old_task][old_idx] = "SHORTAGE"
            
            if new_val and new_val not in ["SHORTAGE", "Empty"]:
                r_key = f"Reten ({target_sh})" if target_sh else ""
                if r_key and r_key in master_schedule[role][day]:
                    if new_val in master_schedule[role][day][r_key]:
                        master_schedule[role][day][r_key].remove(new_val)

            master_schedule[role][day][t_name][slot_index] = new_val
            popup.destroy()
            draw_calendar_ui() 
            update_workload_ui()

        if free_staff:
            free_staff.sort(key=lambda x: finalized_totals[x]) 
            ctk.CTkLabel(scroll, text="Available Staff (Lowest Workload First):", font=("Arial", 12, "bold"), text_color="#28a745").pack(anchor="w", pady=(10,5))
            for s in free_staff:
                ctk.CTkButton(scroll, text=f"Assign {s} (Total: {finalized_totals[s]})", fg_color="#4285F4", command=lambda st=s: apply_resolution(st)).pack(pady=2, fill="x")

        if busy_staff:
            ctk.CTkLabel(scroll, text="Busy Staff (Requires Swap or Pull):", font=("Arial", 12, "bold"), text_color="#f39c12").pack(anchor="w", pady=(15,5))
            for s, (old_t, old_idx) in busy_staff.items():
                frame = ctk.CTkFrame(scroll, fg_color=("gray90", "gray15"))
                frame.pack(fill="x", pady=2)
                ctk.CTkLabel(frame, text=f"{s} is on {old_t[:10]}", font=("Arial", 11)).pack(side="left", padx=10)
                
                if current_assignee not in ["SHORTAGE", "Empty"]:
                    ctk.CTkButton(frame, text="Swap", width=50, fg_color="#17a2b8", command=lambda st=s, ot=(old_t, old_idx): apply_resolution(st, swap_info=ot)).pack(side="right", padx=2, pady=5)
                
                ctk.CTkButton(frame, text="Pull", width=50, fg_color="#d9534f", command=lambda st=s, ot=(old_t, old_idx): apply_resolution(st, pull_info=ot)).pack(side="right", padx=2, pady=5)
                ctk.CTkButton(frame, text="+ Double Book", width=90, fg_color="#28a745", command=lambda st=s: apply_resolution(st, double_book=True)).pack(side="right", padx=2, pady=5)

        if leave_staff:
            ctk.CTkLabel(scroll, text="Staff on Leave/Meeting:", font=("Arial", 12, "bold"), text_color="#d9534f").pack(anchor="w", pady=(15,5))
            for s, reason in leave_staff:
                ctk.CTkButton(scroll, text=f"Override Leave: {s} ({reason[:10]})", fg_color="#d9534f", command=lambda st=s: apply_resolution(st)).pack(pady=2, fill="x")

        ctk.CTkLabel(scroll, text="Other Actions:", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", pady=(15,5))
        ctk.CTkButton(scroll, text="Leave Empty / SHORTAGE", fg_color="#6c757d", command=lambda: apply_resolution("SHORTAGE")).pack(pady=2, fill="x")
        
        custom_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        custom_frame.pack(fill="x", pady=5)
        custom_entry = ctk.CTkEntry(custom_frame, placeholder_text="Custom (e.g. Locum)")
        custom_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(custom_frame, text="Apply", width=60, command=lambda: apply_resolution(custom_entry.get())).pack(side="right")
        
        def remove_slot():
            master_schedule[role][day][t_name].pop(slot_index)
            draw_calendar_ui(); update_workload_ui(); popup.destroy()
            
        if "Other" in t_name or "Reten" in t_name:
            ctk.CTkButton(scroll, text="🗑️ DELETE SLOT", fg_color="#d9534f", command=remove_slot).pack(pady=15, fill="x", padx=20)

    def draw_calendar_ui():
        for role, tab in ui_tabs.items():
            if not hasattr(tab, "main_scroll"):
                tab.main_scroll = ctk.CTkScrollableFrame(tab, fg_color=("gray95", "gray10")); tab.main_scroll.pack(fill="both", expand=True)
            try: cur_y = tab.main_scroll._parent_canvas.yview()[0]
            except: cur_y = 0
            for w in tab.main_scroll.winfo_children(): w.destroy()
            if not has_generated:
                ctk.CTkLabel(tab.main_scroll, text="No Schedule Generated").pack(pady=100); continue

            role_tasks = [{"full": f"{r[2].strip()} ({r[3].strip()})" if r[3].strip() else r[2].strip(), "base": r[2].strip(), "sh": r[3].strip()} for r in task_table if r[0] == role and r[2].strip()]
            
            for week_idx, week in enumerate(cal_matrix):
                wf = ctk.CTkFrame(tab.main_scroll, fg_color=("#cccccc", "#444444"), corner_radius=0); wf.pack(fill="x", padx=5, pady=10)
                
                # 💡 NEW FIX: PERFECT COLUMN ALIGNMENT 
                wf.grid_columnconfigure(0, weight=0, minsize=160) # Lock Task Name Width
                wf.grid_columnconfigure(1, weight=0, minsize=60)  # Lock Shift Width
                wf.grid_columnconfigure((2,3,4,5,6,7,8), weight=1, uniform="daycol") # Lock all 7 days exactly equally

                for c_idx, d_num in enumerate(week):
                    txt = f"{d_num} {days_of_week[c_idx]}" if d_num != 0 else ""
                    ctk.CTkLabel(wf, text=txt, font=("Arial", 11, "bold")).grid(row=0, column=c_idx+2)

                for r_idx, t in enumerate(role_tasks, start=1):
                    ctk.CTkLabel(wf, text=t["base"], font=("Arial", 11, "bold"), anchor="w").grid(row=r_idx, column=0, sticky="w", padx=10)
                    ctk.CTkLabel(wf, text=t["sh"]).grid(row=r_idx, column=1)
                    
                    for c_idx, d_num in enumerate(week):
                        if d_num != 0:
                            cell = ctk.CTkFrame(wf, fg_color=("white", "gray20")); cell.grid(row=r_idx, column=c_idx+2, sticky="nsew", padx=1, pady=1)
                            for s_idx, ass in enumerate(master_schedule[role].get(d_num, {}).get(t["full"], [])):
                                b = ctk.CTkButton(cell, text=ass[:10], height=22, font=("Arial", 11, "bold"))
                                b.configure(command=lambda r=role, d=d_num, t_f=t["full"], s=t["sh"], i=s_idx: open_assignment_popup(r, d, t_f, s, i))
                                b.pack(fill="x", pady=2, padx=2)
                        else:
                            # Ghost cell for blank days to keep structure locked
                            ctk.CTkFrame(wf, fg_color="transparent").grid(row=r_idx, column=c_idx+2, sticky="nsew", padx=1, pady=1)

                sr = len(role_tasks)+1
                for o_idx, o_name in enumerate(["Other (AM)", "Other (PM)"], start=sr):
                    sh = "AM" if "AM" in o_name else "PM"
                    ctk.CTkLabel(wf, text="Other", font=("Arial", 11, "italic"), anchor="w").grid(row=o_idx, column=0, sticky="w", padx=10)
                    ctk.CTkLabel(wf, text=sh).grid(row=o_idx, column=1)
                    
                    for c_idx, d_num in enumerate(week):
                        if d_num != 0:
                            cell = ctk.CTkFrame(wf, fg_color=("gray90", "gray25")); cell.grid(row=o_idx, column=c_idx+2, sticky="nsew", padx=1, pady=1)
                            for s_idx, ass in enumerate(master_schedule[role].get(d_num, {}).get(o_name, [])):
                                b = ctk.CTkButton(cell, text=ass[:15], fg_color="#f39c12", height=22, font=("Arial", 11, "bold"))
                                b.configure(command=lambda r=role, d=d_num, t_o=o_name, s=sh, i=s_idx: open_assignment_popup(r, d, t_o, s, i))
                                b.pack(fill="x", pady=2, padx=2)
                            ctk.CTkButton(cell, text="➕ Add", height=20, fg_color="#28a745", command=lambda r=role, d=d_num, t_o=o_name: [master_schedule[r][d].setdefault(t_o, []).append("Empty"), draw_calendar_ui()]).pack(pady=2)
                        else:
                            ctk.CTkFrame(wf, fg_color="transparent").grid(row=o_idx, column=c_idx+2, sticky="nsew", padx=1, pady=1)
                            
                sr2 = sr + 2
                for r_idx, r_name in enumerate(["Reten (AM)", "Reten (PM)"], start=sr2):
                    sh = "AM" if "AM" in r_name else "PM"
                    ctk.CTkLabel(wf, text="Reten", font=("Arial", 11, "italic", "bold"), anchor="w").grid(row=r_idx, column=0, sticky="w", padx=10)
                    ctk.CTkLabel(wf, text=sh).grid(row=r_idx, column=1)
                    
                    for c_idx, d_num in enumerate(week):
                        if d_num != 0:
                            cell = ctk.CTkFrame(wf, fg_color=("gray90", "gray25")); cell.grid(row=r_idx, column=c_idx+2, sticky="nsew", padx=1, pady=1)
                            for s_idx, ass in enumerate(master_schedule[role].get(d_num, {}).get(r_name, [])):
                                b = ctk.CTkButton(cell, text=ass[:15], fg_color="#9b59b6", height=22, font=("Arial", 11, "bold")) 
                                b.configure(command=lambda r=role, d=d_num, t_o=r_name, s=sh, i=s_idx: open_assignment_popup(r, d, t_o, s, i))
                                b.pack(fill="x", pady=2, padx=2)
                            ctk.CTkButton(cell, text="➕ Add", height=20, fg_color="#28a745", command=lambda r=role, d=d_num, t_o=r_name: [master_schedule[r][d].setdefault(t_o, []).append("Empty"), draw_calendar_ui()]).pack(pady=2)
                        else:
                            ctk.CTkFrame(wf, fg_color="transparent").grid(row=r_idx, column=c_idx+2, sticky="nsew", padx=1, pady=1)

            if cur_y > 0: tab.main_scroll.after(15, lambda: tab.main_scroll._parent_canvas.yview_moveto(cur_y))

    def generate_schedule():
        nonlocal has_generated
        import random 
        
        ai_w = {s: int(database.memory["WORKLOAD_OFFSETS"].get(s, 0)) for s in staff_roles.keys()}
        task_counts = {s: {} for s in staff_roles.keys()} 

        for role in roles_with_staff:
            master_schedule[role] = {d: {} for d in range(1, num_days + 1)}
            
            role_ts = [(f"{r[2].strip()} ({r[3].strip()})" if r[3].strip() else r[2].strip(), r[3].strip(), r[2].strip()) for r in task_table if r[0] == role and r[2].strip()]
            all_base_tasks = list(set([t[2] for t in role_ts]))
            
            for day in range(1, num_days + 1):
                d_str = str(day)
                assigned = {s: [] for s in staff_roles if staff_roles[s] == role}
                
                # 💡 Check if this specific day is manually ticked as a Blocked Day
                is_blocked = day in database.memory.get("HOLIDAYS", {}).get(month_key, [])

                daily_tasks = list(role_ts)
                random.seed(day) 
                random.shuffle(daily_tasks)

                for t_f, t_s, t_base in daily_tasks:
                    d_list = demand_plan.get(t_f, ["0"]*31)
                    val = d_list[day-1] if day-1 < len(d_list) else "0"
                    
                    # 💡 If day is blocked (ticked), demand is 0
                    if is_blocked or str(val).strip().upper() in ["X", ""]: dmd = 0
                    else:
                        try: dmd = int(val)
                        except: dmd = 0
                        
                    master_schedule[role][day][t_f] = []
                    target_shift = "AM" if "AM" in t_s else "PM"

                    for s in list(assigned.keys()):
                        s_plan_val = staff_plan.get(s, {}).get(d_str, {}).get(target_shift, "").strip()
                        if s_plan_val.upper() == t_base.upper() and t_s not in assigned[s]:
                            master_schedule[role][day][t_f].append(s)
                            assigned[s].append(t_s)
                            ai_w[s] += 1
                            task_counts[s][t_base] = task_counts[s].get(t_base, 0) + 1
                            dmd -= 1 

                    for _ in range(max(0, dmd)):
                        avail = [s for s in assigned if t_s not in assigned[s] and staff_plan.get(s, {}).get(d_str, {}).get(target_shift, "").strip() in ["", "X"]]
                        
                        if avail:
                            avail.sort(key=lambda x: (
                                task_counts[x].get(t_base, 0), 
                                ai_w[x],
                                random.random()
                            ))
                            c = avail[0]
                            master_schedule[role][day][t_f].append(c)
                            assigned[c].append(t_s)
                            ai_w[c] += 1
                            task_counts[c][t_base] = task_counts[c].get(t_base, 0) + 1
                        else: 
                            master_schedule[role][day][t_f].append("SHORTAGE")
                            
                # 3. OTHER ROWS
                for o_t in ["Other (AM)", "Other (PM)"]:
                    sh = "AM" if "AM" in o_t else "PM"
                    master_schedule[role][day][o_t] = []
                    
                    if is_blocked:
                        continue
                        
                    for s in assigned:
                        res = staff_plan.get(s, {}).get(d_str, {}).get(sh, "").strip()
                        is_base_task = any(res.upper() == b.upper() for b in all_base_tasks)
                        if res not in ["", "X", "Weekend", "Holiday", "Blocked"] and not is_base_task and sh not in assigned[s]:
                            master_schedule[role][day][o_t].append(f"{s} [{res}]")
                            assigned[s].append(sh)
                            
                # 4. RETEN ROWS (Free Staff)
                for r_t in ["Reten (AM)", "Reten (PM)"]:
                    sh = "AM" if "AM" in r_t else "PM"
                    master_schedule[role][day][r_t] = []
                    
                    if is_blocked:
                        continue 
                        
                    for s in assigned:
                        res = staff_plan.get(s, {}).get(d_str, {}).get(sh, "").strip()
                        if res in ["", "X"] and sh not in assigned[s]:
                            master_schedule[role][day][r_t].append(s)
                            
        has_generated = True
        draw_calendar_ui()
        update_workload_ui()

    def save_timetable():
        database.memory["SAVED_SCHEDULE"][month_key] = master_schedule; database.save_memory(database.memory)
        save_btn.configure(text="✅ SAVED!", fg_color="#28a745"); gen_window.after(2000, lambda: save_btn.configure(text="💾 SAVE TIMETABLE", fg_color="#007bff"))

    gen_btn.configure(command=generate_schedule); save_btn.configure(command=save_timetable)
    if month_key in database.memory.get("SAVED_SCHEDULE", {}):
        saved = database.memory["SAVED_SCHEDULE"][month_key]
        for r, d_dict in saved.items(): master_schedule[r] = {int(k): v for k, v in d_dict.items()}
        has_generated = True
    draw_calendar_ui(); update_workload_ui()