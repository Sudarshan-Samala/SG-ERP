import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey, Boolean, Table, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association tables for RBAC
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
)

class TimeStampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class TenantMixin:
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

class AuditLog(Base, TimeStampMixin):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    previous_values = Column(String, nullable=True)
    new_values = Column(String, nullable=True)
class Organization(Base, TimeStampMixin):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)

    branches = relationship("Branch", back_populates="organization")
    users = relationship("User", back_populates="organization")

class Branch(Base, TimeStampMixin):
    __tablename__ = "branches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)

    organization = relationship("Organization")

    
    organization = relationship("Organization", back_populates="branches")
    users = relationship("User", secondary="user_branches", back_populates="branches")

class User(Base, TimeStampMixin):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    organization = relationship("Organization", back_populates="users")
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    branches = relationship("Branch", secondary="user_branches", back_populates="users")

user_branches = Table(
    "user_branches",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("branch_id", UUID(as_uuid=True), ForeignKey("branches.id"), primary_key=True),
)

class Role(Base, TimeStampMixin):
    __tablename__ = "roles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True) # Null for global roles
    name = Column(String, nullable=False)
    
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

class Permission(Base, TimeStampMixin):
    __tablename__ = "permissions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class AcademicYear(Base, TimeStampMixin):
    __tablename__ = "academic_years"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    organization = relationship("Organization")

class AdmissionEnquiry(Base, TimeStampMixin):
    __tablename__ = "admission_enquiries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    student_name = Column(String, nullable=False)
    parent_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    status = Column(String, default="ENQUIRY") # ENQUIRY, APPLIED, SELECTED, ADMITTED, REJECTED
    lead_source = Column(String)
    
    organization = relationship("Organization")
    branch = relationship("Branch")
    academic_year = relationship("AcademicYear")

class Student(Base, TimeStampMixin):
    __tablename__ = "students"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    academic_year_id = Column(UUID(as_uuid=True), ForeignKey("academic_years.id"), nullable=False)
    
    admission_number = Column(String, nullable=False, unique=True)
    student_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    
    # Relationships for tenant scoping
    organization = relationship("Organization")
    branch = relationship("Branch")
    academic_year = relationship("AcademicYear")

class Grade(Base, TimeStampMixin):
    __tablename__ = "grades"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    name = Column(String, nullable=False)

class Section(Base, TimeStampMixin):
    __tablename__ = "sections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False)
    name = Column(String, nullable=False)

class Subject(Base, TimeStampMixin):
    __tablename__ = "subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)

class Attendance(Base, TimeStampMixin):
    __tablename__ = "attendance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False) # PRESENT, ABSENT, LATE, etc.

class StaffAttendance(Base, TimeStampMixin):
    __tablename__ = "staff_attendance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    status = Column(String, nullable=False) # PRESENT, ABSENT, LATE, etc.

class TeacherAvailability(Base, TimeStampMixin):
    __tablename__ = "teacher_availability"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0-6
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

class Timetable(Base, TimeStampMixin):
    __tablename__ = "timetables"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False) # 0-6
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

class ExamType(Base, TimeStampMixin):
    __tablename__ = "exam_types"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)

class Exam(Base, TimeStampMixin):
    __tablename__ = "exams"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    exam_type_id = Column(UUID(as_uuid=True), ForeignKey("exam_types.id"), nullable=False)
    name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

class ExamSchedule(Base, TimeStampMixin):
    __tablename__ = "exam_schedules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    max_marks = Column(Integer, nullable=False)

class ExamResult(Base, TimeStampMixin):
    __tablename__ = "exam_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    marks_obtained = Column(Integer, nullable=False)

class FeeType(Base, TimeStampMixin):
    __tablename__ = "fee_types"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)

class FeeStructure(Base, TimeStampMixin):
    __tablename__ = "fee_structures"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False)
    fee_type_id = Column(UUID(as_uuid=True), ForeignKey("fee_types.id"), nullable=False)
    amount = Column(Integer, nullable=False)

class Invoice(Base, TimeStampMixin):
    __tablename__ = "invoices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    amount_due = Column(Integer, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False) # DRAFT, UNPAID, PAID, OVERDUE

class Payment(Base, TimeStampMixin):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    amount_paid = Column(Integer, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(String, nullable=False) # CASH, BANK, ONLINE

class Account(Base, TimeStampMixin):
    __tablename__ = "accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # ASSET, LIABILITY, INCOME, EXPENSE

class JournalEntry(Base, TimeStampMixin):
    __tablename__ = "journal_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    type = Column(String, nullable=False) # DEBIT, CREDIT

class Employee(Base, TimeStampMixin):
    __tablename__ = "employees"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    employee_id = Column(String, nullable=False, unique=True)
    department = Column(String, nullable=False)
    designation = Column(String, nullable=False)

class SalaryStructure(Base, TimeStampMixin):
    __tablename__ = "salary_structures"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    basic_salary = Column(Integer, nullable=False)
    hra = Column(Integer, nullable=False)

class Payroll(Base, TimeStampMixin):
    __tablename__ = "payrolls"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    net_salary = Column(Integer, nullable=False)

class Vehicle(Base, TimeStampMixin):
    __tablename__ = "vehicles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    number = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)

class Route(Base, TimeStampMixin):
    __tablename__ = "routes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)

class Driver(Base, TimeStampMixin):
    __tablename__ = "drivers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    license_number = Column(String, nullable=False)

class InventoryItem(Base, TimeStampMixin):
    __tablename__ = "inventory_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

class Asset(Base, TimeStampMixin):
    __tablename__ = "assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    asset_tag = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False) # DEPLOYED, REPAIR, DISPOSED

class Ticket(Base, TimeStampMixin):
    __tablename__ = "tickets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False) # OPEN, IN_PROGRESS, CLOSED
    priority = Column(String, nullable=False) # LOW, MEDIUM, HIGH

class NetworkConnection(Base, TimeStampMixin):
    __tablename__ = "network_connections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    isp_name = Column(String, nullable=False)
    plan_details = Column(String, nullable=True)
    bandwidth = Column(String, nullable=True)
    expiry_date = Column(DateTime, nullable=False)

class Facility(Base, TimeStampMixin):
    __tablename__ = "facilities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # CLASSROOM, LAB, OFFICE, BUILDING

class MaintenanceRequest(Base, TimeStampMixin):
    __tablename__ = "maintenance_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False) # OPEN, IN_PROGRESS, CLOSED

class Visitor(Base, TimeStampMixin):
    __tablename__ = "visitors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=True)

class SchoolEvent(Base, TimeStampMixin):
    __tablename__ = "school_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String, nullable=True)

class Communication(Base, TimeStampMixin):
    __tablename__ = "communications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    recipient_type = Column(String, nullable=False) # ALL, GRADE, BRANCH
    channel = Column(String, nullable=False) # SMS, EMAIL, WHATSAPP, IN_APP
    content = Column(String, nullable=False)
    status = Column(String, nullable=False) # SENT, FAILED

class Circular(Base, TimeStampMixin):
    __tablename__ = "circulars"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Document(Base, TimeStampMixin):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    category = Column(String, nullable=False) # POLICY, CERTIFICATE, CONTRACT
