from flask import Flask, render_template
from forms import UploadForm

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'


@app.route('/', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        # Save the file somewhere
        return form.csv.data.filename
    return render_template('upload.html', form=form)


if __name__ == '__main__':
    app.run()
