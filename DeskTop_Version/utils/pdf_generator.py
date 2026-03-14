import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

class PDFGenerator:
    @staticmethod
    def generate_payslip(payroll_record, filepath, generator_name="System"):
        from models import SalaryBreakdown
        from database import get_db_session
        from datetime import datetime
        employee = payroll_record.employee
        session = get_db_session()
        breakdown = session.query(SalaryBreakdown).filter_by(employee_id=employee.id, year=payroll_record.year).first()
        
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=50, bottomMargin=50)
        elements = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=5
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            alignment=TA_RIGHT,
            spaceAfter=15
        )

        company_name = employee.company.name if employee.company else "Company Info Unavailable"
        
        # Header
        elements.append(Paragraph(company_name.upper(), title_style))
        month_name = f"Payslip {payroll_record.year}-{payroll_record.month:02d}"
        elements.append(Paragraph(month_name, subtitle_style))

        # Employee Info Section
        emp_info_data = [
            [f"Name: {employee.full_name}", f"Joining Date: {employee.joining_date.strftime('%d.%m.%Y') if employee.joining_date else '-'}"],
            [f"Emp. ID: {employee.id}", f"Department: {employee.business_area.name if employee.business_area else '-'}"],
            [f"Grade: {employee.designation.name if employee.designation else '-'}", f"No. of Working Days: {payroll_record.total_present + payroll_record.total_absent + payroll_record.total_leave:.2f}"],
            [f"Designation: {employee.designation_subcategory.name if employee.designation_subcategory else '-'}", f"No. of Paid Days: {payroll_record.total_present + payroll_record.total_leave:.2f}"]
        ]
        
        emp_table = Table(emp_info_data, colWidths=[270, 260])
        emp_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(emp_table)
        elements.append(Spacer(1, 15))

        # Salary Details Section
        base = payroll_record.base_salary
        net = payroll_record.net_salary

        if breakdown:
            basic = breakdown.basic
            hra = breakdown.house_rent_allowance
            conveyance = breakdown.conveyance
            medical = breakdown.medical
            other = breakdown.other_allowance
            mobile = breakdown.mobile_bill
            transport = breakdown.transportation_allowance
        else:
            basic = base * 0.40
            hra = base * 0.25
            conveyance = base * 0.15
            medical = base * 0.05
            other = base * 0.15
            mobile = 0.0
            transport = 0.0
            
        total_payment = basic + hra + conveyance + medical + other + mobile + transport + payroll_record.ot_pay
        total_deduction = payroll_record.late_deduction + payroll_record.leave_deduction

        details_data = [
            ["Payment Details", "Amount", "Deduction Details", "Amount"],
            ["Basic", f"{basic:,.2f}", "Late Deduction", f"{payroll_record.late_deduction:,.2f}"],
            ["House Rent Allowance", f"{hra:,.2f}", "Leave Deduction", f"{payroll_record.leave_deduction:,.2f}"],
            ["Conveyance", f"{conveyance:,.2f}", "Other Deductions", "0.00"],
            ["Medical", f"{medical:,.2f}", "", ""],
            ["Mobile Bill", f"{mobile:,.2f}", "", ""],
            ["Transportation", f"{transport:,.2f}", "", ""],
            ["Other Allowance", f"{other:,.2f}", "", ""],
        ]
        
        if payroll_record.ot_pay > 0:
            details_data.append(["Overtime Pay", f"{payroll_record.ot_pay:,.2f}", "", ""])

        # Add empty rows to match height if needed
        while len(details_data) < 10:
             details_data.append(["", "", "", ""])

        # Totals Row
        details_data.append([
            "Total Payment", f"{total_payment:,.2f}", 
            "Total Deduction", f"{total_deduction:,.2f}"
        ])

        details_table = Table(details_data, colWidths=[180, 85, 180, 85])
        details_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,1), (1,-1), 'RIGHT'),
            ('ALIGN', (3,1), (3,-1), 'RIGHT'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Bold Totals
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        elements.append(details_table)
        
        # Net Pay Row (Fixed formula)
        net_pay_calculated = total_payment - total_deduction
        net_pay_data = [["Net Pay:", "", "", f"{net_pay_calculated:,.2f}"]]
        net_pay_table = Table(net_pay_data, colWidths=[180, 85, 180, 85])
        net_pay_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (3,0), (3,0), 'RIGHT'),
        ]))
        elements.append(net_pay_table)
        elements.append(Spacer(1, 20))
        
        # Amount in words (Dynamic South-Asian format)
        elements.append(Paragraph(f"In Words: {PDFGenerator.number_to_words(int(net_pay_calculated))} Taka Only", styles['Normal']))
        elements.append(Spacer(1, 60))

        # Signatures Block
        sig_data = [
            ["_______________", "_______________", "_______________", "_______________"],
            ["Checked By", "Authorized By", "Paid By", "Received By"]
        ]
        sig_table = Table(sig_data, colWidths=[132, 132, 132, 132])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), -5)
        ]))
        elements.append(sig_table)
        elements.append(Spacer(1, 30))

        # Generator Stamp (Moved to below signatures)
        gen_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        small_style = ParagraphStyle('SmallStyle', parent=styles['Normal'], fontSize=8, alignment=TA_RIGHT, textColor=colors.gray)
        elements.append(Paragraph(f"Generated by: {generator_name} on {gen_time}", small_style))

        doc.build(elements)
        return True

    @staticmethod
    def generate_bonus_statement(bonus_record, filepath, generator_name="System"):
        from datetime import datetime
        employee = bonus_record.employee
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=50, bottomMargin=50)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, alignment=TA_CENTER, spaceAfter=5)
        subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, alignment=TA_RIGHT, spaceAfter=15)

        company_name = employee.company.name if employee.company else "Company Info Unavailable"
        elements.append(Paragraph(company_name.upper(), title_style))
        month_name = f"Bonus Statement {bonus_record.year}-{bonus_record.month:02d}"
        elements.append(Paragraph(month_name, subtitle_style))

        # Employee Info
        emp_info_data = [
            [f"Name: {employee.full_name}", f"Department: {employee.business_area.name if employee.business_area else '-'}"],
            [f"Emp. ID: {employee.id}", f"Grade: {employee.designation.name if employee.designation else '-'}"]
        ]
        emp_table = Table(emp_info_data, colWidths=[270, 260])
        emp_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('FONTNAME', (0,0), (-1,-1), 'Helvetica')]))
        elements.append(emp_table)
        elements.append(Spacer(1, 15))

        # Bonus Details
        rate_str = f"{bonus_record.bonus_rate_or_amount}%" if bonus_record.is_percentage else f"{bonus_record.bonus_rate_or_amount:,.2f}"
        
        details_data = [
            ["Details", "Amount"],
            ["Base Salary", f"{bonus_record.base_salary:,.2f}"],
            ["Bonus Rate/Amount", rate_str],
            ["Final Bonus Pay", f"{bonus_record.final_bonus_pay:,.2f}"]
        ]
        
        details_table = Table(details_data, colWidths=[270, 260])
        details_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,1), (1,-1), 'RIGHT'),
        ]))
        
        elements.append(details_table)
        elements.append(Spacer(1, 60))

        # Signatures & Generator Stamp
        gen_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        small_style = ParagraphStyle('SmallStyle', parent=styles['Normal'], fontSize=8, alignment=TA_RIGHT, textColor=colors.gray)
        elements.append(Paragraph(f"Generated by: {generator_name} on {gen_time}", small_style))
        elements.append(Spacer(1, 40))

        sig_data = [
            ["_______________", "_______________"],
            ["Authorized By", "Received By"]
        ]
        sig_table = Table(sig_data, colWidths=[265, 265])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), -5)
        ]))
        elements.append(sig_table)

        doc.build(elements)
        return True

    @staticmethod
    def number_to_words(num):
        if num == 0:
            return "Zero"

        def _convert_below_1000(n):
            ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
            tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
            
            if n == 0:
                return ""
            elif n < 20:
                return ones[n]
            elif n < 100:
                return tens[n // 10] + (" " + ones[n % 10] if (n % 10) != 0 else "")
            else:
                return ones[n // 100] + " Hundred" + (" " + _convert_below_1000(n % 100) if (n % 100) != 0 else "")

        if num < 0:
            return "Minus " + PDFGenerator.number_to_words(abs(num))
            
        words = ""
        
        # Crores (10,000,000)
        crore = num // 10000000
        num %= 10000000
        if crore > 0:
            words += _convert_below_1000(crore) + " Crore "
            
        # Lacs / Lakhs (100,000)
        lac = num // 100000
        num %= 100000
        if lac > 0:
            words += _convert_below_1000(lac) + " Lac "
            
        # Thousands (1,000)
        thousand = num // 1000
        num %= 1000
        if thousand > 0:
            words += _convert_below_1000(thousand) + " Thousand "
            
        # Hundreds and Below
        if num > 0:
            words += _convert_below_1000(num)
            
        return words.strip()
