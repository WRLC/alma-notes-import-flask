from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired


# Add/Edit User Form
class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    displayname = StringField('Display Name', validators=[DataRequired()])
    emailaddress = StringField('Email', validators=[DataRequired()])
    admin = BooleanField('Admin')
