# -*- coding: utf-8 -*-
from flask import Flask, render_template, flash
from flask_wtf import FlaskForm
from wtforms import FieldList
from wtforms import Form as NoCsrfForm
from wtforms.fields import StringField, FormField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange

SECRET_KEY = 'a really not so random string'

app = Flask(__name__)
app.secret_key = SECRET_KEY


class Checkin():
    dev_name = ""
    tasks = ""


class Task():
    task_name = ""
    duration = ""


class TaskForm(NoCsrfForm):
    task_name = StringField('Task name', validators=[DataRequired()])
    duration = IntegerField('Duration of the task', validators=[DataRequired(), NumberRange(min=1, max=24)])


class CombinedForm(FlaskForm):
    dev_name = StringField('Developer', validators=[DataRequired()])
    # we must provide empth Phone() instances else populate_obj will fail
    tasks = FieldList(FormField(TaskForm, default=lambda: Task()))
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    checkin = Checkin()

    # if User has no tasks, provide an empty one so table is rendered
    if len(checkin.tasks) == 0:
        checkin.tasks = [Task()]

    form = CombinedForm(obj=checkin)

    if form.validate_on_submit():
        form.populate_obj(checkin)
        flash("Saved Changes")
        for i in form.tasks.data:
            print i
        #flash()
    return render_template('multi.html', form=form)



if __name__ == '__main__':
    app.run(debug=True)#, port=5000)
