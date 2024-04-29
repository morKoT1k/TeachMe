from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from datetime import datetime
from extensions import db

# Association table for the many-to-many relationship between User and Group
teacher_group_association = db.Table('teacher_group_association',
                                     db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                                     db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
                                     )

student_group_association = db.Table('student_group_association',
                                     db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
                                     db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
                                     )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True)
    hashed_password = db.Column(db.String(120))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    registered = db.Column(db.Boolean)
    is_teacher = db.Column(db.Boolean, default=False)

    # Definice vztahu ke skupinám se vztahem many-to-many
    hosted_groups = db.relationship('Group', secondary=teacher_group_association,
                                    backref=db.backref('teachers', lazy='dynamic'))

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    surname = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(15), nullable=False)
    groups = db.relationship('Group', secondary=student_group_association,
                             backref=db.backref('students', lazy='dynamic'))


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    due_time = db.Column(db.Time, nullable=False)
    group = db.relationship('Group', backref=db.backref('assignments', lazy=True))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id', ondelete='CASCADE'), nullable=False)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notes = db.Column(db.Text)
    document_link = db.Column(db.String(255))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)  # Add points field
    student = db.relationship('Student', backref=db.backref('submissions', lazy=True))
    assignment = db.relationship('Assignment',
                                 backref=db.backref('submissions', lazy=True, cascade='all, delete-orphan'))
