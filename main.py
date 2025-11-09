import gspread
from google.oauth2.service_account import Credentials
import csv
import datetime

NUM_JUDGING_GROUPS = 4 
SESSION_DURATION_MINUTES = 10
BREAK_DURATION_MINUTES = 5
START_TIME_STR = "13:00"
END_TIME_STR = "16:00"
output_file = "judging_assignments.csv"

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)

sheet_id = "1jJMJdrKYDSat91D381fN4nYihXOrAC2UCxp51O5mbwk"
sheet = client.open_by_key(sheet_id)
worksheet = sheet.sheet1

all_data = worksheet.get_all_values()

all_projects = [] 

if not all_data or len(all_data) < 2:
    print("No data found in the sheet.")
    exit()

print("Fetching all projects...")
for row in all_data[1:]:
    try:
        name = row[2]
        devpost = row[1]
        
        if not name or not devpost:
            print(f"Skipping row with missing name or devpost: {row}")
            continue
            
        project_data = { "name": name, "devpost": devpost }
        all_projects.append(project_data)
        
    except IndexError:
        print(f"Skipping a row with incomplete data: {row}")

print(f"Found a total of {len(all_projects)} projects to distribute.")

judging_groups_assignments = [ [] for _ in range(NUM_JUDGING_GROUPS) ]

print(f"Distributing projects into {NUM_JUDGING_GROUPS} judging groups...")

for index, project in enumerate(all_projects):
    judging_group_index = index % NUM_JUDGING_GROUPS
    judging_groups_assignments[judging_group_index].append(project)

print(f"Writing master schedule to {output_file}...")

today = datetime.date.today()
start_dt = datetime.datetime.combine(today, datetime.datetime.strptime(START_TIME_STR, "%H:%M").time())
end_boundary_dt = datetime.datetime.combine(today, datetime.datetime.strptime(END_TIME_STR, "%H:%M").time())
session_delta = datetime.timedelta(minutes=SESSION_DURATION_MINUTES)
break_delta = datetime.timedelta(minutes=BREAK_DURATION_MINUTES)

max_sessions = 0
for group in judging_groups_assignments:
    if len(group) > max_sessions:
        max_sessions = len(group)

print(f"Schedule will have a maximum of {max_sessions} time slots.")

with open(output_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    
    header = ["Time"]
    for i in range(NUM_JUDGING_GROUPS):
        header.append(f"Team {i + 1}")
    writer.writerow(header)

    current_time = start_dt
    
    for session_index in range(max_sessions):
        
        session_start_time = current_time
        session_end_time = current_time + session_delta
        
        if session_end_time > end_boundary_dt:
            print(f"WARNING: Reached end time {END_TIME_STR}. "
                  f"Stopping schedule. Not all projects may be scheduled.")
            break
            
        start_time_formatted = session_start_time.strftime("%I:%M %p")
        
        row_to_write = [start_time_formatted]
        
        for group_index in range(NUM_JUDGING_GROUPS):
            try:
                project = judging_groups_assignments[group_index][session_index]
                combined_cell = f"{project['name']} ({project['devpost']})"
                row_to_write.append(combined_cell)
                
            except IndexError:
                row_to_write.append("")
        
        writer.writerow(row_to_write)
        
        current_time = session_end_time + break_delta

print(f"\nSuccessfully finished writing master schedule to {output_file}")


