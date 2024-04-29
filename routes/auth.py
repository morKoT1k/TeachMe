import logging
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user, current_user
from forms import LoginForm, RegisterForm
from datetime import datetime
from sqlalchemy import or_
from extensions import db
from models import User, Student

auth = Blueprint('auth', __name__)
import re


# Set up logging
logging.basicConfig(level=logging.ERROR)  # Log all errors


# Define a mapping of characters to their normalized versions
CHARACTER_MAPPING = {
    'á': 'a', 'Á': 'a',
    'č': 'c', 'Č': 'c',
    'ď': 'd', 'Ď': 'd',
    'é': 'e', 'É': 'e',
    'ě': 'e', 'Ě': 'e',
    'í': 'i', 'Í': 'i',
    'ň': 'n', 'Ň': 'n',
    'ó': 'o', 'Ó': 'o',
    'ř': 'r', 'Ř': 'r',
    'š': 's', 'Š': 's',
    'ť': 't', 'Ť': 't',
    'ú': 'u', 'Ú': 'u',
    'ů': 'u', 'Ů': 'u',
    'ý': 'y', 'Ý': 'y',
    'ž': 'z', 'Ž': 'z'
}

def normalize_text(text):
    # Replace special characters with their normalized versions (case insensitive)
    for char, replacement in CHARACTER_MAPPING.items():
        text = re.sub(f'[{char}]', replacement, text)
    return text.lower()
def generate_username(surname):
    normalized_surname = normalize_text(surname)[:4]
    base_username = f"{normalized_surname}00"
    counter = 0
    new_username = base_username
    while User.query.filter_by(username=new_username).first():
        new_username = f"{base_username[:-2]}{counter:02}"
        counter += 1
    return new_username




@auth.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_teacher:
            return redirect(url_for('main.groups'))
        else:
            return redirect(url_for('main.assignments'))
    # Instantiate LoginForm
    form = LoginForm()

    if form.validate_on_submit():
        try:
            # Check if the user entered a valid username or email
            user = User.query.filter(or_(User.username == form.username.data,
                                          User.email == form.username.data)).first()

            if user and user.check_password(form.password.data):
                # Log in the user and update their last login time
                login_user(user, remember=form.remember.data)
                user.last_login = datetime.utcnow()
                db.session.commit()

                # Redirect based on user type
                if current_user.is_teacher:
                    return redirect(url_for('main.groups'))
                else:
                    return redirect(url_for('main.assignments'))

            # Flash an error message if the username or password is invalid
            flash('Invalid username or password', 'error')
        except Exception as e:
            # Log any exceptions
            logging.error(f"An error occurred during login: {e}")
            flash('An error occurred. Please try again later.', 'error')

    # Render the index page with the LoginForm
    return render_template('index.html', form=form)
@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Instantiate LoginForm
    form = LoginForm()

    if form.validate_on_submit():
        try:
            # Check if the user entered a valid username or email
            user = User.query.filter(or_(User.username == form.username.data,
                                          User.email == form.username.data)).first()

            if user and user.check_password(form.password.data):
                # Log in the user and update their last login time
                login_user(user, remember=form.remember.data)
                user.last_login = datetime.utcnow()
                db.session.commit()

                # Redirect based on user type
                if current_user.is_teacher:
                    return redirect(url_for('main.groups'))
                else:
                    return redirect(url_for('main.assignments'))

            # Flash an error message if the username or password is invalid
            flash('Invalid username or password', 'error')
        except Exception as e:
            # Log any exceptions
            logging.error(f"An error occurred during login: {e}")
            flash('An error occurred. Please try again later.', 'error')

    # Render the login page with the LoginForm
    return render_template('login.html', form=form)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    # Instantiate RegisterForm
    form = RegisterForm()

    # Check if the 'filled' argument is in the request
    filled = request.args.get('filled', False)

    if form.validate_on_submit():
        try:
            # Validate name and surname for Czech or Latin letters
            if not re.match(r'^[a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\s]+$', form.surname.data):
                raise ValueError('Surname must contain only Czech or Latin letters')
            if not re.match(r'^[a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\s]+$', form.name.data):
                raise ValueError('Name must contain only Czech or Latin letters')

            # Create a new User object with the submitted data
            new_user = User(
                surname=form.surname.data,
                name=form.name.data,
                email=form.email.data,
                registered=True,
                username=generate_username(form.surname.data)
            )
            new_user.set_password(form.password.data)

            # Check if the user is a teacher
            if form.is_teacher.data:
                new_user.is_teacher = True
            else:
                # If not a teacher, create a new student
                new_student = Student(
                    username=new_user.username,
                    surname=new_user.surname,
                    name=new_user.name
                )
                db.session.add(new_student)

            db.session.add(new_user)
            db.session.commit()
            # Flash a success message if the new user was created successfully
            flash('New user has been created', 'success')
            return redirect(url_for('auth.index'))
        except ValueError as e:
            # Flash an error message if the input contains invalid characters
            flash(str(e), 'error')
        except Exception as e:
            # Log any exceptions
            logging.error(f"An error occurred during signup: {e}")
            # Roll back the session and flash an error message if the username or email already exists
            db.session.rollback()
            flash('Mail or Username already exists', 'error')

    # Render the signup page with the RegisterForm and 'filled' argument
    return render_template('signup.html', form=form, filled=filled)


@auth.route('/logout')
@login_required
def logout():
    # Log out the user and redirect to the main index page
    logout_user()
    return redirect(url_for('auth.index'))
