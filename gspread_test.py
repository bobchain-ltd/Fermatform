import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('f.json', scope)

gc = gspread.authorize(credentials)

wks = gc.open("Checkins")
done_tasks = wks.worksheet("Done tasks")
days = wks.worksheet("Days")
discussion_requests = wks.worksheet("Discussion requests")
planned_tasks = wks.worksheet("Planned tasks")

#WARN: Do NOT comment this back, since it kills the spreadsheet content!
#days.resize(rows=1,cols=3)
#discussion_requests.resize(rows=1,cols=4)
#done_tasks.resize(rows=1,cols=4)
#planned_tasks.resize(rows=1,cols=3)

#sheet.append_row(["a","b","c"])