"""Statistics utility functions"""
from app import db
from app.models import RecycleOrder, ResidentInfo, User
from datetime import datetime, timedelta
from config import Config

def calculate_points(garbage_type, weight):
    """Calculate points"""
    points_per_kg = Config.POINTS_PER_KG.get(garbage_type, 10)
    return int(weight * points_per_kg)

def award_points_to_resident(resident_id, points):
    """Award points to resident"""
    resident = ResidentInfo.query.get(resident_id)
    if resident:
        resident.garbage_points += points
        resident.last_recycle_time = datetime.utcnow()
        db.session.commit()
        return True
    return False

def get_recycling_stats(time_range='month'):
    """Get recycling statistics"""
    now = datetime.utcnow()
    
    if time_range == 'week':
        start_date = now - timedelta(days=7)
    elif time_range == 'month':
        start_date = now - timedelta(days=30)
    elif time_range == 'quarter':
        start_date = now - timedelta(days=90)
    elif time_range == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = datetime(2020, 1, 1)
    
    # Total recycled weight
    total_weight = db.session.query(db.func.sum(RecycleOrder.recycle_weight)).filter(
        RecycleOrder.order_status == 'completed',
        RecycleOrder.create_time >= start_date
    ).scalar() or 0
    
    # Statistics by category
    category_stats = {}
    categories = ['paper', 'plastic', 'clothes', 'electronic', 'other']
    for cat in categories:
        weight = db.session.query(db.func.sum(RecycleOrder.recycle_weight)).filter(
            RecycleOrder.garbage_type == cat,
            RecycleOrder.order_status == 'completed',
            RecycleOrder.create_time >= start_date
        ).scalar() or 0
        category_stats[cat] = float(weight)
    
    # Participant count
    participant_count = db.session.query(db.func.count(db.func.distinct(RecycleOrder.resident_id))).filter(
        RecycleOrder.order_status == 'completed',
        RecycleOrder.create_time >= start_date
    ).scalar() or 0
    
    # Total points
    total_points = db.session.query(db.func.sum(RecycleOrder.recycle_weight)).filter(
        RecycleOrder.order_status == 'completed',
        RecycleOrder.create_time >= start_date
    ).scalar() or 0
    # Simplified calculation, should calculate by category in practice
    total_points = int(total_points * 20)  # Average 20 points per kg
    
    return {
        'total_weight': float(total_weight),
        'category_stats': category_stats,
        'participant_count': participant_count,
        'total_points': total_points
    }

def get_order_status_stats():
    """Get order status statistics"""
    stats = {
        'pending': RecycleOrder.query.filter_by(order_status='pending').count(),
        'assigned': RecycleOrder.query.filter_by(order_status='assigned').count(),
        'in_progress': RecycleOrder.query.filter_by(order_status='in_progress').count(),
        'completed': RecycleOrder.query.filter_by(order_status='completed').count(),
        'cancelled': RecycleOrder.query.filter_by(order_status='cancelled').count()
    }
    return stats

