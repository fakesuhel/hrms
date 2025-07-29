from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
import os
import shutil
import zipfile
import io
from datetime import datetime, timezone, timedelta
from app.database.users import DatabaseUsers, UserUpdate, UserInDB
from app.database.documents import DatabaseDocuments, DocumentCreate, DocumentResponse
from app.database.salary_slips import DatabaseSalarySlips, SalarySlipResponse
from app.utils.auth import get_current_user
from app.utils.helpers import generate_filename, allowed_file_extension, create_directory_if_not_exists
import uuid

router = APIRouter()

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Get current datetime in IST timezone"""
    return datetime.now()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
DOCUMENTS_DIR = os.path.join(UPLOAD_DIR, "documents")
create_directory_if_not_exists(DOCUMENTS_DIR)

@router.get("/profile")
async def get_profile(current_user: UserInDB = Depends(get_current_user)):
    """Get current user's profile information"""
    # Generate full_name from first_name and last_name
    full_name = ""
    if hasattr(current_user, 'first_name') and current_user.first_name:
        full_name = current_user.first_name
    if hasattr(current_user, 'last_name') and current_user.last_name:
        full_name = f"{full_name} {current_user.last_name}".strip()
    if not full_name and hasattr(current_user, 'display_name') and current_user.display_name:
        full_name = current_user.display_name
    if not full_name:
        full_name = current_user.username
    
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": full_name,
        "first_name": getattr(current_user, 'first_name', None),
        "last_name": getattr(current_user, 'last_name', None),
        "phone_number": getattr(current_user, 'phone', None),
        "date_of_birth": getattr(current_user, 'birthday', None),
        "gender": getattr(current_user, 'gender', None),
        "address": getattr(current_user, 'address', None),
        "city": getattr(current_user, 'city', None),
        "state": getattr(current_user, 'state', None),
        "pincode": getattr(current_user, 'zip_code', None),
        "country": getattr(current_user, 'country', None),
        "bank_name": getattr(current_user, 'bank_name', None),
        "account_number": getattr(current_user, 'account_number', None),
        "ifsc_code": getattr(current_user, 'ifsc_code', None),
        "pan_number": getattr(current_user, 'pan_number', None),
        "aadhar_number": getattr(current_user, 'aadhar_number', None),
        "uan_number": getattr(current_user, 'uan_number', None),
        "employee_id": getattr(current_user, 'employee_id', None),
        "department": getattr(current_user, 'department', None),
        "designation": getattr(current_user, 'position', None),
        "position": getattr(current_user, 'position', None),
        "employment_type": getattr(current_user, 'employment_type', None),
        "join_date": getattr(current_user, 'joining_date', None),
        "reporting_to": getattr(current_user, 'manager_id', None),
        "performance_incentives": getattr(current_user, 'performance_incentives', None),
        "base_salary": getattr(current_user, 'salary', None),
        "hra": getattr(current_user, 'hra', None),
        "allowances": getattr(current_user, 'allowances', None),
        "pf_deduction": getattr(current_user, 'pf_deduction', None),
        "tax_deduction": getattr(current_user, 'tax_deduction', None),
        "penalty_deductions": getattr(current_user, 'penalty_deductions', None),
        "net_salary": getattr(current_user, 'net_salary', None),
        "role": current_user.role,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }

