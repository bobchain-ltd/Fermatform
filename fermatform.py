# -*- coding: utf-8 -*-
from flask import Flask, render_template, flash, redirect, url_for, request, Markup, jsonify
from flask_wtf import FlaskForm
from wtforms import FieldList
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, IntegerField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, NumberRange
from datetime import date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from slackclient import SlackClient
from itsdangerous import Signer
import time

# ------------- Keys, credentials and configs --------------------

with open('signer.key', 'r') as f:
    SECRET_KEY = f.read().rstrip()

with open('slack_call.key', 'r') as f:
    SLACK_CALL_TOKEN = unicode(f.read().rstrip())

with open('slackbot.auth', 'r') as f:
    SLACK_BOT_AUTH_TOKEN = f.read().rstrip()

with open('slackwebhook.auth', 'r') as f:
    SLACK_APP_AUTH_TOKEN = f.read().rstrip()


CURRENT_DATE = date.today().strftime('%m-%d-%Y')
YESTERDAY = (date.today()-timedelta(1)).strftime('%m-%d-%Y')

OPTIONS = [(1,"Very bad"),(2,"No good"),(3,"OK"),(4,"Above expected"),(5,"Supercool")]

scope = ['https://spreadsheets.google.com/feeds']

credentials = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', scope)

with open('slack_target_channel.name', 'r') as f:
    SLACK_TARGET_CHANNEL = f.read().rstrip()

with open('google_spreadsheet.name', 'r') as f:
    SPREADSHEET = f.read().rstrip()


# ------------------ Accessors and connections ----------------

scbot = SlackClient(SLACK_BOT_AUTH_TOKEN)   
scapp = SlackClient(SLACK_APP_AUTH_TOKEN)
#FIXME refact this to reconnect

# ------------------ Flask app init -------------------------

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ----------------- String signing functions ----------------

def sign_string(instring):
    s = Signer(SECRET_KEY)
    signed_string = s.sign(instring)
    return signed_string

def unsign_string(instring):
    s = Signer(SECRET_KEY)
    try:
        return s.unsign(instring) 
    except:
        return False


# --------------------- Google spreadsheet functions ---------------

def save_the_day(form, wks):
    gc = gspread.authorize(credentials)
    wks = gc.open(SPREADSHEET)

    days = wks.worksheet("Days")
    row = [YESTERDAY,form.dev_name.data,form.evaluation.data]
    days.append_row(row)

    return

def save_done_tasks(form, wks):
    done_tasks = wks.worksheet("Done tasks")

    for  task in form.tasks.data:
        row = [YESTERDAY,form.dev_name.data,task["task_name"],task["duration"]]
        done_tasks.append_row(row)

    return

def save_plans_and_discussion_requests(form, wks):
    discussion_requests = wks.worksheet("Discussion requests")
    planned_tasks = wks.worksheet("Planned tasks")

    for req in form.plans.data:

        row = [CURRENT_DATE,form.dev_name.data,req["plan_name"]]
        planned_tasks.append_row(row)

        slack_usernames_choices =dict(get_slack_user_choices())
        #print req["contacts"]
        if req["contacts"] != []:
            for individual in req["contacts"]:
                row = [CURRENT_DATE,form.dev_name.data,req["plan_name"],"@"+str(slack_usernames_choices[individual])]
                discussion_requests.append_row(row)
    return

def save_to_google(form):
    gc = gspread.authorize(credentials)
    wks = gc.open(SPREADSHEET)

    save_the_day(form, wks)
    save_done_tasks(form, wks)
    save_plans_and_discussion_requests(form, wks)
    del wks
    del gc
    return


# ----------------- Slack posting and helper functions ------------------

def get_slack_user_choices():

    slack_users = scbot.api_call("users.list")
    slack_usernames = [u["name"] for u in slack_users["members"]]
    slack_usernames_choices = []
    for s in range(len(slack_usernames)):
        slack_usernames_choices.append((s,slack_usernames[s]))
    return slack_usernames_choices

def get_slack_userobject(user_name):
    print "Calling API as bot to get users list..."

    slack_users = scbot.api_call("users.list")
    for item in slack_users["members"]:
        if item["name"] == user_name:
            user_object = item
    #user_object = (item for item in slack_users["members"] if item["name"] == user_name).next()
    #print slack_users["members"][0]['name']
    return user_object

