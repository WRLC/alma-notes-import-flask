from app.extensions import db
from datetime import datetime


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

    # Log the user into the app
    @staticmethod
    def user_login(session, user_data):
        # Assemble to user's display name
        user_data['DisplayName'] = ''  # Initialize the display name
        if 'GivenName' in user_data:  # if the user has a first name...
            user_data['DisplayName'] += user_data['GivenName'] + ' '  # ...set the first name
        if 'Name' in user_data:
            user_data['DisplayName'] += user_data['Name']

        # Set the session variables
        session['username'] = user_data['UserName']  # Set the username
        session['display_name'] = user_data['DisplayName']  # Set the user's display name
        session['email'] = user_data['Email']  # Set the user's email
        session['authorizations'] = []  # Initialize the user's authorizations

        user = User.check_user(session['username'])  # Check if the user exists in the database

        # If the user is in the database...
        if user is not None:
            User.set_email(user, session)  # ...set the user's email address
            if user.admin:  # ...if the user is an admin...
                session['authorizations'].append('admin')  # ...set the user's authorizations to ['admin']

        # If the user isn't in the database...
        else:
            User.add_user(session)  # ...add the user to the database

    # Check if the user exists in the database
    @staticmethod
    def check_user(username):
        user = db.session.execute(db.select(User).filter(User.username == username)).scalar_one_or_none()
        return user

    # Set the user's email address
    @staticmethod
    def set_email(user, session):
        user.emailaddress = session['email']
        db.session.commit()

    # Set the last login time for the user
    @staticmethod
    def set_last_login(user):
        user.last_login = datetime.now()  # Set the last login time to the current time
        db.session.commit()  # Commit the changes

    # Add the user to the database
    @staticmethod
    def add_user(session, ):

        # Create the user object
        user = User(
            username=session['username'],
            displayname=session['display_name'],
            emailaddress=session['email'],
            last_login=datetime.now()
        )
        db.session.add(user)  # Add the user to the database
        db.session.commit()  # Commit the changes

    # Get the users
    @staticmethod
    def get_users():
        users = db.session.execute(db.select(
            User.id,
            User.username,
            User.displayname,
            User.emailaddress,
            User.last_login,
            User.admin
        ).order_by(User.username)).mappings().all()
        return users

    # Update the user
    @staticmethod
    def update_user(userid, username, displayname, emailaddress, admin):
        user = db.session.execute(db.select(User).filter(User.id == userid)).scalar_one_or_none()
        user.username = username
        user.displayname = displayname
        user.emailaddress = emailaddress
        user.admin = admin
        db.session.commit()
