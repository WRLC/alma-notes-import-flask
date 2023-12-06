from flask import Flask, render_template, flash, session, url_for
from forms import UploadForm
from werkzeug.utils import secure_filename
from batch import batch
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'


@app.route('/', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        # File
        file = form.csv.data  # Get the CSV file from the form
        filename = secure_filename(file.filename)  # Make the filename safe, even though it should be safe already
        file.save(os.path.join(  # Save the file to the CSV folder in the instance path
            app.instance_path, 'static/csv', filename
        ))

        # Field
        field = form.almafield.data  # Get the Alma field from the form

        # Run the batch function on the CSV file
        batch(os.path.join(
            app.instance_path, 'static/csv', filename
        ), field)

        # Provide import info as message to user
        flash(
            'The CSV is being processed. An email will be sent when complete.',
            'info'
        )

        return url_for('upload')  # Redirect to the upload page

    return render_template('upload.html', form=form)


if __name__ == '__main__':
    app.run()
