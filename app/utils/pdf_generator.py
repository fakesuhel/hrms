from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
from datetime import datetime
from typing import Dict, Any

async def generate_salary_slip_pdf(slip_data: Dict[str, Any]) -> bytes:
    """Generate a clean and simple salary slip PDF"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50, leftMargin=50, rightMargin=50)
    
    styles = getSampleStyleSheet()
    
    # Define clean styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    story = []
    
    # Header
    story.append(Paragraph('SALARY SLIP', title_style))
    month_name = datetime(slip_data['year'], slip_data['month'], 1).strftime('%B')
    story.append(Paragraph(f'{month_name} {slip_data["year"]}', subtitle_style))
    
    # Company Info - Clean without icons
    company_info = """
    <b>Bhoomi Techzone Pvt. Ltd.</b><br/>
    A-43, A Block, Sector 63, Noida, Uttar Pradesh 201301<br/>
    Email: info@bhoomitechzone.com | Website: www.bhoomitechzone.com
    """
    story.append(Paragraph(company_info, 
                          ParagraphStyle('Company', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)))
    story.append(Spacer(1, 30))
    
    # Calculate salary including incentives
    total_monthly_salary = slip_data['base_salary'] + slip_data['hra'] + slip_data['allowances'] + slip_data.get('incentives', 0)
    actual_working_days = 30 - slip_data['absent_days'] - (slip_data.get('half_days', 0) * 0.5)
    
    proportional_base = (slip_data['base_salary'] / 30) * actual_working_days
    proportional_hra = (slip_data['hra'] / 30) * actual_working_days
    proportional_allowances = (slip_data['allowances'] / 30) * actual_working_days
    proportional_incentives = (slip_data.get('incentives', 0) / 30) * actual_working_days
    
    gross_salary = proportional_base + proportional_hra + proportional_allowances + proportional_incentives
    total_deductions = (slip_data['pf_deduction'] + slip_data['tax_deduction'] + 
                       slip_data['penalty_deductions'] + slip_data.get('other_deductions', 0))
    net_pay = gross_salary - total_deductions
    
    # Single Complete Table with all information
    table_data = [
        # Employee Information Header
        ['EMPLOYEE INFORMATION', '', '', ''],
        ['Employee ID:', slip_data['employee_id'], 'Name:', slip_data['employee_name']],
        ['Department:', slip_data['department'], 'Designation:', slip_data['designation']],
        ['Working Days:', f"{actual_working_days:.0f}/30", 'Absent Days:', str(slip_data['absent_days'])],
        
        # Spacing row
        ['', '', '', ''],
        
        # Salary Information Header  
        ['SALARY BREAKDOWN', '', '', ''],
        ['EARNINGS', 'AMOUNT', 'DEDUCTIONS', 'AMOUNT'],
        ['Basic Salary', f"Rs. {proportional_base:,.0f}", 'PF Deduction', f"Rs. {slip_data['pf_deduction']:,.0f}"],
        ['HRA', f"Rs. {proportional_hra:,.0f}", 'Tax Deduction', f"Rs. {slip_data['tax_deduction']:,.0f}"],
        ['Allowances', f"Rs. {proportional_allowances:,.0f}", 'Penalty', f"Rs. {slip_data['penalty_deductions']:,.0f}"],
    ]
    
    # Add incentives row if it exists
    if slip_data.get('incentives', 0) > 0:
        table_data.append(['Incentives', f"Rs. {proportional_incentives:,.0f}", '', ''])
    
    # Add totals and net salary
    table_data.extend([
        ['', '', '', ''],
        ['GROSS SALARY', f"Rs. {gross_salary:,.0f}", 'TOTAL DEDUCTIONS', f"Rs. {total_deductions:,.0f}"],
        ['', '', '', ''],
        ['NET SALARY PAYABLE', '', '', f"Rs. {net_pay:,.0f}"],
    ])
    
    # Create the single comprehensive table
    main_table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch, 1.5*inch])
    main_table.setStyle(TableStyle([
        # Employee Info Header
        ('SPAN', (0, 0), (3, 0)),
        ('BACKGROUND', (0, 0), (3, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (3, 0), colors.white),
        ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (3, 0), 12),
        ('ALIGN', (0, 0), (3, 0), 'CENTER'),
        
        # Employee Info Rows
        ('BACKGROUND', (0, 1), (3, 3), colors.lightgrey),
        ('FONTNAME', (0, 1), (3, 3), 'Helvetica'),
        ('FONTSIZE', (0, 1), (3, 3), 10),
        
        # Salary Breakdown Header
        ('SPAN', (0, 5), (3, 5)),
        ('BACKGROUND', (0, 5), (3, 5), colors.darkgreen),
        ('TEXTCOLOR', (0, 5), (3, 5), colors.white),
        ('FONTNAME', (0, 5), (3, 5), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 5), (3, 5), 12),
        ('ALIGN', (0, 5), (3, 5), 'CENTER'),
        
        # Salary Headers
        ('BACKGROUND', (0, 6), (3, 6), colors.lightblue),
        ('FONTNAME', (0, 6), (3, 6), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 6), (3, 6), 11),
        
        # Salary Data Rows
        ('FONTNAME', (0, 7), (3, -4), 'Helvetica'),
        ('FONTSIZE', (0, 7), (3, -4), 10),
        
        # Totals Row
        ('BACKGROUND', (0, -3), (3, -3), colors.lightblue),
        ('FONTNAME', (0, -3), (3, -3), 'Helvetica-Bold'),
        
        # Net Salary Row
        ('SPAN', (0, -1), (2, -1)),
        ('BACKGROUND', (0, -1), (3, -1), colors.darkgreen),
        ('TEXTCOLOR', (0, -1), (3, -1), colors.white),
        ('FONTNAME', (0, -1), (3, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (3, -1), 16),
        ('ALIGN', (0, -1), (2, -1), 'CENTER'),
        ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
        
        # General Styling
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(main_table)
    story.append(Spacer(1, 40))
    
    # Footer
    story.append(Paragraph('<i>This is a computer generated salary slip.</i>', 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                       alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content
    """Generate a professional salary slip PDF matching the provided format"""
    
    # Create a bytes buffer for the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document with proper margins
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=40, bottomMargin=40, leftMargin=40, rightMargin=40)
    
    # Define custom styles
    styles = getSampleStyleSheet()
    
    # Header style for PAYSLIP
    header_style = ParagraphStyle(
        'PayslipHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=5,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    
    # Month/Year style
    month_style = ParagraphStyle(
        'MonthStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    
    # Company name style
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=5,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    
    # Address style
    address_style = ParagraphStyle(
        'AddressStyle',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=3,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica'
    )
    
    # Section header style
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    
    # Story will hold all elements
    story = []
    
    # Header section with PAYSLIP and month
    header_data = [
        ['PAYSLIP', '', '', datetime(slip_data['year'], slip_data['month'], 1).strftime('%b %Y').upper()]
    ]
    
    header_table = Table(header_data, colWidths=[2*inch, 2*inch, 2*inch, 1.5*inch])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 16),
        ('FONTNAME', (3, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (3, 0), (3, 0), 12),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    
    # Company header with logo space and clean design
    company_header = [
        ['BHOOMI TECHZONE PVT. LTD.', '', '', f'PAYSLIP - {month_name.upper()} {slip_data["year"]}']
    ]
    
    header_table = Table(company_header, colWidths=[4*inch, 1*inch, 1*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('FONTNAME', (3, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (3, 0), (3, 0), 12),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.darkblue),
        ('TEXTCOLOR', (3, 0), (3, 0), colors.darkred),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(header_table)
    
    # Company address
    address_data = [
        ['A-43, A Block, Sector 63, Noida, Uttar Pradesh 201301', '', '📧 info@bhoomitechzone.com'],
        ['🌐 www.bhoomitechzone.com', '', '📞 +91-120-4298000']
    ]
    
    address_table = Table(address_data, colWidths=[4*inch, 1*inch, 2*inch])
    address_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    company_table = Table(company_data, colWidths=[2.5*inch, 1*inch, 1*inch, 2*inch])
    company_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 10),
        ('FONTNAME', (0, 1), (0, 3), 'Helvetica'),
        ('FONTSIZE', (0, 1), (0, 3), 8),
        ('FONTNAME', (3, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (3, 0), (3, 3), 8),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(company_table)
    story.append(Spacer(1, 20))
    
    # Calculate salary based on 30-day month standard
    total_monthly_salary = slip_data['base_salary'] + slip_data['hra'] + slip_data['allowances']
    per_day_earning = total_monthly_salary / 30
    
    # Calculate actual days worked (30 - absent_days - (half_days * 0.5))
    actual_working_days = 30 - slip_data['absent_days'] - (slip_data.get('half_days', 0) * 0.5)
    
    # Calculate proportional salary
    proportional_base = (slip_data['base_salary'] / 30) * actual_working_days
    proportional_hra = (slip_data['hra'] / 30) * actual_working_days
    proportional_allowances = (slip_data['allowances'] / 30) * actual_working_days
    
    gross_salary = proportional_base + proportional_hra + proportional_allowances
    
    # Deductions remain the same regardless of working days
    total_deductions = (slip_data['pf_deduction'] + slip_data['tax_deduction'] + 
                       slip_data['penalty_deductions'] + slip_data.get('other_deductions', 0))
    
    # Simple Employee Info
    emp_info_data = [
        ['Employee ID:', slip_data['employee_id'], 'Name:', slip_data['employee_name']],
        ['Department:', slip_data['department'], 'Designation:', slip_data['designation']],
        ['Working Days:', f"{actual_working_days:.0f}/30", 'Absent Days:', str(slip_data['absent_days'])]
    ]
    
    emp_table = Table(emp_info_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    emp_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(emp_table)
    story.append(Spacer(1, 30))
    
    # Employee Information Table
    emp_data = [
        ['Employee Name:', slip_data['employee_name'], 'Employee ID:', slip_data['employee_id']],
        ['Department:', slip_data['department'], 'Designation:', slip_data['designation']],
        ['Date of Joining:', slip_data['join_date'], 'Bank Account:', slip_data.get('account_number', 'N/A')],
        ['PAN Number:', slip_data.get('pan_number', 'N/A'), 'UAN Number:', slip_data.get('uan_number', 'N/A')]
    ]
    
    emp_table = Table(emp_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    emp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(emp_table)
    story.append(Spacer(1, 20))
    
    # Attendance Summary
    attendance_data = [
        ['ATTENDANCE SUMMARY'],
        ['Total Days in Month', '30'],
        ['Present Days', str(30 - slip_data['absent_days'])],
        ['Absent Days', str(slip_data['absent_days'])],
        ['Half Days', str(slip_data.get('half_days', 0))],
        ['Effective Working Days', f"{actual_working_days:.1f}"]
    ]
    
    attendance_table = Table(attendance_data, colWidths=[3*inch, 1.5*inch])
    attendance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(attendance_table)
    story.append(Spacer(1, 30))
    
    # Earnings and Deductions Table
    story.append(Paragraph("<b>EARNINGS & DEDUCTIONS</b>", section_style))
    
    # Calculate salary based on 30-day month standard
    # Per day earning = Monthly salary / 30
    total_monthly_salary = slip_data['base_salary'] + slip_data['hra'] + slip_data['allowances']
    per_day_earning = total_monthly_salary / 30
    
    # Calculate actual days worked (30 - absent_days - (half_days * 0.5))
    actual_working_days = 30 - slip_data['absent_days'] - (slip_data.get('half_days', 0) * 0.5)
    
    # Calculate proportional salary
    proportional_base = (slip_data['base_salary'] / 30) * actual_working_days
    proportional_hra = (slip_data['hra'] / 30) * actual_working_days
    proportional_allowances = (slip_data['allowances'] / 30) * actual_working_days
    
    gross_salary = proportional_base + proportional_hra + proportional_allowances
    
    # Deductions remain the same regardless of working days
    total_deductions = (slip_data['pf_deduction'] + slip_data['tax_deduction'] + 
                       slip_data['penalty_deductions'] + slip_data.get('other_deductions', 0))
    
    salary_data = [
        ['EARNINGS', 'FULL MONTH (₹)', 'PAYABLE (₹)', 'DEDUCTIONS', 'AMOUNT (₹)'],
        ['Basic Salary', f"{slip_data['base_salary']:,.2f}", f"{proportional_base:,.2f}", 'PF Contribution', f"{slip_data['pf_deduction']:,.2f}"],
        ['HRA', f"{slip_data['hra']:,.2f}", f"{proportional_hra:,.2f}", 'Tax Deduction (TDS)', f"{slip_data['tax_deduction']:,.2f}"],
        ['Other Allowances', f"{slip_data['allowances']:,.2f}", f"{proportional_allowances:,.2f}", 'Penalty Deductions', f"{slip_data['penalty_deductions']:,.2f}"],
        ['', '', '', 'Other Deductions', f"{slip_data.get('other_deductions', 0):,.2f}"],
        ['GROSS EARNINGS', f"{total_monthly_salary:,.2f}", f"{gross_salary:,.2f}", 'TOTAL DEDUCTIONS', f"{total_deductions:,.2f}"]
    ]
    
    salary_table = Table(salary_data, colWidths=[1.8*inch, 1.3*inch, 1.3*inch, 1.8*inch, 1.3*inch])
    salary_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        
        # Total rows
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        
        # General styling
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(salary_table)
    story.append(Spacer(1, 20))
    
    # Calculation Note
    calc_note = f"""
    <b>Salary Calculation:</b><br/>
    • Monthly salary is calculated based on 30 days standard<br/>
    • Per day rate: ₹{per_day_earning:,.2f} (Monthly Gross ÷ 30)<br/>
    • Payable amount = Per day rate × {actual_working_days:.1f} effective working days<br/>
    • Half days are counted as 0.5 days
    """
    
    story.append(Paragraph(calc_note, ParagraphStyle('CalcNote', parent=styles['Normal'], 
                                                   fontSize=9, textColor=colors.grey, 
                                                   leftIndent=20, rightIndent=20)))
    story.append(Spacer(1, 20))
    
    # Net Salary
    net_salary_data = [
        ['NET SALARY PAYABLE', f"₹ {slip_data['net_salary']:,.2f}"]
    ]
    
    net_table = Table(net_salary_data, colWidths=[4*inch, 3*inch])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 2, colors.darkgreen),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(net_table)
    story.append(Spacer(1, 40))
    
    # Footer
    story.append(Paragraph("This is a computer-generated salary slip and does not require a signature.", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, 
                                       alignment=TA_CENTER, textColor=colors.grey)))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                          ParagraphStyle('Generated', parent=styles['Normal'], fontSize=8, 
                                       alignment=TA_CENTER, textColor=colors.grey)))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def number_to_words(number: float) -> str:
    """Convert number to words (Indian format)"""
    # This is a simplified version - you can implement a more comprehensive one
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 
             'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def convert_hundreds(n):
        result = ''
        if n >= 100:
            result += ones[n // 100] + ' Hundred '
            n %= 100
        if n >= 20:
            result += tens[n // 10] + ' '
            n %= 10
        elif n >= 10:
            result += teens[n - 10] + ' '
            n = 0
        if n > 0:
            result += ones[n] + ' '
        return result
    
    if number == 0:
        return 'Zero'
    
    # Split into lakhs, thousands, and remainder
    lakhs = int(number // 100000)
    thousands = int((number % 100000) // 1000)
    remainder = int(number % 1000)
    
    result = ''
    if lakhs > 0:
        result += convert_hundreds(lakhs) + 'Lakh '
    if thousands > 0:
        result += convert_hundreds(thousands) + 'Thousand '
    if remainder > 0:
        result += convert_hundreds(remainder)
    
    return result.strip() + ' Rupees Only'
