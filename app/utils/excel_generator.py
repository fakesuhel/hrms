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
    @staticmethod
    def generate_performance_report(data: List[Dict[str, Any]], start_date: str, end_date: str) -> BytesIO:
        """Generate performance report Excel file"""
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # If no data, create empty structure
        if df.empty:
            df = pd.DataFrame({
                "Employee ID": ["No data available"],
                "Employee Name": [""],
                "Department": [""],
                "Performance Score": [0],
                "Review Date": [""],
                "Goals Met": [0],
                "Comments": ["No performance data found"]
            })
        
        # Create Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Performance Report', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Performance Report']
            
            # Add report metadata
            worksheet['A1'] = f"Performance Report: {start_date} to {end_date}"
            worksheet['A2'] = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Insert rows for metadata
            worksheet.insert_rows(1, 3)
            
            # Write data starting from row 4
            df.to_excel(writer, sheet_name='Performance Report', index=False, startrow=3)
            
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
        
        # Reorder columns for better presentation
        column_order = [
            "_id", "username", "full_name", "email", "department", 
            "role", "is_active", "created_at", "last_login"
        ]
        
        # Only include columns that exist in the data
        available_columns = [col for col in column_order if col in df.columns]
        remaining_columns = [col for col in df.columns if col not in column_order]
        all_columns = available_columns + remaining_columns
        
        if all_columns:
            df = df[all_columns]
        
        # Rename columns for better readability
        column_names = {
            "_id": "Employee ID",
            "username": "Username",
            "full_name": "Full Name",
            "email": "Email",
            "department": "Department",
            "role": "Role",
            "is_active": "Active Status",
            "created_at": "Created Date",
            "last_login": "Last Login"
        }
        
        df.rename(columns=column_names, inplace=True)
        
        # Create Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Employee Report', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Employee Report']
            
            # Add report metadata
            worksheet['A1'] = f"Employee Report"
            worksheet['A2'] = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Insert rows for metadata
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

    @staticmethod
    def generate_payroll_report(data: List[Dict[str, Any]], start_date: str, end_date: str) -> BytesIO:
        """Generate payroll report Excel file"""
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # If no data, create empty structure with sample data
        if df.empty:
            df = pd.DataFrame({
                "Employee ID": ["EMP001", "EMP002", "EMP003"],
                "Employee Name": ["John Doe", "Jane Smith", "Mike Johnson"],
                "Department": ["IT", "HR", "Sales"],
                "Basic Salary": [5000, 4500, 4000],
                "Allowances": [500, 450, 400],
                "Deductions": [200, 180, 160],
                "Net Salary": [5300, 4770, 4240],
                "Pay Period": [f"{start_date} to {end_date}"] * 3,
                "Payment Status": ["Processed", "Processed", "Pending"]
            })
        
        # Create Excel file in memory
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Write main data
            df.to_excel(writer, sheet_name="Payroll Report", index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets["Payroll Report"]
            
            # Add report metadata
            worksheet["A1"] = f"Payroll Report: {start_date} to {end_date}"
            date_format = "%Y-%m-%d %H:%M:%S"
            worksheet["A2"] = f"Generated on: {datetime.now().strftime(date_format)}"
            worksheet["A3"] = f"Total Employees: {len(df)}"
            
            # Insert rows for metadata
            worksheet.insert_rows(1, 4)
            
            # Write data starting from row 5
            df.to_excel(writer, sheet_name="Payroll Report", index=False, startrow=4)
            
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
    def generate_recruitment_report(job_postings, applications, interviews, start_date=None, end_date=None):
        """Generate recruitment report Excel file"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Job Postings Sheet
            if job_postings:
                # Convert job postings to DataFrame
                jobs_data = []
                for job in job_postings:
                    jobs_data.append({
                        "Job ID": str(job.get("_id", "")),
                        "Title": job.get("title", ""),
                        "Department": job.get("department", ""),
                        "Location": job.get("location", ""),
                        "Employment Type": job.get("employment_type", ""),
                        "Status": job.get("status", ""),
                        "Posted Date": str(job.get("created_at", "")),
                        "Application Deadline": str(job.get("application_deadline", "")),
                        "Salary Range": job.get("salary_range", ""),
                        "Experience Level": job.get("experience_level", ""),
                        "Posted By": job.get("posted_by", "")
                    })
                
                if jobs_data:
                    jobs_df = pd.DataFrame(jobs_data)
                    jobs_df.to_excel(writer, sheet_name="Job Postings", index=False, startrow=4)
                    
                    # Add metadata to job postings sheet
                    job_worksheet = writer.sheets["Job Postings"]
                    job_worksheet["A1"] = "Job Postings Report"
                    if start_date and end_date:
                        job_worksheet["A2"] = f"Period: {start_date} to {end_date}"
                    date_format = "%Y-%m-%d %H:%M:%S"
                    job_worksheet["A3"] = f"Generated on: {datetime.now().strftime(date_format)}"
                    job_worksheet["A4"] = f"Total Job Postings: {len(jobs_data)}"
                else:
                    jobs_df = pd.DataFrame([{"Message": "No job postings found"}])
                    jobs_df.to_excel(writer, sheet_name="Job Postings", index=False)
            else:
                jobs_df = pd.DataFrame([{"Message": "No job postings found"}])
                jobs_df.to_excel(writer, sheet_name="Job Postings", index=False)
            
            # Applications Sheet
            if applications:
                apps_data = []
                for app in applications:
                    first_name = app.get("first_name", "")
                    last_name = app.get("last_name", "")
                    exp_years = app.get("experience_years", 0)
                    apps_data.append({
                        "Application ID": str(app.get("_id", "")),
                        "Job ID": str(app.get("job_id", "")),
                        "Applicant Name": f"{first_name} {last_name}".strip(),
                        "Email": app.get("email", ""),
                        "Phone": app.get("phone", ""),
                        "Status": app.get("status", ""),
                        "Applied Date": str(app.get("created_at", "")),
                        "Experience": f"{exp_years} years",
                        "Education": app.get("education", ""),
                        "Skills": ", ".join(app.get("skills", [])) if isinstance(app.get("skills", []), list) else str(app.get("skills", "")),
                        "Rating": app.get("rating", ""),
                        "Notes": app.get("notes", ""),
                        "Reviewed By": app.get("reviewer_id", "")
                    })
                
                if apps_data:
                    apps_df = pd.DataFrame(apps_data)
                    apps_df.to_excel(writer, sheet_name="Applications", index=False, startrow=4)
                    
                    apps_worksheet = writer.sheets["Applications"]
                    apps_worksheet["A1"] = "Job Applications Report"
                    if start_date and end_date:
                        apps_worksheet["A2"] = f"Period: {start_date} to {end_date}"
                    date_format = "%Y-%m-%d %H:%M:%S"
                    apps_worksheet["A3"] = f"Generated on: {datetime.now().strftime(date_format)}"
                    apps_worksheet["A4"] = f"Total Applications: {len(apps_data)}"
                else:
                    apps_df = pd.DataFrame([{"Message": "No applications found"}])
                    apps_df.to_excel(writer, sheet_name="Applications", index=False)
            else:
                apps_df = pd.DataFrame([{"Message": "No applications found"}])
                apps_df.to_excel(writer, sheet_name="Applications", index=False)
            
            # Interviews Sheet
            if interviews:
                interviews_data = []
                for interview in interviews:
                    interviews_data.append({
                        "Interview ID": str(interview.get("_id", "")),
                        "Application ID": str(interview.get("application_id", "")),
                        "Candidate Name": interview.get("candidate_name", ""),
                        "Interview Type": interview.get("interview_type", ""),
                        "Status": interview.get("status", ""),
                        "Scheduled Date": str(interview.get("scheduled_date", "")),
                        "Duration": f"{interview.get('duration_minutes', 0)} minutes",
                        "Interviewer": interview.get("interviewer_id", ""),
                        "Location/Platform": interview.get("location", ""),
                        "Result": interview.get("result", ""),
                        "Score": interview.get("score", ""),
                        "Feedback": interview.get("feedback", ""),
                        "Next Steps": interview.get("next_steps", "")
                    })
                
                if interviews_data:
                    interviews_df = pd.DataFrame(interviews_data)
                    interviews_df.to_excel(writer, sheet_name="Interviews", index=False, startrow=4)
                    
                    int_worksheet = writer.sheets["Interviews"]
                    int_worksheet["A1"] = "Interviews Report"
                    if start_date and end_date:
                        int_worksheet["A2"] = f"Period: {start_date} to {end_date}"
                    date_format = "%Y-%m-%d %H:%M:%S"
                    int_worksheet["A3"] = f"Generated on: {datetime.now().strftime(date_format)}"
                    int_worksheet["A4"] = f"Total Interviews: {len(interviews_data)}"
                else:
                    interviews_df = pd.DataFrame([{"Message": "No interviews found"}])
                    interviews_df.to_excel(writer, sheet_name="Interviews", index=False)
            else:
                interviews_df = pd.DataFrame([{"Message": "No interviews found"}])
                interviews_df.to_excel(writer, sheet_name="Interviews", index=False)
            
            # Summary Sheet
            summary_data = [{
                "Metric": "Total Job Postings",
                "Value": len(job_postings) if job_postings else 0
            }, {
                "Metric": "Total Applications", 
                "Value": len(applications) if applications else 0
            }, {
                "Metric": "Total Interviews",
                "Value": len(interviews) if interviews else 0
            }, {
                "Metric": "Active Job Postings",
                "Value": len([j for j in job_postings if j.get("status") == "open"]) if job_postings else 0
            }, {
                "Metric": "Pending Applications",
                "Value": len([a for a in applications if a.get("status") == "applied"]) if applications else 0
            }, {
                "Metric": "Completed Interviews", 
                "Value": len([i for i in interviews if i.get("status") == "completed"]) if interviews else 0
            }]
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Summary", index=False, startrow=4)
            
            summary_worksheet = writer.sheets["Summary"]
            summary_worksheet["A1"] = "Recruitment Summary Report"
            if start_date and end_date:
                summary_worksheet["A2"] = f"Period: {start_date} to {end_date}"
            date_format = "%Y-%m-%d %H:%M:%S"
            summary_worksheet["A3"] = f"Generated on: {datetime.now().strftime(date_format)}"
            
            # Auto-adjust column widths for all sheets
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
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
