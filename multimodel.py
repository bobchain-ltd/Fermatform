# -*- coding: utf-8 -*-
from flask import Flask, render_template, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import FieldList
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange
from datetime import date, timedelta

SECRET_KEY = 'a really not so random string'

app = Flask(__name__)
app.secret_key = SECRET_KEY


class Checkin():
    current_date = date.today().strftime('%m-%d-%Y')
    yesterday = (date.today()-timedelta(1)).strftime('%m-%d-%Y')
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

    options = ["Very bad","No good","OK","Above expected","Supercool"]
    evaluation = SelectField('Self evaluation', choices = [(o, o) for o in options] , validators = [DataRequired()])

    plans = FieldList(FormField(PlanForm, default=lambda: Plan()))

    submit = SubmitField('Submit')

def save_to_google(form):
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
        flash("Saved Changes")
        save_to_google(form)
        return redirect(url_for('thanks'))

    return render_template('multi.html', form=form)



if __name__ == '__main__':
    app.run(debug=True)#, port=5000)
