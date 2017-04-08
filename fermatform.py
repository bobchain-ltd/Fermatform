# -*- coding: utf-8 -*-
from flask import Flask, render_template, flash, redirect, url_for, request, Markup, jsonify
from flask_wtf import FlaskForm
from wtforms import FieldList
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange
from datetime import date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from slackclient import SlackClient
from itsdangerous import Signer

with open('signer.key', 'r') as f:
    SECRET_KEY = f.read().rstrip()

with open('slack_call.key', 'r') as f:
    SLACK_CALL_TOKEN = unicode(f.read().rstrip())
    
app = Flask(__name__)
app.secret_key = SECRET_KEY

CURRENT_DATE = date.today().strftime('%m-%d-%Y')
YESTERDAY = (date.today()-timedelta(1)).strftime('%m-%d-%Y')

OPTIONS = [(1,"Very bad"),(2,"No good"),(3,"OK"),(4,"Above expected"),(5,"Supercool")]

#def get_slack_user_choices():
#    with open('slack.auth', 'r') as f:
#        SLACK_AUTH_TOKEN = f.read().rstrip()
#    sc = SlackClient(SLACK_AUTH_TOKEN)
#
#    slack_users = sc.api_call("users.list")
#    slack_usernames = [u["name"] for u in slack_users["members"]]
#    global slack_usernames_choices
#    slack_usernames_choices = []
#    for s in range(len(slack_usernames)):
#        slack_usernames_choices.append((s,slack_usernames[s]))
#    #print slack_usernames_choices
#    return slack_usernames_choices

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
    contacts = StringField('Contact persons')


class CombinedForm(FlaskForm):
    dev_name = StringField('My name / nick', validators=[DataRequired()])
    #dev_name = SelectField('My name / nick', choices=get_slack_user_choices(), validators = [DataRequired()])

    tasks = FieldList(FormField(TaskForm, default=lambda: Task()))
    
    evaluation = SelectField('Self evaluation', coerce=int, choices=[(1,"Very bad"),(2,"No good"),(3,"OK"),(4,"Above expected"),(5,"Supercool")], default=3, validators = [DataRequired()])

    plans = FieldList(FormField(PlanForm, default=lambda: Plan()))

    submit = SubmitField('Submit')

def save_the_day(form):
    days = wks.worksheet("Days")
    row = [YESTERDAY,form.dev_name.data,form.evaluation.data]
    days.append_row(row)
    return

def save_done_tasks(form):
    done_tasks = wks.worksheet("Done tasks")

    for  task in form.tasks.data:
        row = [YESTERDAY,form.dev_name.data,task["task_name"],task["duration"]]
        done_tasks.append_row(row)
    return

def save_plans_and_discussion_requests(form):
    discussion_requests = wks.worksheet("Discussion requests")
    planned_tasks = wks.worksheet("Planned tasks")

    for req in form.plans.data:

        row = [CURRENT_DATE,form.dev_name.data,req["plan_name"]]
        planned_tasks.append_row(row)

        if "," in req["contacts"]: 
            splitted = req["contacts"].split(",")
        elif " " in req["contacts"]:
            splitted = req["contacts"].split(" ")
        else:
            splitted = req["contacts"]

        if isinstance(splitted, basestring) and splitted != "":
            row = [CURRENT_DATE,form.dev_name.data,req["plan_name"],splitted.replace(" ", "")]
            discussion_requests.append_row(row)
        else:
            for individual in splitted:
                row = [CURRENT_DATE,form.dev_name.data,req["plan_name"],individual.replace(" ", "")]
                discussion_requests.append_row(row)
    return

def save_to_google(form):
    save_the_day(form)
    save_done_tasks(form)
    save_plans_and_discussion_requests(form)
    return

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
        save_to_google(form)

        return redirect(url_for('thanks'))

    return render_template('multi.html', form=form)

@app.route('/checkin', methods=['GET','POST'])
def slack_checkin():
    #print request.form
    #print request.url_root
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
            "author_name": "Fermat.org",
            "author_icon": "http://www.fermat.org/wp-content/uploads/2016/05/cropped-lcono_fermat_512x512-32x32.png",
            "color": "good"

        }
                    ]
    }
    return jsonify(resp)#Markup('Hello bello @%s!') % slack_username

if __name__ == '__main__':

    scope = ['https://spreadsheets.google.com/feeds']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('google_credentials.json', scope)
    gc = gspread.authorize(credentials)
    with open('google_spreadsheet.name', 'r') as f:
        SPREADSHEET = f.read().rstrip()

    wks = gc.open(SPREADSHEET)

    app.run(debug=False)
