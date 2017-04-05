# -*- coding: utf-8 -*-
from flask import Flask, render_template, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import FieldList
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange
from datetime import date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SECRET_KEY = 'a really not so random string'

app = Flask(__name__)
app.secret_key = SECRET_KEY

CURRENT_DATE = date.today().strftime('%m-%d-%Y')
YESTERDAY = (date.today()-timedelta(1)).strftime('%m-%d-%Y')

OPTIONS = {"Very bad":-2,"No good":-1,"OK":0,"Above expected":1,"Supercool":2}

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
    tasks = FieldList(FormField(TaskForm, default=lambda: Task()))
    
    evaluation = SelectField('Self evaluation', choices = [(o, o) for o in OPTIONS.keys()] , validators = [DataRequired()])

    plans = FieldList(FormField(PlanForm, default=lambda: Plan()))

    submit = SubmitField('Submit')

def save_the_day(form):
    days = wks.worksheet("Days")
    row=[YESTERDAY,form.dev_name.data,OPTIONS[form.evaluation.data]]
    days.append_row(row)
    return

def save_done_tasks(form):
    done_tasks = wks.worksheet("Done tasks")

    for  task in form.tasks.data:
        row=[YESTERDAY,form.dev_name.data,task["task_name"],task["duration"]]
        done_tasks.append_row(row)
    return

def save_discussion_requests(form):
    discussion_requests = wks.worksheet("Discussion requests")
    for req in form.contacts.data:
        if "," in req["contacts"]: 
            splitted=req["contacts"].split(",")
        elif " " in req["contacts"]:
            splitted=req["contacts"].split(" ")
        else:
            splitted=req

        for individual in splitted:
            row=[CURRENT_DATE,form.dev_name.data,req.plan_name.data,individual]
            discussion_requests.append_row(row)
    return

def save_to_google(form):
    #save_the_day(form)
    #save_done_tasks(form)
    return

@app.route('/thanks', methods=['GET',])
def thanks():
    return render_template('thanks.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    checkin = Checkin()

    # if User has no tasks, provide an empty one so table is rendered
    if len(checkin.tasks) == 0:
        checkin.tasks = [Task()]
    if len(checkin.plans) == 0:
        checkin.plans = [Plan()]

    form = CombinedForm(obj=checkin)

    if form.validate_on_submit():
        form.populate_obj(checkin)

        save_to_google(form)

        return redirect(url_for('thanks'))

    return render_template('multi.html', form=form)


if __name__ == '__main__':

    scope = ['https://spreadsheets.google.com/feeds']

    credentials = ServiceAccountCredentials.from_json_keyfile_name('f.json', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open("Checkins")

    app.run(debug=True)#, port=5000)
