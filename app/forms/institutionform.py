from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


# Add/Edit Institution Form
class InstitutionForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    code = StringField('Code', validators=[DataRequired()])
    apikey = StringField('API Key', validators=[DataRequired()])