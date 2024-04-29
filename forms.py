from wtforms import StringField, PasswordField, BooleanField,SubmitField, SelectMultipleField, FileField, SelectField, IntegerField, \
    SelectField
from wtforms.validators import InputRequired, Email, NumberRange
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, URL
from flask_wtf import FlaskForm
from models import Student
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField

from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=50)])
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid Email'), Length(max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=80)])
    surname = StringField('Surname', validators=[InputRequired(), Length(max=50)])  # Add surname field
    name = StringField('Name', validators=[InputRequired(), Length(max=50)])  # Add name field
    is_teacher = BooleanField('Teacher')


class GroupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Create Group')
    students = SelectMultipleField('Students', coerce=int)

    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.students.choices = [(student.id, student.name) for student in Student.query.all()]

class ConfigureGroupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    # You may need to add fields for students here
    submit = SubmitField('Save Changes')

class AssignmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    due_time = TimeField('Due Time', validators=[DataRequired()])

class SubmissionForm(FlaskForm):
    notes = TextAreaField('Notes')
    file = FileField('Upload File')
    submit = SubmitField('Submit')

class SubmitGradeForm(FlaskForm):
    points = IntegerField('Points', validators=[DataRequired(), NumberRange(min=0, max=100)])  # Field for entering points
    submit = SubmitField('Submit')  # Submit button