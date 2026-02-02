from sqlalchemy.orm import Session
from models import LeaveRequest, LeaveQuota, Employee, ShortLeave
from datetime import date, datetime
from sqlalchemy import func

class LeaveService:
    @staticmethod
    def get_leave_balance(session: Session, employee_id: int, year: int) -> dict:
        """
        Calculates used and remaining leave for an employee.
        Returns: { 'type': {'quota': X, 'used': Y, 'remaining': Z} }
        """
        employee = session.query(Employee).get(employee_id)
        if not employee: return {}
        
        # 1. Get Quotas (Hierarchy: EMP (Todo?) > BA > COMP)
        # Assuming Quota is set at BA or Comp level for now.
        # Check BA Quotas
        ba_quotas = session.query(LeaveQuota).filter_by(
            year=year, business_area_id=employee.business_area_id
        ).all()
        
        # Check Company Quotas (if BA not set for that type)
        comp_quotas = session.query(LeaveQuota).filter_by(
            year=year, company_id=employee.company_id
        ).all()
        
        # Merge Quotas (BA overrides Comp)
        quotas = {}
        for q in comp_quotas:
            quotas[q.leave_type] = q.quota_limit
        for q in ba_quotas:
            quotas[q.leave_type] = q.quota_limit # Override
            
        # 2. Get Used Leaves (Approved)
        used_stats = {}
        
        # Full Day Leaves
        approved_requests = session.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == "Approved",
            func.strftime('%Y', LeaveRequest.start_date) == str(year)
        ).all()
        
        for req in approved_requests:
            days = (req.end_date - req.start_date).days + 1
            used_stats[req.leave_type] = used_stats.get(req.leave_type, 0) + days
            
        # Short Leaves (Converted to hours? Or days?)
        # Quota usually has "ShortLeave" (hours).
        short_leaves = session.query(ShortLeave).filter(
            ShortLeave.employee_id == employee.id,
            ShortLeave.status == "Approved",
            func.strftime('%Y', ShortLeave.date) == str(year)
        ).all()
        
        short_leave_hours = 0
        for sl in short_leaves:
            # Calc duration
            start = datetime.combine(date.min, sl.start_time)
            end = datetime.combine(date.min, sl.end_time)
            short_leave_hours += (end - start).total_seconds() / 3600
            
        used_stats["ShortLeave"] = round(short_leave_hours, 2)
        
        # 3. Compile Result
        balance = {}
        # Ensure ShortLeave is in quotas map if not exist (default 0 or handled)
        all_types = set(quotas.keys()).union(set(used_stats.keys()))
        
        for l_type in all_types:
            q = quotas.get(l_type, 0)
            u = used_stats.get(l_type, 0)
            balance[l_type] = {
                "quota": q,
                "used": u,
                "remaining": q - u
            }
            
        return balance

    @staticmethod
    def submit_leave_request(session: Session, employee_id: int, leave_type: str, start_date: date, end_date: date, reason: str) -> dict:
        # Validate dates
        if end_date < start_date:
            return {"success": False, "message": "End date cannot be before start date"}
            
        # Check quota? Optional. Policy might allow requesting anyway.
        # Use get_leave_balance.
        
        req = LeaveRequest(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            request_date=date.today(),
            reason=reason,
            status="Pending"
        )
        session.add(req)
        session.commit()
        
        return {"success": True, "message": "Leave request submitted successfully"}

    @staticmethod
    def approve_request(session: Session, request_id: int, admin_user: str) -> dict:
        req = session.query(LeaveRequest).get(request_id)
        if not req: return {"success": False, "message": "Request not found"}
        
        req.status = "Approved"
        session.commit()
        return {"success": True, "message": "Request approved"}

    @staticmethod
    def reject_request(session: Session, request_id: int, reason: str) -> dict:
        req = session.query(LeaveRequest).get(request_id)
        if not req: return {"success": False, "message": "Request not found"}
        
        req.status = "Rejected"
        req.rejection_reason = reason
        session.commit()
        return {"success": True, "message": "Request rejected"}
    
    @staticmethod
    def approve_short_leave(session: Session, leave_id: int) -> dict:
        sl = session.query(ShortLeave).get(leave_id)
        if not sl: return {"success": False, "message": "Request not found"}
        
        sl.status = "Approved"
        session.commit()
        return {"success": True, "message": "Short Leave approved"}
        
    @staticmethod
    def reject_short_leave(session: Session, leave_id: int) -> dict:
        sl = session.query(ShortLeave).get(leave_id)
        if not sl: return {"success": False, "message": "Request not found"}
        
        sl.status = "Rejected"
        session.commit()
        return {"success": True, "message": "Short Leave rejected"}
