from slackclient import SlackClient

with open('slack.auth', 'r') as f:
	token=f.read().rstrip()
print token

#token="xoxp-145472380709-146388452275-166445283399-d06496f8ed102be9bb858bce7f86c0e8"
sc = SlackClient(token)

channels = sc.api_call(
  "channels.list",
  exclude_archived=1
)

print channels
