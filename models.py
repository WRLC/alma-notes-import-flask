from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()  # Create a database object


##################
# Object Classes #
##################

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    displayname = db.Column(db.String(255), nullable=False)
    emailaddress = db.Column(db.String(255), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return '<User %r>' % self.username


# Institution model
class Institution(db.Model):
    code = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    apikey = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Institution %r>' % self.code


# BatchImport model
class BatchImport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    field = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    user = db.Column(db.String(255), nullable=False)
    institution = db.Column(db.String(255), db.ForeignKey('institution.code'), nullable=False)


####################
# Helper functions #
####################

# Log the user into the application
def user_login(session, user_data):

    # Set the session variables
    session['username'] = user_data['primary_id']  # Set the username
    session['display_name'] = user_data['full_name']  # Set the user's display name
    session['authorizations'] = user_data['authorizations']  # Set the user's authorizations
    session['email'] = user_data['email']  # Set the user's email

    user = check_user(session['username'])  # Check if the user exists in the database

    # If the user is in the database...
    if user is not None:
        set_email(user, session)  # ...set the user's email address
        if user.admin:  # ...if the user is an admin...
            session['authorizations'].append('admin')  # ...set the user's authorizations to ['admin']
        if 'exceptions' in session['authorizations']:
            set_last_login(user)  # ...set the last login time for the user

    # If the user isn't in the database...
    else:
        add_user(session)  # ...add the user to the database


# Check if the user exists in the database
def check_user(username):
    user = db.session.execute(db.select(User).filter(User.username == username)).scalar_one_or_none()
    return user


# Set the user's email address
def set_email(user, session):
    user.emailaddress = session['email']
    db.session.commit()


# Set the last login time for the user
def set_last_login(user):
    user.last_login = datetime.now()  # Set the last login time to the current time
    db.session.commit()  # Commit the changes


# Add the user to the database
def add_user(session,):

    # Create the user object
    user = User(
        username=session['username'],
        displayname=session['display_name'],
        emailaddress=session['email'],
        last_login=datetime.now()
    )
    db.session.add(user)  # Add the user to the database
    db.session.commit()  # Commit the changes


def add_batch_import(uuid, filename, field, user, institution):
    batch_import = BatchImport(
        uuid=uuid,
        filename=filename,
        field=field,
        date=datetime.now(),
        user=user,
        institution=institution
    )
    db.session.add(batch_import)  # Add the batch import to the database
    db.session.commit()  # Commit the changes


def get_batch_imports():
    batch_imports = db.session.execute(
        db.select(
            BatchImport.uuid,
            BatchImport.filename,
            BatchImport.field,
            BatchImport.date,
            User.displayname,
            Institution.name
        ).join(
            User, BatchImport.user == User.id
        ).join(
            Institution, BatchImport.institution == Institution.code
        ).order_by(
            BatchImport.date.desc()
        )
    ).mappings().all()
    return batch_imports


def get_institutions():
    institutions = db.session.execute(db.select(
        Institution.code,
        Institution.name,
        Institution.apikey
    ).order_by(Institution.name)).mappings().all()
    return institutions


def get_single_institution(code):
    institution = db.session.execute(db.select(Institution).filter(Institution.code == code)).scalar_one_or_none()
    return institution


def addinstitution(code, name, apikey):
    institution = Institution(
        code=code,
        name=name,
        apikey=apikey
    )
    db.session.add(institution)  # Add the institution to the database
    db.session.commit()  # Commit the changes
