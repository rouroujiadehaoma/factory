"""Test script to check user promote/demote functionality"""
from app import create_app, db
from app.models import User, ResidentInfo, ManagerInfo

def test_user_roles():
    """Test user roles and their info records"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Checking user roles and info records")
        print("=" * 60)
        
        users = User.query.filter_by(is_deleted=0).all()
        
        for user in users:
            print(f"\nUser: {user.username} (ID: {user.user_id})")
            print(f"  Type: {user.user_type} ({'Resident' if user.user_type == 0 else 'Manager' if user.user_type == 1 else 'Admin'})")
            
            has_resident_info = ResidentInfo.query.filter_by(user_id=user.user_id).first() is not None
            has_manager_info = ManagerInfo.query.filter_by(user_id=user.user_id).first() is not None
            
            print(f"  Has ResidentInfo: {has_resident_info}")
            print(f"  Has ManagerInfo: {has_manager_info}")
            
            # Check for inconsistencies
            if user.user_type == 0 and not has_resident_info:
                print(f"  ⚠ WARNING: Resident user without ResidentInfo record!")
            if user.user_type == 1 and not has_manager_info:
                print(f"  ⚠ WARNING: Manager user without ManagerInfo record!")
            if user.user_type == 0 and has_manager_info:
                print(f"  ⚠ WARNING: Resident user has ManagerInfo record!")
            if user.user_type == 1 and has_resident_info:
                print(f"  ⚠ WARNING: Manager user has ResidentInfo record!")

if __name__ == '__main__':
    test_user_roles()

