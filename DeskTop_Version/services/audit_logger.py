import json
from sqlalchemy import event, insert
from datetime import datetime, date, time
from utils.user_context import get_current_user_id

def default_json_serializer(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    return str(obj)

def setup_audit_logging(Session):
    """
    Sets up event listeners on the provided Session factory/scoped_session.
    We track structural changes (creations, updates, deletions) for non-log tables.
    """
    
    # List of model class names to track for changes
    TRACKED_MODELS = [
        'Company', 'BusinessArea', 'Designation', 'DesignationSubcategory', 'Shift',
        'Employee', 'ShortLeave', 'HolidayCalendar', 'LeaveRequest', 'WeeklyHoliday',
        'LeaveQuota', 'PayrollConfig', 'AdminUser', 'Bonus', 'SalaryBreakdown'
    ]

    @event.listens_for(Session, 'after_flush')
    def receive_after_flush(session, flush_context):
        user_id = get_current_user_id()
        
        # We handle new, dirty (updated), and deleted objects separately
        for target in session.new:
            if target.__class__.__name__ in TRACKED_MODELS:
                record_audit(session, target, "Created", user_id)
                
        for target in session.dirty:
            if target.__class__.__name__ in TRACKED_MODELS:
                # To check if it was actually changed, we can check for history
                record_audit(session, target, "Updated", user_id)
                
        for target in session.deleted:
            if target.__class__.__name__ in TRACKED_MODELS:
                record_audit(session, target, "Deleted", user_id)

def record_audit(session, target, action, user_id):
    """Internal helper to extract changes and execute a core INSERT to avoid flush recursion."""
    # To avoid circular imports, we import SystemLog here
    from models import SystemLog
    
    details = {}
    from sqlalchemy import inspect
    inspections = inspect(target)
    
    if action == "Updated":
        for attr in inspections.mapper.column_attrs:
            history = inspections.get_history(attr.key, True)
            if history.has_changes():
                details[attr.key] = {
                    "old": history.deleted[0] if history.deleted else None,
                    "new": history.added[0] if history.added else None
                }
        if not details: # No actual data changed (maybe just a flush artifact)
            return
    elif action == "Created":
        for attr in inspections.mapper.column_attrs:
            details[attr.key] = getattr(target, attr.key)
    elif action == "Deleted":
        for attr in inspections.mapper.column_attrs:
            details[attr.key] = getattr(target, attr.key)

    try:
        details_json = json.dumps(details, default=default_json_serializer)
    except Exception:
        details_json = "{}"
        
    # Execute a core insert to bypass the current ORM flush/session tracking state
    # This prevents 'after_flush' from triggering another flush recursively.
    stmt = insert(SystemLog.__table__).values(
        timestamp=datetime.now(),
        user_id=user_id,
        action_type=action,
        entity_type=target.__class__.__name__,
        entity_id=getattr(target, 'id', None),
        details=details_json
    )
    session.execute(stmt)