def post_checkin_to_channel(form):
    print "Posting to Slack channel..."
    #print form.dev_name.data
    slack_user = get_slack_userobject(form.dev_name.data)

    #print slack_user["profile"]["image_24"]
    feeling = (item for item in OPTIONS if item[0] == form.evaluation.data).next()
    #print form.evaluation.data
    if form.evaluation.data == 1:
        feeling_color = "danger"
    elif form.evaluation.data == 2:
        feeling_color = "warning"
    elif form.evaluation.data > 3:
        feeling_color = "#439FE0"
    else:
        feeling_color = "good"

    final_text = " \n --- \n"

    tasks_value = ""#"Task name:"# \t\t Duration:\n" 
    duration_value = ""

    for task in form.tasks.data:
        tasks_value = tasks_value + task["task_name"] + "\n"#+ "\t      " + str(task["duration"])+ "\n"
        duration_value = duration_value + str(task["duration"]) + "\n"
    tasks_value+="\n"
    duration_value+="\n"
    plans_value = ""#"Planned task:"

    for req in form.plans.data:
        plans_value = plans_value + req["plan_name"] + "\n"

    scbot.api_call(
      "chat.postMessage",
      channel="#"+SLACK_TARGET_CHANNEL,
      #parse="full",
      #text=final_text,
      
      attachments= [
        {
            "title": "Daily Checkin",
            #"title_link": "http://google.com",
            "author_name": slack_user["profile"]["first_name"]+" "+slack_user["profile"]["last_name"]+" @"+slack_user["name"],
            "author_icon": slack_user["profile"]["image_24"],
            "color": "good",
            "text": final_text,
            "fields": [
                {
                    "title": "Tasks done yesterday:",
                    "value": tasks_value,
                    "short": True
                },
{
                    "title": "Duration (hours):",
                    "value": duration_value,
                    "short": True
                },
                ],
        },

{
            "color": feeling_color,
            "fields": [
                {
                    "title": "Feeling of success:",
                    "value": feeling[1],
                    "short": False
                },
                ],
                #"thumb_url": slack_user["profile"]["image_24"],
        },
        {
            "color": "good",
            "fields": [
                {
                    "title": "Tasks planned for today:",
                    "value": plans_value,
                    "short": False
                }
                ],
                "footer": "Bobchain Ltd.",
                "footer_icon": "https://i1.wp.com/mfsys.com.pk/wp-content/uploads/2016/06/blockchain.info-logo.jpg?resize=256%2C256"
        },

        ]) 
    return

def create_channel(channel_name):

    # https://api.slack.com/methods/channels.create
    # let slack modify the channel name
            
    response = scapp.api_call(
      "groups.create",
      name=channel_name,
      validate=False)

    # print response
    
    if response.get("error","")=="name_taken":
        response = scapp.api_call(
            "groups.list",
            exclude_archived=False
            )
        print "Name alredy taken. Unarchiving..."
        for channel in response["groups"]:
            print channel["name"]
            if channel["name"] == channel_name:
                channel_id = channel["id"]

            response = scapp.api_call(
                "groups.unarchive",
                channel_id=channel_id
            )
    else: 
        channel_id = response["group"]["id"]

    return channel_id

def set_channel_purpose_and_topic(channel_id, plan_name, originator_name):

    # set topic
    # https://api.slack.com/methods/channels.setTopic
    response = scapp.api_call(
      "groups.setTopic",
      channel=channel_id,
      topic=plan_name)

    # set purpose
    # https://api.slack.com/methods/channels.setPurpose
    # notify users about /archive in the topic desctiption
    purpose_text = "@" + originator_name + " plans to work on " + plan_name + " today, and feels the need to discuss it. \n Please cooperate with him to help the work! \n If you think the discussion is complete, please use /archive to close the channel! Thanks!"

    response = scapp.api_call(
      "groups.setPurpose",
      channel=channel_id,
      purpose=purpose_text)
    print "setPurpose response: ",response
    return

def post_to_start(channel_id):

    scbot.api_call(
      "chat.postMessage",
      channel=channel_id,
      text="Feel free to discuss!",
      username="Checkinbot",
      icon_url="https://i1.wp.com/mfsys.com.pk/wp-content/uploads/2016/06/blockchain.info-logo.jpg?resize=256%2C256")

    return

def join_channel(channel_id):

    # https://api.slack.com/methods/channels.join
    
    response = scbot.api_call(
      "channels.join",
      name=channel_id)

    return
          
def invite_user_to_channel(channel_id, user_name):
    slack_user = get_slack_userobject(user_name)

    print "Inviting user ", slack_user["name"].strip()," to ",channel_id.strip()," ..."

    #print "These are the channels..."
    #channels = scapp.api_call("groups.list")
    #for c in channels["groups"]:
    #    print c["id"]
    #    if c["id"] == channel_id:
    #        print "FOUND!!!!!!"

    response = scapp.api_call(
      "groups.invite",
      channel=channel_id.strip(),
      user=slack_user['id'])
    #print response
    return  

