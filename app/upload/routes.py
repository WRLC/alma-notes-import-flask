from flask import render_template, flash, redirect, url_for, session, current_app, request, abort
import app.forms.uploadform as uploadform
import app.forms.institutionform as institutionform
import app.forms.userform as userform
from functools import wraps
from werkzeug.utils import secure_filename
from app.tasks.batch import batch
from celery.result import AsyncResult
import os
import jwt
from app.models.user import User
from app.models.institution import Institution
from app.models.batchimport import BatchImport
from app.upload import bp


# decorator for pages that need auth
def auth_required(f):
    @wraps(f)  # preserve the original function's metadata
    def decorated(*args, **kwargs):  # the wrapper function
        if 'username' not in session:  # if the user is not logged in
            return redirect(url_for('upload.login'))  # redirect to the login page
        else:
            return f(*args, **kwargs)  # otherwise, call the original function

    return decorated


@bp.route('/', methods=['GET', 'POST'])
@auth_required
def upload():
    if 'almanotesimport' not in session['authorizations']:
        abort(403)
    form = uploadform.UploadForm()
    izs = Institution.get_institutions()  # Get the institutions from the database
    form.iz.choices = [(i.code, i.name) for i in izs]  # Set the choices for the institution field
    if form.validate_on_submit():
        # File
        file = form.csv.data  # Get the CSV file from the form
        filename = secure_filename(file.filename)  # Get the filename from the file

        # If the filename already exists in the upload folder...
        if os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], filename)):
            name, ext = os.path.splitext(file.filename)  # ...get the filename and extension
            count = 0  # ...initialize filecount
            # ...while the filename and filecount exists...
            while os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], name) + '-{}'.format(count) + ext):
                count += 1  # ...increment the filecount until the filename doesn't exist
            filename = name + '-{}'.format(count) + ext  # ...add the new filecount to the filename

        secfilename = secure_filename(filename)  # Make the filename safe, even though it should be safe already

        # Save the file to the CSV folder in the instance path
        file.save(os.path.join(
            current_app.config['UPLOAD_FOLDER'], secfilename
        ))

        # Field
        field = form.almafield.data  # Get the Alma field from the form

        iz = form.iz.data  # Get the institution from the form
        apikey = Institution.get_single_institution(iz).apikey  # Get the API key for the institution

        user = User.check_user(session['username'])  # Get the current user object

        # Run the batch function on the CSV file
        task = batch.delay(
            os.path.join(
                current_app.config['UPLOAD_FOLDER'], secfilename
            ), field, user.emailaddress, apikey
        )

        # Add task to database
        BatchImport.add_batch_import(task.id, filename, field, user.id, iz)

        # Provide import info as message to user
        flash(
            'The CSV "' + filename + '" is being processed (taskid = ' + str(
                task.id) + '). An email will be sent to {} when complete.'.format(session['email']),
            'info'
        )
        return redirect(url_for('upload.upload'))

    # Get batch imports from database
    batch_imports = BatchImport.get_batch_imports()  # Get the batch imports from the database
    imports = []  # Initialize the imports list
    for batch_import in batch_imports:  # Iterate through the batch imports
        status = AsyncResult(batch_import.uuid).status  # Get the status of the task
        result = AsyncResult(batch_import.uuid).result  # Get the result of the task
        imports.append({  # Add the batch import to the imports list with the status and result
            'filename': batch_import.filename,
            'field': batch_import.field,
            'date': batch_import.date,
            'user': batch_import.displayname,
            'institution': batch_import.name,
            'status': status,
            'result': result
        })
    return render_template('upload.html', form=form, imports=imports, uploadfolder=current_app.config['UPLOAD_FOLDER'])


@bp.route('/login')
def login():
    if 'username' in session:
        return redirect(url_for('upload.upload'))
    else:
        login_url = current_app.config['SAML_SP']
        login_url += current_app.config['COOKIE_ISSUING_FILE']
        login_url += '?institution='
        login_url += current_app.config['INSTITUTION_CODE']
        login_url += '&url='
        login_url += current_app.config['SITE_URL']
        login_url += '/login/n'
        return render_template('login.html', login_url=login_url)


@bp.route('/login/n')
def new_login():
    session.clear()
    if 'wrt' in request.cookies:  # if the login cookie is present
        encoded_token = request.cookies['wrt']  # get the login cookie
        user_data = jwt.decode(encoded_token, current_app.config['SHARED_SECRET'], algorithms=['HS256'])  # decode token
        User.user_login(session, user_data)  # Log the user in

        if 'almanotesimport' in session['authorizations']:  # if the user is an exceptions user
            return redirect(url_for('upload.upload'))  # redirect to the home page
        else:
            abort(403)  # otherwise, abort with a 403 error
    else:
        return "no login cookie"  # if the login cookie is not present, return an error


# Logout handler
@bp.route('/logout')
@auth_required
def logout():
    session.clear()  # clear the session
    return redirect(url_for('upload.upload'))  # redirect to the home page


# Institutions handler
@bp.route('/institutions')
@auth_required
def institutions():
    if 'admin' not in session['authorizations']:
        abort(403)
    izs = Institution.get_institutions()
    return render_template('institutions.html', izs=izs)


# Institution handler
@bp.route('/institutions/<code>', methods=['GET', 'POST'])
@auth_required
def edit_institution(code):
    if 'admin' not in session['authorizations']:
        abort(403)
    iz = Institution.query.get_or_404(code)
    form = institutionform.InstitutionForm(obj=iz)
    if form.validate_on_submit():
        Institution.updateinstitution(form.code.data, form.name.data, form.apikey.data)
        flash(form.name.data + ' updated', 'info')
        return redirect(url_for('upload.institutions'))
    return render_template('edit_institution.html', form=form)


# Add institution handler
@bp.route('/institutions/add', methods=['GET', 'POST'])
@auth_required
def add_institution():
    if 'admin' not in session['authorizations']:
        abort(403)
    form = institutionform.InstitutionForm()
    if form.validate_on_submit():
        Institution.addinstitution(form.code.data, form.name.data, form.apikey.data)
        flash('Institution added', 'info')
        return redirect(url_for('upload.institutions'))
    return render_template('add_institution.html', form=form)


# Users handler
@bp.route('/users')
@auth_required
def users():
    if 'admin' not in session['authorizations']:
        abort(403)
    allusers = User.get_users()
    return render_template('users.html', allusers=allusers)


# Edit User handler
@bp.route('/users/<userid>', methods=['GET', 'POST'])
@auth_required
def edit_user(userid):
    if 'admin' not in session['authorizations']:
        abort(403)
    edituser = User.query.get_or_404(userid)
    form = userform.UserForm(obj=edituser)
    if form.validate_on_submit():
        User.updateuser(edituser.id, form.username.data, form.displayname.data, form.emailaddress.data,
                        form.admin.data)
        flash(edituser.displayname + ' updated', 'info')
        return redirect(url_for('upload.users'))
    return render_template('edit_user.html', form=form)


# set up error handlers & templates for HTTP codes used in abort()
#   see http://flask.pocoo.org/docs/1.0/patterns/errorpages/
# 400 error handler
@bp.errorhandler(400)
def badrequest(e):
    return render_template('error_400.html', e=e), 400  # render the error template


# 403 error handler
@bp.errorhandler(403)
def forbidden(e):
    return render_template('unauthorized.html', e=e), 403  # render the error template


# 500 error handler
@bp.errorhandler(500)
def internalerror(e):
    return render_template('error_500.html', e=e), 500  # render the error template
