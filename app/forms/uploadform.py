from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField
from wtforms.validators import DataRequired


# Upload Form
class UploadForm(FlaskForm):
    iz = SelectField('Alma IZ', coerce=str, validators=[DataRequired()])
    csv = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv',], 'CSV files only!')
    ])
    almafield = SelectField('Alma Field', choices=[
        'pid',
        'barcode',
        'policy',
        'provenance',
        'description',
        'library',
        'location',
        'pages',
        'pieces',
        'requested',
        'creation_date',
        'modification_date',
        'base_status',
        'awaiting_reshelving',
        'physical_material_type',
        'po_line',
        'is_magnetic',
        'arrival_date',
        'year_of_issue',
        'enumeration_a',
        'enumeration_b',
        'enumeration_c',
        'enumeration_d',
        'enumeration_e',
        'enumeration_f',
        'enumeration_g',
        'enumeration_h',
        'chronology_i',
        'chronology_j',
        'chronology_k',
        'chronology_l',
        'chronology_m',
        'break_indicator',
        'pattern_type',
        'linking_number',
        'type_of_unit',
        'receiving_operator',
        'process_type',
        'inventory_number',
        'inventory_price',
        'alternative_call_number',
        'alternative_call_number_type',
        'storage_location_id',
        'public_note',
        'fulfillment_note',
        'internal_note_1',
        'internal_note_2',
        'internal_note_3',
        'statistics_note_1',
        'statistics_note_2',
        'statistics_note_3',
        'physical_condition',
        'committed_to_retain',
        'retention_reason',
        'retention_note'
    ], default='internal_note_1', validators=[DataRequired()])
