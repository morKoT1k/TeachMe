from flask import Blueprint, flash, redirect, render_template, request, url_for, abort, get_flashed_messages
from models import Group, Student, Assignment,Submission,student_group_association, teacher_group_association
from forms import GroupForm, ConfigureGroupForm, AssignmentForm, SubmissionForm, SubmitGradeForm, LoginForm
from flask_login import current_user, login_user, logout_user
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from extensions import db
from flask import make_response
import random
import base64
import json
import io
import logging
from datetime import datetime
from extensions import bucket
from werkzeug.utils import secure_filename
import urllib.parse
from datetime import datetime


# Set up logging
logging.basicConfig(level=logging.ERROR)  # Log all errors

main = Blueprint('main', __name__)



# Route to display all groups
from flask import abort

@main.route('/groups')
def groups():
    if not current_user.is_teacher:
        abort(403)
    teacher_groups = Group.query.join(teacher_group_association).filter(teacher_group_association.c.user_id == current_user.id).all()
    return render_template('groups.html', groups=teacher_groups)


# Trasa pro vytvoření nové skupiny
@main.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if not current_user.is_teacher:
        abort(403)
    form = GroupForm()
    students = Student.query.order_by(Student.surname, Student.name).all()
  # Přivést všechny studenty
    if form.validate_on_submit():
        try:
            # Create a new Group object with the submitted data
            new_group = Group(name=form.name.data)

            # Assign teacher to the group
            current_user.hosted_groups.append(new_group)

            # Assign students to the group
            selected_student_ids = request.form.getlist('students')
            selected_students = Student.query.filter(Student.id.in_(selected_student_ids)).all()
            for student in selected_students:
                new_group.students.append(student)

            db.session.add(new_group)
            db.session.commit()
            flash('New group has been created', 'success')
            return redirect(url_for('main.groups'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the group', 'error')
            logging.error(f"An error occurred during group creation: {e}")
    return render_template('create_group.html', form=form, students=students)


@main.route('/group/<int:group_id>/configure', methods=['GET', 'POST'])
def configure_group(group_id):
    group = Group.query.get_or_404(group_id)
    if not current_user.is_teacher or current_user.id not in [teacher.id for teacher in group.teachers]:
        abort(403)

    # Check if the current user is associated with the group as a teacher
    teacher_group_ids = db.session.query(teacher_group_association.c.group_id).filter_by(user_id=current_user.id).all()
    flattened_group_ids = [group_id for (group_id,) in teacher_group_ids]
    if not group_id in flattened_group_ids:
        abort(403)

    form = GroupForm(obj=group)

    if form.validate_on_submit():
        # Update group name
        group.name = form.name.data

        # Remove all students from the group
        group.students = []

        # Add selected students to the group
        for student in Student.query.order_by(Student.surname, Student.name).all():
            if str(student.id) in request.form.getlist('students'):
                group.students.append(student)

        db.session.commit()
        flash('Group configuration updated successfully!', 'success')
        return redirect(url_for('main.group', group_id=group.id))

    # Pass all students to the template
    students = Student.query.all()
    return render_template('configure_group.html', form=form, group=group, students=students)

@main.route('/group/<int:group_id>')
@login_required
def group(group_id):
    if not current_user.is_teacher:
        abort(403)
    # Check if the current user is associated with the group as a teacher
    teacher_group_ids = db.session.query(teacher_group_association.c.group_id).filter_by(user_id=current_user.id).all()
    flattened_group_ids = [group_id for (group_id,) in teacher_group_ids]
    if not group_id in flattened_group_ids:
        abort(403)

    group = Group.query.get_or_404(group_id)
    assignments = group.assignments
    students = group.students.order_by(Student.surname, Student.name).all()
    return render_template('group.html', group=group, assignments=assignments, students=students)



# Trasa pro vytvoření úlohy
@main.route('/create_assignment/<int:group_id>', methods=['GET', 'POST'])
def create_assignment(group_id):

    group = Group.query.get_or_404(group_id)
    if not current_user.is_teacher:
        abort(403)
    # Zkontrolujte, zda je aktuální uživatel přidružen ke skupině jako učitel.
    teacher_group_ids = db.session.query(teacher_group_association.c.group_id).filter_by(user_id=current_user.id).all()
    flattened_group_ids = [group_id for (group_id,) in teacher_group_ids]
    if not group_id in flattened_group_ids:
        abort(403)
    # Vymazat všechny blikající zprávy
    get_flashed_messages(category_filter=[])
    form = AssignmentForm()

    if form.validate_on_submit():
        # Parse due_date do objektu datetime
        due_date = form.due_date.data
        due_time = form.due_time.data

        # Vytvoření nového úkolu
        assignment = Assignment(
            title=form.title.data,
            description=form.description.data,
            due_date=due_date,
            due_time=due_time,
            group_id=group_id
        )

        db.session.add(assignment)
        db.session.commit()

        flash('Assignment created successfully!', 'success')
        return redirect(url_for('main.group', group_id=group.id))
    return render_template('create_assignment.html', form=form, group=group.name, group_id = group.id)







# Route to configure an assignment
@main.route('/configure_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def configure_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    if not current_user.is_teacher or current_user.id not in [teacher.id for teacher in assignment.group.teachers]:
        abort(403)

    # Clear all flashed messages
    get_flashed_messages(category_filter=[])

    form = AssignmentForm(obj=assignment)  # Pre-fill the form with assignment data

    if form.validate_on_submit():
        form.populate_obj(assignment)  # Update assignment with form data
        db.session.commit()
        return redirect(url_for('main.assignment_details', assignment_id=assignment.id))

    return render_template('configure_assignment.html', form=form, assignment=assignment)


from flask import request, redirect, url_for


@main.route('/delete_assignment/<int:assignment_id>')
def delete_assignment(assignment_id):
    if not current_user.is_teacher:
        abort(403)

    # Retrieve the assignment from the database
    assignment = Assignment.query.get_or_404(assignment_id)

    # Retrieve submissions associated with the assignment
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()

    # Delete files from Firebase storage associated with each submission
    for submission in submissions:
        blob = bucket.blob(submission.document_link)
        blob.delete()

    # Perform the deletion operation for the assignment
    db.session.delete(assignment)
    db.session.commit()

    flash('Assignment deleted successfully!', 'success')

    # Redirect to the group page
    return redirect(url_for('main.group', group_id=assignment.group_id))


@main.route('/delete_group/<int:group_id>')
def delete_group(group_id):
    if not current_user.is_teacher:
        abort(403)

    # Retrieve the group from the database
    group = Group.query.get_or_404(group_id)

    # Retrieve all assignments associated with the group
    assignments = Assignment.query.filter_by(group_id=group_id).all()

    # Update or delete assignments
    for assignment in assignments:
        # Update or delete submissions associated with the assignment
        submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
        for submission in submissions:
            try:
                blob = bucket.blob(submission.document_link)
                blob.delete()
            except Exception as e:
                print(f"Error deleting document: {e}")
        db.session.delete(assignment)

    # Perform the deletion operation for the group
    db.session.delete(group)
    db.session.commit()

    flash('Group deleted successfully!', 'success')

    # Redirect to the groups page
    return redirect(url_for('main.groups'))






@main.route('/assignment/<int:assignment_id>', methods=['GET'])
def assignment_details(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    if not current_user.is_teacher or current_user.id not in [teacher.id for teacher in assignment.group.teachers]:
        abort(403)
    group = assignment.group

    # Get all students associated with the assignment's group
    students = group.students

    # Get submissions for the assignment
    submissions = Submission.query.filter_by(assignment_id=assignment.id)

    # Create a dictionary to store submission details for each student
    student_submissions = {}

    # Iterate over all students
    for student in students:
        # Check if there is a submission for the student and assignment
        submission = submissions.filter_by(student_id=student.id).first()

        if submission:
            # If submission exists, store submission details
            student_submissions[student.id] = {
                'name': student.name,
                'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                'document_link': submission.document_link,
                'notes': submission.notes,
                'points': submission.points,
                'id':submission.id
            }
        else:
            # If no submission exists, store null values
            student_submissions[student.id] = {
                'name': student.name,
                'submitted_at': None,
                'document_link': None,
                'notes': None,
                'points': None
            }

    return render_template('assignment_details.html', assignment=assignment, student_submissions=student_submissions, group_id = group.id)


@main.route('/assignments')
def assignments():
    if current_user.is_teacher:
        abort(403)

    # Initialize variables
    submitted = []
    not_submitted = []
    overdue = []
    student_submissions = []

    # Get the current user's ID and name
    current_user_name = current_user.username
    # Query the student based on the current user's name
    student = Student.query.filter_by(username=current_user_name).first()
    # Get the student's ID
    if student:
        student_id = student.id

        # Query for all group IDs associated with the student
        student_group_ids = db.session.query(student_group_association.c.group_id).filter_by(
            student_id=student_id).all()
        # Flatten the list of group IDs

        flattened_group_ids = [group_id for (group_id,) in student_group_ids]
        # Query assignments associated with the student's groups

        student_assignments = Assignment.query.filter(Assignment.group_id.in_(flattened_group_ids)).all()
        # Query submissions associated with the student

        student_submissions = Submission.query.filter_by(student_id=student_id).all()
        # Get current datetime

        now = datetime.now()
        # Separate assignments into submitted, not submitted, and overdue

        for assignment in student_assignments:
            # Check if there's a submission for the current assignment by the current student
            submission = Submission.query.filter_by(assignment_id=assignment.id, student_id=student_id).first()
            if submission:
                submitted.append((assignment, submission.points))  # Append a tuple of assignment and points
            else:
                not_submitted.append(assignment)
                # Convert due_date to datetime if it's a date object
                due_datetime = datetime.combine(assignment.due_date, datetime.min.time())
                if due_datetime < now:
                    overdue.append(assignment)

    return render_template('assignments.html', submitted=submitted, not_submitted=not_submitted, overdue=overdue,
                           student_submissions=student_submissions, student_id=student_id)



@main.route('/submit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def submit_assignment(assignment_id):
    if current_user.is_teacher:
        abort(403)
    form = SubmissionForm()
    assignment = Assignment.query.get_or_404(assignment_id)

    submission = Submission.query.filter_by(student_id=current_user.id, assignment_id=assignment_id).first()
    current_user_name = current_user.username

    # Query the student based on the current user's name
    student = Student.query.filter_by(username=current_user_name).first()

    if submission:
        form.notes.data = submission.notes
        # Pre-fill file field with filename if it exists
        if submission.document_link:
            form.file.data = submission.document_link

    if form.validate_on_submit():
        # Save the file to Firebase Storage
        file = form.file.data
        if file:
            filename = secure_filename(file.filename)
            blob = bucket.blob(filename)
            blob.upload_from_string(file.read(), content_type=file.content_type)
            file_path = blob.name  # Get the path to the object in the blob

            # Create or update submission in the database
            if submission:
                submission.notes = form.notes.data
                submission.document_link = file_path  # Update document_path with the file path
            else:
                submission = Submission(
                    notes=form.notes.data,
                    document_link=file_path,  # Save the file path
                    student_id=student.id,
                    assignment_id=assignment_id
                )
                db.session.add(submission)
            db.session.commit()

            flash('Assignment submitted successfully!', 'success')
            return redirect(url_for('main.assignments'))
        else:
            flash('No file selected!', 'error')

    return render_template('submit_assignment.html', form=form, assignment=assignment, submission=submission)

@main.route('/configure_submission/<int:assignment_id>/<int:student_id>', methods=['GET', 'POST'])
def configure_submission(assignment_id, student_id):
    if current_user.is_teacher:
        abort(403)

    # Query the submission based on the provided assignment and student IDs
    submission = Submission.query.filter_by(assignment_id=assignment_id, student_id=student_id).first_or_404()

    # Create a form and populate it with the submission data
    form = SubmissionForm(obj=submission)

    if form.validate_on_submit():
        form.populate_obj(submission)
        db.session.commit()
        flash('Submission updated successfully!', 'success')
        return redirect(url_for('main.assignments'))

    return render_template('configure_submission.html', form=form, submission=submission)





@main.route('/submission/<int:submission_id>', methods=['GET', 'POST'])
def submission_details(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    form = SubmitGradeForm()
    assignment_id = submission.assignment.id
    assignment = submission.assignment
    if not current_user.is_teacher or current_user.id not in [teacher.id for teacher in assignment.group.teachers]:
        abort(403)
    if form.validate_on_submit():
        submission.points = form.points.data
        db.session.commit()
        return redirect(url_for('main.assignment_details', assignment_id=assignment_id))

    # Pre-fill the form with submission's points if they exist
    if submission.points is not None:
        form.points.data = submission.points

    return render_template('submission_details.html', submission=submission, form=form, assignment_id=assignment_id)




@main.route('/download_submission/<int:submission_id>', methods=['GET'])
def download_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    # Get the blob object using the file path saved in the submission
    blob = bucket.blob(submission.document_link)

    # Add logging to track the document link being used
    logging.info(f"Attempting to download file from Firebase Storage with document link: {submission.document_link}")

    # Download the file from Firebase Storage
    try:
        file_content = blob.download_as_string()
        response = make_response(file_content)

        # Set the appropriate content type and attachment disposition
        response.headers['Content-Type'] = blob.content_type
        response.headers['Content-Disposition'] = f'attachment; filename="{blob.name}"'

        # Add logging for successful download
        logging.info(f"File downloaded successfully from Firebase Storage: {submission.document_link}")

        return response
    except Exception as e:
        # Log the error
        logging.error(f"Error downloading file: {e}")

        # Handle errors or file not found
        flash('Error downloading file. Please try again later.', 'error')

