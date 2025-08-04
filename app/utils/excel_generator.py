import pandas as pd
from io import BytesIO
from typing import List, Dict, Any
from datetime import datetime

class ExcelReportGenerator:
    """Utility class for generating Excel reports"""
    
    @staticmethod
    def generate_attendance_report(data: List[Dict[str, Any]], start_date: str, end_date: str) -> BytesIO:
        """Generate attendance report Excel file"""
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Standardize column names - handle both 'name' and 'employee_name'
        if 'name' in df.columns and 'employee_name' not in df.columns:
            df['employee_name'] = df['name']
        elif 'employee_name' in df.columns and 'name' not in df.columns:
            df['name'] = df['employee_name']
        
        # Reorder columns for better presentation
        column_order = [
            "employee_id", "employee_name", "department", "email",
            "present_days", "absent_days", "late_days", "total_days", 
            "attendance_percentage", "total_work_hours"
        ]
        
        # Only include columns that exist in the data
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]
        
        # Rename columns for better readability
        column_names = {
            "employee_id": "Employee ID",
            "employee_name": "Employee Name", 
            "department": "Department",
            "email": "Email",
            "present_days": "Present Days",
            "absent_days": "Absent Days",
            "late_days": "Late Days",
            "total_days": "Total Days",
            "attendance_percentage": "Attendance %",
            "total_work_hours": "Total Hours"
        }
        
        df.rename(columns=column_names, inplace=True)
        
        # Create Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Attendance Report', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Attendance Report']
            
            # Add report metadata
            worksheet['A1'] = f'Attendance Report ({start_date} to {end_date})'
            worksheet['A2'] = f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
            # Move data down to make room for headers
            worksheet.insert_rows(1, 3)
            
            # Write data starting from row 4
            df.to_excel(writer, sheet_name='Attendance Report', index=False, startrow=3)
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    
    @staticmethod
    def generate_leave_report(data: List[Dict[str, Any]], start_date: str, end_date: str) -> BytesIO:
        """Generate leave report Excel file"""
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Reorder columns for better presentation
        column_order = [
            "employee_id", "name", "department", "email",
            "total_requests", "approved_requests", "pending_requests", "rejected_requests",
            "total_leave_days", "leave_balance"
        ]
        
        # Only include columns that exist in the data
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]
        
        # Rename columns for better readability
        column_names = {
            "employee_id": "Employee ID",
            "name": "Employee Name",
            "department": "Department", 
            "email": "Email",
            "total_requests": "Total Requests",
            "approved_requests": "Approved",
            "pending_requests": "Pending",
            "rejected_requests": "Rejected",
            "total_leave_days": "Leave Days Used",
            "leave_balance": "Leave Balance"
        }
        
        df.rename(columns=column_names, inplace=True)
        
        # Create Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Leave Report', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Leave Report']
            
            # Add report metadata
            worksheet['A1'] = f'Leave Report ({start_date} to {end_date})'
            worksheet['A2'] = f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
            # Move data down to make room for headers
            worksheet.insert_rows(1, 3)
            
            # Write data starting from row 4
            df.to_excel(writer, sheet_name='Leave Report', index=False, startrow=3)
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
    
    @staticmethod
    def generate_employee_report(data: List[Dict[str, Any]]) -> BytesIO:
        """Generate employee report Excel file"""
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Employee Report', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Employee Report']
            
            # Add report metadata
            worksheet['A1'] = 'Employee Report'
            worksheet['A2'] = f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
            # Move data down to make room for headers
            worksheet.insert_rows(1, 3)
            
            # Write data starting from row 4
            df.to_excel(writer, sheet_name='Employee Report', index=False, startrow=3)
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return output
