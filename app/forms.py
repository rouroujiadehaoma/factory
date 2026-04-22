"""WTForms for hazardous waste workflows."""
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from config import Config


class LoginForm(FlaskForm):
    username = StringField('Username or email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField(
        'Role',
        choices=[
            (Config.ROLE_OPERATOR, 'Operator — register batches & transfers'),
            (Config.ROLE_ES_OFFICER, 'Environmental safety officer — compliance & alerts'),
            (Config.ROLE_AUDITOR, 'Auditor — read-only, audit log & exports'),
        ],
        validators=[DataRequired()],
        description='Administrator accounts cannot be self-registered; an existing admin must create them.',
    )
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    invite_code = StringField(
        'Team invite code',
        validators=[Optional(), Length(max=80)],
        description='Required for Environmental safety officer and Auditor. Leave empty for Operator. Ask your course team for the code.',
    )
    submit = SubmitField('Register')

    def validate_invite_code(self, field):
        role = self.role.data
        code = (field.data or '').strip()
        if role == Config.ROLE_OPERATOR:
            if code:
                raise ValidationError('Leave invite code empty when registering as an operator.')
        elif role == Config.ROLE_ES_OFFICER:
            if code != Config.REGISTRATION_INVITE_ES:
                raise ValidationError('Enter the valid invite code for environmental safety officer registration.')
        elif role == Config.ROLE_AUDITOR:
            if code != Config.REGISTRATION_INVITE_AUDITOR:
                raise ValidationError('Enter the valid invite code for auditor registration.')


class WasteBatchForm(FlaskForm):
    name = StringField('Waste name', validators=[DataRequired(), Length(max=200)])
    category = StringField('Category', validators=[DataRequired(), Length(max=100)])
    source_unit = StringField('Source unit / workshop', validators=[DataRequired(), Length(max=120)])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    unit = SelectField(
        'Unit',
        choices=[('kg', 'kg'), ('L', 'L'), ('ton', 'ton'), ('pcs', 'pcs')],
        validators=[DataRequired()],
    )
    storage_location = StringField('Storage location', validators=[DataRequired(), Length(max=120)])
    hazard_level = SelectField(
        'Hazard level',
        choices=[(h, h) for h in Config.HAZARD_LEVELS],
        validators=[DataRequired()],
    )
    responsible_person = StringField('Responsible person', validators=[DataRequired(), Length(max=120)])
    remarks = TextAreaField('Remarks', validators=[Optional(), Length(max=4000)])
    is_abnormal = BooleanField('Mark as abnormal')
    external_disposal_info = TextAreaField('External disposal / manifest notes', validators=[Optional()])
    submit = SubmitField('Save')


class WasteBatchEditForm(WasteBatchForm):
    """Same as create; used when editing allowed fields (not status)."""

    submit = SubmitField('Update')


class StatusTransitionForm(FlaskForm):
    to_status = SelectField('Next status', choices=[], validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Advance status')


class TransferForm(FlaskForm):
    transfer_vendor = StringField('Vendor / carrier', validators=[DataRequired(), Length(max=200)])
    destination = StringField('Destination', validators=[Optional(), Length(max=300)])
    manifest_number = StringField('Manifest number', validators=[Optional(), Length(max=120)])
    submit = SubmitField('Record transfer')


class UserAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField(
        'Role',
        choices=[(r, r) for r in Config.ROLES],
        validators=[DataRequired()],
    )
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create user')


class AlertRuleForm(FlaskForm):
    rule_name = StringField('Rule name', validators=[DataRequired(), Length(max=120)])
    rule_type = SelectField(
        'Type',
        choices=[
            ('storage_exceeds_days', 'Days in storage / early statuses'),
            ('hazard_minimum_level', 'Minimum hazard level (threshold = low|medium|high|critical)'),
            ('remark_keyword', 'Remark keywords (comma-separated)'),
            ('location_capacity', 'Location aggregate quantity (kg)'),
            ('inactive_batch_days', 'Inactive days while registered/stored'),
        ],
        validators=[DataRequired()],
    )
    threshold = StringField('Threshold', validators=[DataRequired(), Length(max=255)])
    severity = SelectField(
        'Severity',
        choices=[('info', 'info'), ('warning', 'warning'), ('critical', 'critical')],
        validators=[DataRequired()],
    )
    enabled = BooleanField('Enabled', default=True)
    submit = SubmitField('Save rule')


class AlertResolveForm(FlaskForm):
    resolution_note = TextAreaField('Resolution notes', validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField('Mark resolved')


class AuditFilterForm(FlaskForm):
    class Meta:
        csrf = False

    actor = StringField('User contains', validators=[Optional()])
    entity_type = StringField('Entity type', validators=[Optional()])
    batch_id = StringField('Entity id', validators=[Optional()])
    submit = SubmitField('Filter')


class RunAlertEvalForm(FlaskForm):
    submit = SubmitField('Run evaluation')
