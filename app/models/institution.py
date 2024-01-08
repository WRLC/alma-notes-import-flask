from app.extensions import db


# Institution model
class Institution(db.Model):
    code = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    apikey = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Institution %r>' % self.code

    # Get the institutions
    @staticmethod
    def get_institutions():
        institutions = db.session.execute(db.select(
            Institution.code,
            Institution.name,
            Institution.apikey
        ).order_by(Institution.name)).mappings().all()
        return institutions

    # Get a single institution
    @staticmethod
    def get_single_institution(code):
        institution = db.session.execute(db.select(Institution).filter(Institution.code == code)).scalar_one_or_none()
        return institution

    # Add the institution to the database
    @staticmethod
    def addinstitution(code, name, apikey):
        institution = Institution(
            code=code,
            name=name,
            apikey=apikey
        )
        db.session.add(institution)  # Add the institution to the database
        db.session.commit()  # Commit the changes

    # Update the institution in the database
    @staticmethod
    def updateinstitution(code, name, apikey):
        institution = Institution.get_single_institution(code)
        institution.name = name
        institution.apikey = apikey
        db.session.commit()  # Commit the changes