def create_channel_discussions(form):

    print "Creating Slack channels..."

    for req in form.plans.data:

        slack_usernames_choices =dict(get_slack_user_choices())
        #print req["contacts"]
        if req["contacts"] != []:
            print "Planned channel name: ",req["plan_name"]
            channel_id = create_channel(req["plan_name"])
            print "Channel id: ", channel_id
            #join_channel(channel_id)

            #invite original poster
            #invite_user_to_channel(channel_id, form.dev_name.data)
            #invite checkinbot
            invite_user_to_channel(channel_id, "checkinbot")

            for individual in req["contacts"]:
                # invite marked individual
                invite_user_to_channel(channel_id, slack_usernames_choices[individual])
            
            set_channel_purpose_and_topic(channel_id, req["plan_name"], form.dev_name.data)

            post_to_start(channel_id)
    return

def post_to_slack(form):
    print "Executing Slack tasks..."
    post_checkin_to_channel(form)
    create_channel_discussions(form)
    return

    
# ------------------- Flask form elements ------------------

class Checkin():
    dev_name = ""
    tasks = ""
    evaluation = ""
    plans = ""


class Task():
    task_name = ""
    duration = 0

class Plan():
    plan_name = ""
    contacts = ""
    

class TaskForm(NoCsrfForm):
    task_name = StringField('Task name', validators=[DataRequired()])
    duration = IntegerField('Duration of the task', validators=[DataRequired(), NumberRange(min=1, max=24)])

class PlanForm(NoCsrfForm):
    plan_name = StringField('Plan name', validators=[DataRequired()])
    contacts = SelectMultipleField('Contact persons', choices=get_slack_user_choices(), coerce=int)#StringField('Contact persons')


class CombinedForm(FlaskForm):
    dev_name = StringField('My name / nick', validators=[DataRequired()])
    #dev_name = SelectField('My name / nick', choices=get_slack_user_choices(), validators = [DataRequired()])

    tasks = FieldList(FormField(TaskForm, default=lambda: Task()))
    
    evaluation = SelectField('Self evaluation', coerce=int, choices=[(1,"Very bad"),(2,"No good"),(3,"OK"),(4,"Above expected"),(5,"Supercool")], default=3, validators = [DataRequired()])

    plans = FieldList(FormField(PlanForm, default=lambda: Plan()))
    
    #TODO: integrate Chosen.js
    #WARN: Manual include of JS file and call on selected class worked, but broke the row add script from page.js 

    submit = SubmitField('Submit')



# --------------------- Flask routes and logic -------------------------

@app.route('/thanks', methods=['GET',])
def thanks():
    return render_template('thanks.html')

@app.route('/unauthorized', methods=['GET',])
def unauthorized():
    return render_template('unauthorized.html')

@app.route('/', methods=['GET', 'POST'])
def index():


    user = unsign_string(request.args.get('user'))
    if user == False:
        return redirect(url_for('unauthorized'))

    checkin = Checkin()
    checkin.dev_name = user

    # if User has no tasks, provide an empty one so table is rendered
    if len(checkin.tasks) == 0:
        checkin.tasks = [Task()]
    if len(checkin.plans) == 0:
        checkin.plans = [Plan()]

    form = CombinedForm(obj=checkin)
    form.evaluation.default = 1
    
    if form.validate_on_submit():
        form.populate_obj(checkin)
        if checkin.dev_name!=user:
            return redirect(url_for('unauthorized'))
        save_to_google(form)
        post_to_slack(form)

        return redirect(url_for('thanks'))

    return render_template('multi.html', form=form)

@app.route('/checkin', methods=['GET','POST'])
def slack_checkin():
    #print request.form
    #print request.url_root
    #print request.form.getlist("token")[0]
    if request.method!="POST" or request.form.getlist("token")[0]!=SLACK_CALL_TOKEN:
        return redirect(url_for('unauthorized')) 
    
    slack_user_id = request.form.getlist("user_id")[0]
    slack_username = request.form.getlist("user_name")[0]
    link = request.url_root+"?user="+sign_string(slack_username)

    resp = {
    "response_type": "ephemeral",
    "text": "You can do your checkin under the link",
    "attachments": [
        {
            "title": "Daily Checkin",
            "title_link": link,
            "author_name": "Bobchain Ltd.",
            "author_icon": "https://i1.wp.com/mfsys.com.pk/wp-content/uploads/2016/06/blockchain.info-logo.jpg?resize=256%2C256",
            "color": "good"

        }
                    ]
    }
    return jsonify(resp)



# ------------------ Main app start ------------------

if __name__ == '__main__':

    app.run(debug=False)
