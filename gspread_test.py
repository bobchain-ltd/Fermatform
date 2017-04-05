import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('f.json', scope)

gc = gspread.authorize(credentials)

print gc

#gc.openall()#open_by_url("https://docs.google.com/spreadsheets/d/18qWEJe7UTW51-mGv6v1CZcIt5Nt0u1phnLKUw9XQ25c/edit#gid=0")#open_by_key("18qWEJe7UTW51-mGv6v1CZcIt5Nt0u1phnLKUw9XQ25c")#("Checkins").sheet1
wks = gc.open("Checkins")
sheet = wks.worksheet("Done tasks")
sheet.resize(rows=1,cols=4)

sheet2 = wks.worksheet("Days")
sheet2.resize(rows=1,cols=3)

sheet2 = wks.worksheet("Discussion requests")
sheet2.resize(rows=1,cols=4)
#sheet.append_row(["a","b","c"])