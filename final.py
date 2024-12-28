from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from fastapi.middleware.cors import CORSMiddleware


# Initialize FastAPI
app = FastAPI()

# CORS settings
origins = [
    "http://localhost",  # Allow requests from your local machine
    "http://127.0.0.1:5500",  # Add this if you're using a local server for HTML testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = 'mysql+pymysql://root@localhost:3306/testdb2'  # Replace with your database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Association table for many-to-many
project_employee_table = Table(
    'project_employee', Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
    Column('employee_id', Integer, ForeignKey('employees.id'), primary_key=True)
)

# Define Employee model
class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    projects = relationship('Project', secondary=project_employee_table, back_populates='employees')

# Define Project model
class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    employees = relationship('Employee', secondary=project_employee_table, back_populates='projects')

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to handle database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/employees/")
def create_employee(employee: dict = Body(...), db: Session = Depends(get_db)):
    name = employee.get("name")
    role = employee.get("role")
    if not name or not role:
        raise HTTPException(status_code=400, detail="Name and role are required")
    new_employee = Employee(name=name, role=role)
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return {"id": new_employee.id, "name": new_employee.name, "role": new_employee.role}

@app.post("/projects/")
def create_project(project: dict = Body(...), db: Session = Depends(get_db)):
    name = project.get("name")
    description = project.get("description")
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    new_project = Project(name=name, description=description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {"id": new_project.id, "name": new_project.name, "description": new_project.description}

@app.post("/assign/")
def assign_employee_to_project(assignment: dict = Body(...), db: Session = Depends(get_db)):
    project_id = assignment.get("project_id")
    employee_id = assignment.get("employee_id")
    if not project_id or not employee_id:
        raise HTTPException(status_code=400, detail="Project ID and Employee ID are required")
    project = db.query(Project).filter_by(id=project_id).first()
    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not project or not employee:
        raise HTTPException(status_code=404, detail="Project or Employee not found")
    project.employees.append(employee)
    db.commit()
    return {"message": "Employee assigned to Project successfully"}

@app.get("/employees/")
def get_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    result = [{"id": employee.id, "name": employee.name, "role": employee.role, "projects": [project.name for project in employee.projects]} for employee in employees]
    return result

@app.get("/projects/")
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    result = [{"id": project.id, "name": project.name, "description": project.description, "employees": [employee.name for employee in project.employees]} for project in projects]
    return result

@app.get("/assignments/")
def get_assignments(db: Session = Depends(get_db)):
    assignments = db.query(project_employee_table).all()
    result = [{"project_id": assignment.project_id, "employee_id": assignment.employee_id} for assignment in assignments]
    return result

@app.put("/employees/{employee_id}")
def update_employee(employee_id: int, employee_data: dict = Body(...), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    name = employee_data.get("name")
    role = employee_data.get("role")
    if name:
        employee.name = name
    if role:
        employee.role = role
    db.commit()
    db.refresh(employee)
    return {"id": employee.id, "name": employee.name, "role": employee.role}

@app.patch("/employees/{employee_id}")
def patch_employee(employee_id: int, employee_data: dict = Body(...), db: Session = Depends(get_db)):
    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if "name" in employee_data:
        employee.name = employee_data["name"]
    if "role" in employee_data:
        employee.role = employee_data["role"]
    db.commit()
    db.refresh(employee)
    return {"id": employee.id, "name": employee.name, "role": employee.role}


@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter_by(id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted successfully"}

@app.put("/projects/{project_id}")
def update_project(project_id: int, project_data: dict = Body(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    name = project_data.get("name")
    description = project_data.get("description")
    if name:
        project.name = name
    if description:
        project.description = description
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name, "description": project.description}

@app.patch("/projects/{project_id}")
def patch_project(project_id: int, project_data: dict = Body(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if "name" in project_data:
        project.name = project_data["name"]
    if "description" in project_data:
        project.description = project_data["description"]
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name, "description": project.description}

@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}

