from app.db.models import AuditEvent
async def audit(db, action, resource_type, resource_id=None, outcome="success", details=None):
    db.add(AuditEvent(action=action,resource_type=resource_type,resource_id=str(resource_id) if resource_id is not None else None,outcome=outcome,details=details))
