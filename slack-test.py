from slackclient import SlackClient

with open('slack.auth', 'r') as f:
	token=f.read().rstrip()
sc = SlackClient(token)

channels = sc.api_call(
  "channels.list",
  exclude_archived=1
)

for c in channels["channels"]:
	print c["name_normalized"]," ",c["id"]
	print " "


users=sc.api_call("users.list")

for u in users["members"]:
	print u["name"]
	print " "