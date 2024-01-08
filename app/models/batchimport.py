from app.extensions import db
from datetime import datetime
from app.models.user import User
from app.models.institution import Institution


# BatchImport model
class BatchImport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    field = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    user = db.Column(db.String(255), nullable=False)
    institution = db.Column(db.String(255), db.ForeignKey('institution.code'), nullable=False)

    def __repr__(self):
        return '<BatchImport %r>' % self.uuid

    # Add the batch import to the database
    @staticmethod
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

    # Get the batch imports
    @staticmethod
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
