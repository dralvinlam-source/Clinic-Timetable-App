import json
import os
from datetime import date
import calendar

SAVE_FILE = "clinic_memory.json"

current_month_name = list(calendar.month_name)[date.today().month]
current_year_str = str(date.today().year)

DEFAULT_DATA = {
    "ROLES": ["Dentist", "DSA", "Juruterapi", "PPK", "Driver"],
    "STAFF_HEADERS": ["Position (Role)", "Status (Perm/Contract)", "Staff Name", "Extra 1", "Extra 2"],
    "STAFF_TABLE": [
        # Dentists
        ["Dentist", "Permanent", "Dr. Alvin", "", ""],
        ["Dentist", "Contract", "Dr. Norina", "", ""],
        ["Dentist", "Permanent", "Dr. Siti", "", ""],
        ["Dentist", "Contract", "Dr. Ramesh", "", ""],
        # DSAs
        ["DSA", "Permanent", "DSA Sarah", "", ""],
        ["DSA", "Permanent", "DSA Aminah", "", ""],
        ["DSA", "Contract", "DSA Mei Ling", "", ""],
        ["DSA", "Permanent", "DSA Raji", "", ""],
        ["DSA", "Contract", "DSA Farah", "", ""],
        # Juruterapi (Dental Therapists)
        ["Juruterapi", "Permanent", "JP Zainab", "", ""],
        ["Juruterapi", "Permanent", "JP Nisa", "", ""],
        ["Juruterapi", "Contract", "JP Chong", "", ""],
        # PPK
        ["PPK", "Permanent", "PPK Ahmad", "", ""],
        ["PPK", "Contract", "PPK Zaki", "", ""],
        # Driver
        ["Driver", "Permanent", "En. Kumar", "", ""]
    ],
    "TASK_HEADERS": ["Position (Role)", "Status", "Task Name", "Shift (AM/PM/All Day)", "Extra"],
    "TASK_TABLE": [
        # Dentist Tasks
        ["Dentist", "Permanent", "OP (Outpatient)", "AM", ""],
        ["Dentist", "Contract", "AGP", "All Day", ""],
        ["Dentist", "Permanent", "Denture", "PM", ""],
        # DSA Tasks
        ["DSA", "Permanent", "Assist OP", "AM", ""],
        ["DSA", "Contract", "Assist AGP", "All Day", ""],
        ["DSA", "Permanent", "Counter Duty", "PM", ""],
        # Juruterapi Tasks
        ["Juruterapi", "Permanent", "School Visit", "AM", ""],
        ["Juruterapi", "Contract", "M&I Clinic", "All Day", ""],
        # PPK Tasks
        ["PPK", "Permanent", "Autoclave/Bilik Suci", "All Day", ""],
        ["PPK", "Contract", "Registration", "AM", ""],
        # Driver Tasks
        ["Driver", "Permanent", "Mobile Squad Transport", "AM", ""]
    ],
    "DEMAND_PLAN": {},  
    "HOLIDAYS": {},     
    "STAFF_PLAN": {},
    "CUSTOM_RESOLUTIONS": ["Close Room", "Call Relief Staff", "Double-Book Staff (Ignore Shift)", "PIC Manual Resolve"],
    "WORKLOAD_STATS": {}, 
    "WORKLOAD_OFFSETS": {}, 
    "SAVED_SCHEDULE": {}, # Tells Step 4 if you have a finished calendar to export
    "ACTIVE_MONTH": current_month_name,
    "ACTIVE_YEAR": current_year_str
}

def load_memory():
    if not os.path.exists(SAVE_FILE):
        save_memory(DEFAULT_DATA) 
        return DEFAULT_DATA
    else:
        with open(SAVE_FILE, "r") as file:
            return json.load(file)

def save_memory(data):
    with open(SAVE_FILE, "w") as file:
        json.dump(data, file, indent=4)

memory = load_memory()