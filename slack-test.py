from slackclient import SlackClient

with open('slack.auth', 'r') as f:
	token=f.read()
print token
sc = SlackClient(token)

channels = sc.api_call(
  "channels.list",
  exclude_archived=1
)

print channels