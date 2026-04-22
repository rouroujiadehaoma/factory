"""
Insert 10 demo waste batches (with status history). Run from project root:

    cd webproject0
    python scripts/seed_10_batches.py

Requires existing users (e.g. run `python run.py` once first).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta

from app import create_app, db
from app.models import User, WasteBatch, WasteStatusHistory
from app.utils.batch_util import next_batch_code


def _hist(batch_id, uid, chain):
    """chain: list of (from_status, to_status, comment) — first from can be None."""
    base = datetime.utcnow()
    for i, (from_s, to_s, comment) in enumerate(chain):
        db.session.add(
            WasteStatusHistory(
                waste_batch_id=batch_id,
                from_status=from_s,
                to_status=to_s,
                changed_by=uid,
                comment=comment,
                changed_at=base - timedelta(minutes=15 * (len(chain) - i)),
            )
        )


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        creator = User.query.filter_by(username='operator1').first() or User.query.filter_by(
            username='admin'
        ).first()
        if not creator:
            raise SystemExit('No user found. Start the app once with run.py to seed users.')

        uid = creator.id
        specs = [
            {
                'name': 'Acidic rinse water (pickling line)',
                'category': 'acid_waste',
                'source_unit': 'Unit-1 / Pickling',
                'quantity': 2.5,
                'unit': 'ton',
                'storage_location': 'Shed A-1',
                'hazard_level': 'medium',
                'responsible_person': 'operator1',
                'status': 'registered',
                'remarks': 'Batch record for weekly compliance check.',
                'abnormal': 0,
                'chain': [(None, 'registered', 'Line registration')],
            },
            {
                'name': 'Spent activated carbon (adsorption)',
                'category': 'adsorbent',
                'source_unit': 'Unit-2 / VOC treatment',
                'quantity': 800.0,
                'unit': 'kg',
                'storage_location': 'Warehouse W-4',
                'hazard_level': 'low',
                'responsible_person': 'operator1',
                'status': 'stored',
                'remarks': 'Sealed drums, label verified.',
                'abnormal': 0,
                'chain': [
                    (None, 'registered', 'Registered'),
                    ('registered', 'stored', 'Drums moved to W-4'),
                ],
            },
            {
                'name': 'Alkaline cleaning effluent',
                'category': 'alkaline',
                'source_unit': 'Unit-5 / CIP',
                'quantity': 15.0,
                'unit': 'ton',
                'storage_location': 'Tank farm T-08',
                'hazard_level': 'medium',
                'responsible_person': 'operator1',
                'status': 'pending_transfer',
                'remarks': 'Scheduled for vendor pickup next week.',
                'abnormal': 0,
                'chain': [
                    (None, 'registered', 'Registered'),
                    ('registered', 'stored', 'Neutralization complete'),
                    ('stored', 'pending_transfer', 'Awaiting carrier manifest'),
                ],
            },
            {
                'name': 'Waste catalyst (Ni-based)',
                'category': 'catalyst',
                'source_unit': 'Unit-4 / Hydrogenation',
                'quantity': 45.0,
                'unit': 'kg',
                'storage_location': 'Secure cage C-2',
                'hazard_level': 'high',
                'responsible_person': 'es_officer',
                'status': 'in_transit',
                'remarks': 'Escorted transfer to port.',
                'abnormal': 0,
                'chain': [
                    (None, 'registered', 'Registered'),
                    ('registered', 'stored', 'Caged storage'),
                    ('stored', 'pending_transfer', 'Manifest HW-TR-1042'),
                    ('pending_transfer', 'in_transit', 'Carrier: Mock Logistics Ltd'),
                ],
            },
            {
                'name': 'Off-spec solvent blend',
                'category': 'organic_solvent',
                'source_unit': 'Unit-3 / Distillation',
                'quantity': 340.0,
                'unit': 'L',
                'storage_location': 'Tank farm T-15',
                'hazard_level': 'high',
                'responsible_person': 'operator1',
                'status': 'received_by_disposal_vendor',
                'remarks': 'Third-party treatment plant signed receipt.',
                'abnormal': 0,
                'chain': [
                    (None, 'registered', 'Registered'),
                    ('registered', 'stored', 'Tank transfer'),
                    ('stored', 'pending_transfer', 'Contract signed'),
                    ('pending_transfer', 'in_transit', 'Road transport'),
                    ('in_transit', 'received_by_disposal_vendor', 'Vendor receipt #VR-8891'),
                ],
            },
            {
                'name': 'Laboratory mixed chemical waste',
                'category': 'lab_mixed',
                'source_unit': 'Central lab',
                'quantity': 65.0,
                'unit': 'kg',
                'storage_location': 'Lab store L-01',
                'hazard_level': 'medium',
                'responsible_person': 'operator1',
                'status': 'disposed',
                'remarks': 'Incineration with energy recovery.',
                'abnormal': 0,
                'chain': [
                    (None, 'registered', 'Registered'),
                    ('registered', 'stored', 'Segregated storage'),
                    ('stored', 'pending_transfer', 'Lab clearance'),
                    ('pending_transfer', 'in_transit', 'Sent to disposal site'),
                    ('in_transit', 'received_by_disposal_vendor', 'Weighbridge OK'),
                    ('received_by_disposal_vendor', 'disposed', 'COA on file'),
                ],
            },
            {
                'name': 'Oily sludge (API separator)',
                'category': 'oily_sludge',
                'source_unit': 'Unit-6 / WWT',
                'quantity': 12.0,
                'unit': 'ton',
                'storage_location': 'Berm area B-3',
                'hazard_level': 'medium',
                'responsible_person': 'operator1',
                'status': 'stored',
                'remarks': 'Minor sheen observed — monitoring (no leak keyword).',
                'abnormal': 1,
                'chain': [
                    (None, 'registered', 'Registered'),
                    ('registered', 'stored', 'Temporary berm storage'),
                ],
            },
            {
                'name': 'Chlorinated by-product tar',
                'category': 'chlorinated_organics',
                'source_unit': 'Unit-7 / Chlorination',
                'quantity': 210.0,
                'unit': 'kg',
                'storage_location': 'Tank farm T-12',
                'hazard_level': 'critical',
                'responsible_person': 'es_officer',
                'status': 'pending_transfer',
                'remarks': 'Elevated temperature monitoring; priority disposal.',
                'abnormal': 0,
                'chain': [
                    (None, 'registered', 'Registered'),
                    ('registered', 'stored', 'Cooling period complete'),
                    ('stored', 'pending_transfer', 'Vendor slot booked'),
                ],
            },
            {
                'name': 'Empty contaminated drums (triple-rinsed)',
                'category': 'containers',
                'source_unit': 'Unit-8 / Packaging',
                'quantity': 140.0,
                'unit': 'pcs',
                'storage_location': 'Scrap yard Y-2',
                'hazard_level': 'low',
                'responsible_person': 'operator1',
                'status': 'registered',
                'remarks': 'Residual film only; batch for metal recycler.',
                'abnormal': 0,
                'chain': [(None, 'registered', 'Registered')],
            },
            {
                'name': 'Legacy batch — archived sample',
                'category': 'legacy',
                'source_unit': 'Decommissioned Unit-0',
                'quantity': 0.5,
                'unit': 'ton',
                'storage_location': 'Archive vault V-9',
                'hazard_level': 'low',
                'responsible_person': 'admin',
                'status': 'archived',
                'remarks': 'Retention period ended; records retained 7 years.',
                'abnormal': 0,
                'chain': [
                    (None, 'registered', 'Historical import'),
                    ('registered', 'stored', 'Vault storage'),
                    ('stored', 'pending_transfer', 'Disposition approved'),
                    ('pending_transfer', 'in_transit', 'Final move'),
                    ('in_transit', 'received_by_disposal_vendor', 'Destroyed'),
                    ('received_by_disposal_vendor', 'disposed', 'Certificate archived'),
                    ('disposed', 'archived', 'Lifecycle closed'),
                ],
            },
        ]

        created = 0
        for spec in specs:
            code = next_batch_code()
            b = WasteBatch(
                batch_code=code,
                trace_code=code,
                name=spec['name'],
                category=spec['category'],
                source_unit=spec['source_unit'],
                quantity=spec['quantity'],
                unit=spec['unit'],
                storage_location=spec['storage_location'],
                hazard_level=spec['hazard_level'],
                responsible_person=spec['responsible_person'],
                current_status=spec['status'],
                remarks=spec['remarks'],
                is_abnormal=spec['abnormal'],
                created_by=uid,
            )
            db.session.add(b)
            db.session.flush()
            _hist(b.id, uid, spec['chain'])
            created += 1

        db.session.commit()
        print(f'Inserted {created} waste batches. Last codes use prefix HW-{datetime.utcnow().year}-')


if __name__ == '__main__':
    main()
