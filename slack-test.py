from slackclient import SlackClient

with open('slackbot.auth', 'r') as f:
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
	if u["name"]=="lev":
		targetuser = u
	print u["name"]
	print u["id"]
	print " "


ims = sc.api_call(
	"im.list"
)

print ims
#print " "
#print " "

for im in ims["ims"]:
	if im["user"]==targetuser["id"]:
		im_id = im["id"]
		#print im["id"]
		#print " "

szergely = "U48LR3PCZ"
lev = "U4ABEDA83"

quit()

result = sc.api_call(
  "im.open",
  user=lev,
  text="Hello from Python! :tada:",
)
print result

sc.api_call(
  "chat.postMessage",
  channel=im_id,
  text="Hello from Python! :tada:",
)


#sc.api_call(
#  "chat.postMessage",
#  channel="#api-test",
#  text="Hello from Python! :tada:",
#)