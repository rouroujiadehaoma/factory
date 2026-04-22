"""Waste batch CRUD, lifecycle transitions, QR payload."""
import io
from datetime import datetime

import qrcode
from flask import (
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.forms import StatusTransitionForm, TransferForm, WasteBatchEditForm, WasteBatchForm
from app.models import AuditLog, TransferRecord, WasteBatch, WasteStatusHistory
from app.utils.audit_service import log_action
from app.utils.batch_util import next_batch_code
from app.utils.rbac import roles_required
from app.utils.state_machine import can_transition, next_statuses
from config import Config


def register_routes(app):
    mutators = (
        Config.ROLE_ADMINISTRATOR,
        Config.ROLE_ES_OFFICER,
        Config.ROLE_OPERATOR,
    )
    viewers = mutators + (Config.ROLE_AUDITOR,)

    @app.route('/batches')
    @login_required
    @roles_required(*viewers)
    def batch_list():
        page = request.args.get('page', 1, type=int)
        q = WasteBatch.query.order_by(WasteBatch.created_at.desc())
        pagination = q.paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
        return render_template('batches/list.html', pagination=pagination)

    @app.route('/batches/new', methods=['GET', 'POST'])
    @login_required
    @roles_required(*mutators)
    def batch_new():
        form = WasteBatchForm()
        if form.validate_on_submit():
            code = next_batch_code()
            batch = WasteBatch(
                batch_code=code,
                trace_code=code,
                name=form.name.data,
                category=form.category.data,
                source_unit=form.source_unit.data,
                quantity=form.quantity.data,
                unit=form.unit.data,
                storage_location=form.storage_location.data,
                hazard_level=form.hazard_level.data,
                responsible_person=form.responsible_person.data,
                current_status='registered',
                remarks=form.remarks.data,
                is_abnormal=1 if form.is_abnormal.data else 0,
                external_disposal_info=form.external_disposal_info.data,
                created_by=current_user.id,
            )
            db.session.add(batch)
            db.session.flush()
            hist = WasteStatusHistory(
                waste_batch_id=batch.id,
                from_status=None,
                to_status='registered',
                changed_by=current_user.id,
                comment='Batch registered',
            )
            db.session.add(hist)
            log_action(
                actor=current_user,
                entity_type='WasteBatch',
                entity_id=batch.id,
                action='create',
                before=None,
                after={
                    'batch_code': batch.batch_code,
                    'status': batch.current_status,
                    'name': batch.name,
                },
            )
            db.session.commit()
            flash('Batch created.', 'success')
            return redirect(url_for('batch_detail', batch_id=batch.id))
        return render_template('batches/form.html', form=form, title='New batch')

    @app.route('/batches/<int:batch_id>')
    @login_required
    @roles_required(*viewers)
    def batch_detail(batch_id):
        batch = WasteBatch.query.get_or_404(batch_id)
        history = (
            WasteStatusHistory.query.filter_by(waste_batch_id=batch.id)
            .order_by(WasteStatusHistory.changed_at.asc())
            .all()
        )
        transfers = batch.transfers.order_by(TransferRecord.transfer_time.desc()).all()
        audit_logs = (
            AuditLog.query.filter_by(entity_type='WasteBatch', entity_id=batch.id)
            .order_by(AuditLog.created_at.desc())
            .limit(40)
            .all()
        )
        tform = TransferForm()
        choices = [(s, s) for s in sorted(next_statuses(batch.current_status))]
        if choices:
            sform = StatusTransitionForm()
            sform.to_status.choices = choices
        else:
            sform = None
        return render_template(
            'batches/detail.html',
            batch=batch,
            history=history,
            transfers=transfers,
            sform=sform,
            tform=tform,
            statuses=Config.WASTE_STATUSES,
            audit_logs=audit_logs,
        )

    @app.route('/batches/<int:batch_id>/edit', methods=['GET', 'POST'])
    @login_required
    @roles_required(*mutators)
    def batch_edit(batch_id):
        batch = WasteBatch.query.get_or_404(batch_id)
        if batch.current_status in ('disposed', 'archived'):
            flash('Cannot edit disposed/archived batches except via compliance workflow.', 'warning')
            return redirect(url_for('batch_detail', batch_id=batch.id))
        form = WasteBatchEditForm(obj=batch)
        if form.validate_on_submit():
            before = {
                'name': batch.name,
                'quantity': batch.quantity,
                'storage_location': batch.storage_location,
                'remarks': batch.remarks,
            }
            form.populate_obj(batch)
            batch.is_abnormal = 1 if form.is_abnormal.data else 0
            log_action(
                actor=current_user,
                entity_type='WasteBatch',
                entity_id=batch.id,
                action='update',
                before=before,
                after={
                    'name': batch.name,
                    'quantity': batch.quantity,
                    'storage_location': batch.storage_location,
                    'remarks': batch.remarks,
                },
            )
            db.session.commit()
            flash('Batch updated.', 'success')
            return redirect(url_for('batch_detail', batch_id=batch.id))
        return render_template('batches/form.html', form=form, title='Edit batch', batch=batch)

    @app.route('/batches/<int:batch_id>/transition', methods=['POST'])
    @login_required
    @roles_required(*mutators)
    def batch_transition(batch_id):
        batch = WasteBatch.query.get_or_404(batch_id)
        choices = [(s, s) for s in sorted(next_statuses(batch.current_status))]
        if not choices:
            flash('No legal transitions from this state.', 'warning')
            return redirect(url_for('batch_detail', batch_id=batch.id))
        sform = StatusTransitionForm()
        sform.to_status.choices = choices
        if not sform.validate_on_submit():
            flash('Invalid transition.', 'danger')
            return redirect(url_for('batch_detail', batch_id=batch.id))
        to_status = sform.to_status.data
        if not can_transition(batch.current_status, to_status):
            flash(f'Illegal transition {batch.current_status} → {to_status}.', 'danger')
            return redirect(url_for('batch_detail', batch_id=batch.id))
        before_status = batch.current_status
        batch.current_status = to_status
        db.session.add(
            WasteStatusHistory(
                waste_batch_id=batch.id,
                from_status=before_status,
                to_status=to_status,
                changed_by=current_user.id,
                comment=sform.comment.data,
            )
        )
        log_action(
            actor=current_user,
            entity_type='WasteBatch',
            entity_id=batch.id,
            action='status_transition',
            before={'status': before_status},
            after={'status': to_status},
            remark=sform.comment.data,
        )
        db.session.commit()
        flash('Status updated.', 'success')
        return redirect(url_for('batch_detail', batch_id=batch.id))

    @app.route('/batches/<int:batch_id>/transfer', methods=['POST'])
    @login_required
    @roles_required(*mutators)
    def batch_transfer(batch_id):
        batch = WasteBatch.query.get_or_404(batch_id)
        form = TransferForm()
        if not form.validate_on_submit():
            flash('Transfer form invalid.', 'danger')
            return redirect(url_for('batch_detail', batch_id=batch.id))
        rec = TransferRecord(
            waste_batch_id=batch.id,
            transfer_vendor=form.transfer_vendor.data,
            destination=form.destination.data or '',
            manifest_number=form.manifest_number.data or '',
            transfer_time=datetime.utcnow(),
        )
        db.session.add(rec)
        log_action(
            actor=current_user,
            entity_type='TransferRecord',
            entity_id=batch.id,
            action='transfer_recorded',
            after={
                'vendor': rec.transfer_vendor,
                'manifest': rec.manifest_number,
            },
        )
        db.session.commit()
        flash('Transfer recorded.', 'success')
        return redirect(url_for('batch_detail', batch_id=batch.id))

    @app.route('/batches/<int:batch_id>/qr.png')
    @login_required
    @roles_required(*viewers)
    def batch_qr_png(batch_id):
        batch = WasteBatch.query.get_or_404(batch_id)
        trace_url = request.url_root.rstrip('/') + url_for('trace_batch', code=batch.trace_code)
        img = qrcode.make(trace_url)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Response(buf.getvalue(), mimetype='image/png')
