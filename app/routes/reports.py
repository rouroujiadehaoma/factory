"""Compliance-oriented exports (CSV / PDF)."""
import csv
import io
from datetime import datetime

from flask import Response, render_template
from flask_login import current_user, login_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func

from app import db
from app.models import AlertEvent, ReportExportHistory, WasteBatch
from app.utils.rbac import roles_required
from config import Config


def register_routes(app):
    exporters = (
        Config.ROLE_ADMINISTRATOR,
        Config.ROLE_ES_OFFICER,
        Config.ROLE_AUDITOR,
    )

    @app.route('/reports')
    @login_required
    @roles_required(*exporters)
    def reports_home():
        return render_template('reports/index.html')

    @app.route('/reports/export/summary.csv')
    @login_required
    @roles_required(*exporters)
    def export_summary_csv():
        si = io.StringIO()
        w = csv.writer(si)
        w.writerow(
            [
                'batch_code',
                'name',
                'category',
                'quantity',
                'unit',
                'status',
                'hazard_level',
                'storage_location',
                'created_at',
            ]
        )
        for b in WasteBatch.query.order_by(WasteBatch.id).all():
            w.writerow(
                [
                    b.batch_code,
                    b.name,
                    b.category,
                    b.quantity,
                    b.unit,
                    b.current_status,
                    b.hazard_level,
                    b.storage_location,
                    b.created_at.isoformat() if b.created_at else '',
                ]
            )
        rec = ReportExportHistory(
            exported_by=current_user.id,
            report_type='summary_csv',
            file_path='inline',
        )
        db.session.add(rec)
        db.session.commit()
        return Response(
            si.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=hazwaste_summary.csv'},
        )

    @app.route('/reports/export/monthly.pdf')
    @login_required
    @roles_required(*exporters)
    def export_monthly_pdf():
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont('Helvetica-Bold', 14)
        c.drawString(50, y, 'Hazardous waste — monthly compliance snapshot')
        y -= 30
        c.setFont('Helvetica', 10)
        now = datetime.utcnow()
        c.drawString(50, y, f'Generated (UTC): {now.isoformat()}Z')
        y -= 24
        total = WasteBatch.query.count()
        by_status = dict(
            db.session.query(WasteBatch.current_status, func.count(WasteBatch.id))
            .group_by(WasteBatch.current_status)
            .all()
        )
        c.drawString(50, y, f'Total batches: {total}')
        y -= 18
        for k, v in sorted(by_status.items()):
            c.drawString(50, y, f'  {k}: {v}')
            y -= 16
            if y < 80:
                c.showPage()
                y = height - 50
        open_alerts = AlertEvent.query.filter_by(status='open').count()
        y -= 10
        c.drawString(50, y, f'Open alerts: {open_alerts}')
        c.showPage()
        c.save()
        buf.seek(0)
        rec = ReportExportHistory(
            exported_by=current_user.id,
            report_type='monthly_pdf',
            file_path='inline',
        )
        db.session.add(rec)
        db.session.commit()
        return Response(
            buf.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': 'attachment; filename=hazwaste_monthly.pdf'},
        )
