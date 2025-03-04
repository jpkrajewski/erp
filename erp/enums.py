from enum import Enum

class EmployeeRole(Enum):
    PRODUCTION_WORKER = "Production Worker"
    MACHINE_OPERATOR = "Machine Operator"
    QUALITY_INSPECTOR = "Quality Inspector"
    SHIFT_SUPERVISOR = "Shift Supervisor"
    MAINTENANCE_TECHNICIAN = "Maintenance Technician"
    PRODUCTION_PLANNER = "Production Planner"
    WAREHOUSE_ASSOCIATE = "Warehouse Associate"
    TEAM_LEAD = "Team Lead"

class EmployeeDepartment(Enum):
    PRODUCTION = "Production"
    QUALITY_CONTROL = "Quality Control"
    MAINTENANCE = "Maintenance"
    LOGISTICS = "Logistics"
    PLANNING = "Planning"