@router.put("/profile")
async def update_profile(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update current user's profile information"""
    try:
        # Get the raw JSON data from request
        profile_data = await request.json()
        
        # Map frontend field names to backend field names
        field_mapping = {
            'full_name': None,  # Will be split into first_name and last_name
            'phone_number': 'phone',
            'date_of_birth': 'birthday',
            'pincode': 'zip_code',
            'join_date': 'joining_date',
            'reporting_to': 'manager_id'
        }
        
        update_data = {}
        
        # Handle full_name splitting
        if 'full_name' in profile_data and profile_data['full_name']:
            names = profile_data['full_name'].strip().split(' ', 1)
            update_data['first_name'] = names[0]
            if len(names) > 1:
                update_data['last_name'] = names[1]
            else:
                update_data['last_name'] = ''
        
        # Map other fields
        for frontend_field, backend_field in field_mapping.items():
            if frontend_field in profile_data and backend_field:
                update_data[backend_field] = profile_data[frontend_field]
        
        # Copy fields that have the same name
        direct_fields = [
            'email', 'gender', 'address', 'city', 'state', 'country',
            'bank_name', 'account_number', 'ifsc_code', 'pan_number',
            'aadhar_number', 'uan_number', 'department', 'position',
            'employment_type', 'base_salary', 'hra', 'allowances',
            'performance_incentives', 'pf_deduction', 'tax_deduction',
            'penalty_deductions'
        ]
        
        for field in direct_fields:
            if field in profile_data:
                value = profile_data[field]
                # Convert empty strings to None for optional fields
                if value == '':
                    value = None
                # Convert salary strings to float
                elif field in ['base_salary', 'hra', 'allowances', 'performance_incentives', 
                              'pf_deduction', 'tax_deduction', 'penalty_deductions'] and value:
                    try:
                        # Remove currency symbols and commas
                        if isinstance(value, str):
                            value = value.replace('₹', '').replace(',', '').strip()
                        value = float(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                update_data[field] = value
        
        # Calculate net salary if salary components are updated
        salary_fields = ['base_salary', 'hra', 'allowances', 'performance_incentives', 
                        'pf_deduction', 'tax_deduction', 'penalty_deductions']
        if any(field in update_data for field in salary_fields):
            base = update_data.get('base_salary') or getattr(current_user, 'base_salary', 0) or 0
            hra = update_data.get('hra') or getattr(current_user, 'hra', 0) or 0
            allowances = update_data.get('allowances') or getattr(current_user, 'allowances', 0) or 0
            incentives = update_data.get('performance_incentives') or getattr(current_user, 'performance_incentives', 0) or 0
            pf = update_data.get('pf_deduction') or getattr(current_user, 'pf_deduction', 0) or 0
            tax = update_data.get('tax_deduction') or getattr(current_user, 'tax_deduction', 0) or 0
            penalty = update_data.get('penalty_deductions') or getattr(current_user, 'penalty_deductions', 0) or 0
            
            gross_salary = base + hra + allowances + incentives
            total_deductions = pf + tax + penalty
            update_data['net_salary'] = gross_salary - total_deductions
        
        # Create UserUpdate object
        user_update = UserUpdate(**update_data)
        
        updated_user = await DatabaseUsers.update_user(str(current_user.id), user_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "Profile updated successfully"}
    except Exception as e:
        print(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    category: str = Form(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """Upload a document for the current user"""
    try:
        # Validate file extension
        if not allowed_file_extension(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only PDF, JPG, JPEG, PNG files are allowed."
            )
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1].lower()
        stored_filename = f"{current_user.employee_id}_{document_type}_{uuid.uuid4().hex}{file_extension}"
        
        # Create category directory
        category_dir = os.path.join(DOCUMENTS_DIR, str(current_user.id), category)
        create_directory_if_not_exists(category_dir)
        
        # Save file
        file_path = os.path.join(category_dir, stored_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Save document info to database
        document_data = DocumentCreate(
            user_id=str(current_user.id),
            document_type=document_type,
            category=category,
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_size=file_size,
            file_extension=file_extension,
            mime_type=file.content_type
        )
        
        document = await DatabaseDocuments.create_document(document_data)
        
        # Convert ObjectId to string for response
        document_dict = document.model_dump()
        # Handle _id field properly
        if "_id" in document_dict:
            document_dict["id"] = str(document_dict["_id"])
            document_dict.pop("_id", None)
        elif hasattr(document, "_id"):
            document_dict["id"] = str(document._id)
        else:
            # Fallback to generate an id if none exists
            document_dict["id"] = str(document_dict.get("id", ""))
        
        return {
            "message": "Document uploaded successfully",
            "document": document_dict
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents")
async def get_documents(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get all documents for the current user"""
    try:
        # Get documents directly from database without using DocumentInDB
        query = {"user_id": str(current_user.id)}
        if category:
            query["category"] = category
        
        from app.database import db
        documents_collection = db["documents"]
        documents = list(documents_collection.find(query).sort("created_at", -1))
        
        # Convert to response format
        documents_list = []
        for doc in documents:
            # Convert ObjectId to string for response
            doc_response = {
                "id": str(doc["_id"]),
                "user_id": doc.get("user_id", ""),
                "document_type": doc.get("document_type", ""),
                "category": doc.get("category", ""),
                "original_filename": doc.get("original_filename", ""),
                "stored_filename": doc.get("stored_filename", ""),
                "file_size": doc.get("file_size", 0),
                "file_extension": doc.get("file_extension", ""),
                "mime_type": doc.get("mime_type", ""),
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at")
            }
            documents_list.append(doc_response)
        
        return {
            "documents": documents_list
        }
    except Exception as e:
        print(f"Error in get_documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/categories")
async def get_document_categories(current_user: UserInDB = Depends(get_current_user)):
    """Get document categories with counts"""
    try:
        # Get documents directly from database without using DocumentInDB
        from app.database import db
        documents_collection = db["documents"]
        documents = list(documents_collection.find({"user_id": str(current_user.id)}))
        
        # Count documents by category
        categories = {
            "identity": 0,
            "education": 0,
            "employment": 0,
            "other": 0
        }
        
        for doc in documents:
            category = doc.get("category", "other")
            if category in categories:
                categories[category] += 1
            else:
                categories["other"] += 1
        
        return {"counts": categories}
    except Exception as e:
        print(f"Error in get_document_categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """Download a specific document"""
    try:
        document = await DatabaseDocuments.get_document_by_id(document_id)
        if not document or document.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = os.path.join(DOCUMENTS_DIR, str(current_user.id), document.category, document.stored_filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return FileResponse(
            path=file_path,
            filename=document.original_filename,
            media_type=document.mime_type
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete a specific document"""
    try:
        document = await DatabaseDocuments.get_document_by_id(document_id)
        if not document or document.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete file from disk
        file_path = os.path.join(DOCUMENTS_DIR, str(current_user.id), document.category, document.stored_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database
        success = await DatabaseDocuments.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Failed to delete document")
        
        return {"message": "Document deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/download-all")
async def download_all_documents(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """Download all documents as a ZIP file"""
    try:
        documents = await DatabaseDocuments.get_user_documents(str(current_user.id))
        
        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for document in documents:
                file_path = os.path.join(DOCUMENTS_DIR, str(current_user.id), document.category, document.stored_filename)
                if os.path.exists(file_path):
                    # Add file to ZIP with organized folder structure
                    zip_path = f"{document.category}/{document.original_filename}"
                    zip_file.write(file_path, zip_path)
        
        zip_buffer.seek(0)
        
        # Return ZIP file as streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={current_user.employee_id}_documents.zip"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/salary-slips")
async def get_salary_slips(current_user: UserInDB = Depends(get_current_user)):
    """Get salary slips for the current user"""
    try:
        slips = await DatabaseSalarySlips.get_user_salary_slips(str(current_user.id))
        return {
            "salary_slips": [SalarySlipResponse(**slip.model_dump()) for slip in slips]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/salary-slips/{slip_id}/download")
async def download_salary_slip(
    slip_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """Download salary slip as PDF"""
    try:
        slip = await DatabaseSalarySlips.get_salary_slip_by_id(slip_id)
        if not slip or slip.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Salary slip not found")
        
        # Generate PDF (we'll implement this function)
        pdf_content = await generate_salary_slip_pdf(slip)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=salary_slip_{slip.month}_{slip.year}_{current_user.employee_id}.pdf"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/salary-slips/current")
async def download_current_salary_slip(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """Download current month's salary slip"""
    try:
        now = get_ist_now()
        slip = await DatabaseSalarySlips.get_salary_slip_by_month_year(
            str(current_user.id), now.month, now.year
        )
        
        if not slip:
            raise HTTPException(status_code=404, detail="Current month's salary slip not found")
        
        pdf_content = await generate_salary_slip_pdf(slip)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=salary_slip_{now.month}_{now.year}_{current_user.employee_id}.pdf"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# PDF Generation function
async def generate_salary_slip_pdf(slip) -> bytes:
    """Generate PDF content for salary slip"""
    from app.utils.pdf_generator import generate_salary_slip_pdf as pdf_gen
    
    # Convert slip object to dictionary
    slip_dict = {
        'employee_name': slip.employee_name,
        'employee_id': slip.employee_id,
        'department': slip.department,
        'designation': slip.designation,
        'join_date': slip.join_date,
        'month': slip.month,
        'year': slip.year,
        'base_salary': slip.base_salary,
        'hra': slip.hra,
        'allowances': slip.allowances,
        'pf_deduction': slip.pf_deduction,
        'tax_deduction': slip.tax_deduction,
        'penalty_deductions': slip.penalty_deductions,
        'other_deductions': slip.other_deductions,
        'net_salary': slip.net_salary,
        'working_days': slip.working_days,
        'present_days': slip.present_days,
        'absent_days': slip.absent_days
    }
    
    return await pdf_gen(slip_dict)

# Postal code API integration
@router.get("/postal-code/{pincode}")
async def get_postal_info(pincode: str):
    """Get city and state info from pincode using Indian Postal API"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.postalpincode.in/pincode/{pincode}")
            data = response.json()
            
            if data and len(data) > 0 and data[0]["Status"] == "Success":
                post_office = data[0]["PostOffice"][0]
                
                # Get all cities/areas for this pincode
                cities = []
                for office in data[0]["PostOffice"]:
                    cities.append({
                        "name": office["Name"],
                        "district": office["District"],
                        "state": office["State"]
                    })
                
                return {
                    "success": True,
                    "pincode": pincode,
                    "state": post_office["State"],
                    "district": post_office["District"],
                    "country": post_office["Country"],
                    "cities": cities,
                    "primary_city": post_office["Name"]
                }
            else:
                raise HTTPException(status_code=404, detail="Invalid pincode or no data found")
    
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Postal service temporarily unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching postal info: {str(e)}")

@router.get("/states")
async def get_indian_states():
    """Get list of Indian states"""
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
        "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
        "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
        "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
    ]
    return {"states": sorted(states)}
