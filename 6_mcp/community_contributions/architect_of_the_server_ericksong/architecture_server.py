from mcp.server.fastmcp import FastMCP
from datetime import datetime
from typing import Dict, List

# ============================================================================
# THE ARCHITECT OF THE SERVER
# By ERICKSONG ARCHITECTS INC.
# 
# The first MCP server built specifically for architecture and construction.
# Provides AI-powered building code compliance, material estimation, and
# architectural calculations for AI agent workflows.
# ============================================================================

mcp = FastMCP("architecture_server")

# Building codes database (IBC standards)
# In production, this would connect to a comprehensive code database
# NOTE: All requirements below are based on IBC 2018 (example). Add more versions as needed.
BUILDING_CODES = {
    "IBC_2018": {
        "residential": {
            "bedroom": {
                "min_area_sqft": 70,
                "min_ceiling_height_ft": 7.5,
                "min_width_ft": 7.0,
                "window_area_ratio": 0.08
            },
            "living_room": {
                "min_area_sqft": 120,
                "min_ceiling_height_ft": 7.5
            },
            "bathroom": {
                "min_area_sqft": 35,
                "min_ceiling_height_ft": 7.5
            },
            "kitchen": {
                "min_area_sqft": 50,
                "min_ceiling_height_ft": 7.5
            }
        },
        "commercial": {
            "office": {
                "min_area_sqft": 100,
                "min_ceiling_height_ft": 8.0,
                "occupancy_sqft_per_person": 100
            },
            "corridor": {
                "min_width_inches": 44,
                "min_ceiling_height_ft": 8.0,
                "exit_access_width_inches": 36
            },
            "stair": {
                "min_width_inches": 36,
                "min_ceiling_height_ft": 7.0,
                "max_riser_height_inches": 7.0,
                "min_tread_depth_inches": 11.0
            }
        }
    }
}

# In-memory project storage (use database in production)
# NOTE: PROJECTS is shared mutable state. If the server is run with concurrent requests,
# access to PROJECTS must be synchronized to avoid race conditions.
import threading
PROJECTS_LOCK = threading.Lock()
PROJECTS = {}

# ============================================================================
# CALCULATION TOOLS
# ============================================================================

@mcp.tool()
async def calculate_area(length: float, width: float, unit: str = "feet") -> Dict:
    """Calculate the area of a rectangular space with unit conversion.
    
    Supports imperial (feet, inches) and metric (meters) units.
    Perfect for quick room area calculations.
    
    Args:
        length: Length dimension
        width: Width dimension
        unit: "feet", "meters", or "inches"
    
    Returns:
        Area in both square feet and square meters
    """
    area = length * width
    
    # Convert to both imperial and metric
    if unit == "feet":
        area_sqft = area
        area_sqm = area * 0.092903
    elif unit == "meters":
        area_sqm = area
        area_sqft = area * 10.7639
    else:  # inches
        area_sqft = area / 144
        area_sqm = area_sqft * 0.092903
    
    return {
        "area_sqft": round(area_sqft, 2),
        "area_sqm": round(area_sqm, 2),
        "dimensions": f"{length} x {width} {unit}",
        "calculated_at": datetime.now().isoformat()
    }

@mcp.tool()
async def calculate_volume(length: float, width: float, height: float, unit: str = "feet") -> Dict:
    """Calculate the volume of a rectangular space.
    
    Useful for HVAC sizing, acoustic calculations, and volume requirements.
    
    Args:
        length: Length dimension
        width: Width dimension
        height: Height dimension
        unit: "feet" or "meters"
    
    Returns:
        Volume in both cubic feet and cubic meters
    """
    volume = length * width * height
    
    if unit == "feet":
        volume_cuft = volume
        volume_cum = volume * 0.0283168
    else:  # meters
        volume_cum = volume
        volume_cuft = volume * 35.3147
    
    return {
        "volume_cuft": round(volume_cuft, 2),
        "volume_cum": round(volume_cum, 2),
        "dimensions": f"{length} x {width} x {height} {unit}",
        "calculated_at": datetime.now().isoformat()
    }

# ============================================================================
# BUILDING CODE COMPLIANCE TOOLS
# ============================================================================

@mcp.tool()
async def lookup_building_code(building_type: str, space_type: str) -> Dict:
    """Look up IBC building code requirements for a specific space type.
    
    Provides minimum dimensions, ceiling heights, and other code requirements.
    
    Args:
        building_type: "residential" or "commercial"
        space_type: "bedroom", "office", "corridor", "bathroom", etc.
    
    Returns:
        Code requirements from IBC standards
    """
    building_type = building_type.lower()
    space_type = space_type.lower()
    
    if building_type not in BUILDING_CODES:
        return {
            "error": f"Building type '{building_type}' not found",
            "available_types": list(BUILDING_CODES.keys())
        }
    
    codes = BUILDING_CODES[building_type].get(space_type)
    
    if codes:
        return {
            "building_type": building_type,
            "space_type": space_type,
            "requirements": codes,
            "standard": "IBC (International Building Code)",
            "status": "found"
        }
    else:
        return {
            "error": f"Space type '{space_type}' not found",
            "building_type": building_type,
            "available_types": list(BUILDING_CODES[building_type].keys())
        }

@mcp.tool()
async def check_code_compliance(
    building_type: str,
    space_type: str,
    area_sqft: float,
    ceiling_height_ft: float,
    width_inches: float = None
) -> Dict:
    """Check if a space meets IBC building code requirements.
    
    Validates dimensions against code minimums and identifies violations.
    Essential for design review and permitting.
    
    Args:
        building_type: "residential" or "commercial"
        space_type: "bedroom", "office", "corridor", etc.
        area_sqft: Floor area in square feet
        ceiling_height_ft: Ceiling height in feet
        width_inches: Width in inches (required for corridors/stairs)
    
    Returns:
        Compliance status with detailed pass/fail for each requirement
    """
    building_type = building_type.lower()
    space_type = space_type.lower()
    
    # Get code requirements
    if building_type not in BUILDING_CODES:
        return {"error": f"Building type '{building_type}' not recognized"}
    
    codes = BUILDING_CODES[building_type].get(space_type)
    if not codes:
        return {"error": f"Space type '{space_type}' not found for {building_type} buildings"}
    
    violations = []
    passes = []
    
    # Check minimum area
    if "min_area_sqft" in codes:
        min_area = codes["min_area_sqft"]
        if area_sqft < min_area:
            violations.append(f"Area {area_sqft} sqft < minimum {min_area} sqft required")
        else:
            passes.append(f"Area {area_sqft} sqft ≥ minimum {min_area} sqft ✓")
    
    # Check ceiling height
    if "min_ceiling_height_ft" in codes:
        min_height = codes["min_ceiling_height_ft"]
        if ceiling_height_ft < min_height:
            violations.append(f"Ceiling height {ceiling_height_ft}ft < minimum {min_height}ft required")
        else:
            passes.append(f"Ceiling height {ceiling_height_ft}ft ≥ minimum {min_height}ft ✓")
    
    # Check width (for corridors, stairs)
    if "min_width_inches" in codes and width_inches is not None:
        min_width = codes["min_width_inches"]
        if width_inches < min_width:
            violations.append(f"Width {width_inches} inches < minimum {min_width} inches required")
        else:
            passes.append(f"Width {width_inches} inches ≥ minimum {min_width} inches ✓")
    
    return {
        "compliant": len(violations) == 0,
        "building_type": building_type,
        "space_type": space_type,
        "area_sqft": area_sqft,
        "ceiling_height_ft": ceiling_height_ft,
        "violations": violations,
        "passes": passes,
        "code_standard": "IBC",
        "checked_at": datetime.now().isoformat()
    }

# ============================================================================
# MATERIAL ESTIMATION TOOLS
# ============================================================================

@mcp.tool()
async def estimate_materials(
    material_type: str,
    area: float,
    wall_height: float = 8.0,
    unit: str = "sqft"
) -> Dict:
    """Estimate material quantities for construction with waste factors.
    
    Calculates quantities for common building materials including industry-standard
    waste allowances. Essential for budgeting and ordering.
    
    Args:
        material_type: "drywall", "paint", "flooring", or "roofing"
        area: Area to cover (floor area for most, wall area for paint)
        wall_height: Wall height in feet (used for paint calculations)
        unit: "sqft" or "sqm"
    
    Returns:
        Material quantities with waste factors applied
    """
    # Validate unit
    unit_lc = unit.lower()
    if unit_lc not in ("sqft", "sqm"):
        return {
            "error": f"Unit '{unit}' not supported. Allowed units: 'sqft', 'sqm'.",
            "available_units": ["sqft", "sqm"]
        }
    # Convert to sqft if needed
    if unit_lc == "sqm":
        area_sqft = area * 10.7639
    else:
        area_sqft = area
    
    material_type = material_type.lower()
    
    # Material-specific calculations with waste factors
    if material_type == "drywall":
        # 4ft x 8ft sheets = 32 sqft each, 15% waste
        sheets_needed = (area_sqft / 32) * 1.15
        return {
            "material": "drywall",
            "area_sqft": round(area_sqft, 2),
            "sheets_needed": round(sheets_needed, 1),
            "waste_factor": "15%",
            "sheet_size": "4ft x 8ft (32 sqft)",
            "note": "Standard drywall sheets with 15% waste factor"
        }
    
    elif material_type == "paint":
        # 350 sqft per gallon coverage, 5% waste
        gallons_needed = (area_sqft / 350) * 1.05
        return {
            "material": "paint",
            "wall_area_sqft": round(area_sqft, 2),
            "gallons_needed": round(gallons_needed, 1),
            "waste_factor": "5%",
            "coverage_per_gallon": "350 sqft",
            "note": "One coat coverage with 5% waste factor"
        }
    
    elif material_type == "flooring":
        # 10% waste for cuts and mistakes
        quantity = area_sqft * 1.10
        return {
            "material": "flooring",
            "floor_area_sqft": round(area_sqft, 2),
            "material_needed_sqft": round(quantity, 2),
            "waste_factor": "10%",
            "note": "Includes 10% waste for cuts and fitting"
        }
    
    elif material_type == "roofing":
        # 1 square = 100 sqft, 15% waste
        squares = (area_sqft / 100) * 1.15
        return {
            "material": "roofing",
            "roof_area_sqft": round(area_sqft, 2),
            "roofing_squares": round(squares, 2),
            "waste_factor": "15%",
            "note": "1 square = 100 sqft, includes 15% waste"
        }
    
    else:
        return {"error": f"Material type '{material_type}' not supported",
                "available_types": ["drywall", "paint", "flooring", "roofing"]}

# ============================================================================
# PROJECT MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
async def create_project(
    name: str,
    building_type: str,
    total_area: float,
    description: str = ""
) -> Dict:
    """Create a new architectural project for tracking rooms and spaces.
    
    Projects help organize multiple rooms and generate area schedules.
    
    Args:
        name: Project name
        building_type: "residential" or "commercial"
        total_area: Total building area in sqft
        description: Optional project description
    
    Returns:
        Project details with unique ID
    """
    project_id = f"proj_{len(PROJECTS) + 1}"
    
    PROJECTS[project_id] = {
        "name": name,
        "type": building_type.lower(),
        "total_area": total_area,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "rooms": [],
        "status": "active"
    }
    
    return {
        "project_id": project_id,
        "name": name,
        "building_type": building_type,
        "total_area_sqft": total_area,
        "status": "created"
    }

@mcp.tool()
async def add_room_to_project(
    project_id: str,
    room_name: str,
    length: float,
    width: float,
    height: float,
    space_type: str
) -> Dict:
    """Add a room to an existing project.
    
    Tracks individual spaces for area schedules and project summaries.
    
    Args:
        project_id: Project ID (from create_project)
        room_name: Name of the room
        length: Room length in feet
        width: Room width in feet
        height: Ceiling height in feet
        space_type: Type of space (bedroom, office, etc.)
    
    Returns:
        Room details and updated room count
    """
    if project_id not in PROJECTS:
        return {"error": f"Project '{project_id}' not found",
                "available_projects": list(PROJECTS.keys())}
    
    room = {
        "name": room_name,
        "type": space_type,
        "dimensions": f"{length}ft x {width}ft x {height}ft",
        "area_sqft": round(length * width, 2),
        "volume_cuft": round(length * width * height, 2)
    }
    
    PROJECTS[project_id]["rooms"].append(room)
    
    return {
        "project_id": project_id,
        "room_added": room_name,
        "room_details": room,
        "total_rooms_in_project": len(PROJECTS[project_id]["rooms"])
    }

@mcp.tool()
async def get_project_summary(project_id: str) -> Dict:
    """Generate a project summary with area schedule.
    
    Provides complete project overview including all rooms, total areas,
    and circulation space calculations.
    
    Args:
        project_id: Project ID
    
    Returns:
        Complete project summary with area breakdown
    """
    if project_id not in PROJECTS:
        return {"error": f"Project '{project_id}' not found",
                "available_projects": list(PROJECTS.keys())}
    
    project = PROJECTS[project_id]
    total_room_area = sum(room["area_sqft"] for room in project["rooms"])
    circulation = project["total_area"] - total_room_area
    
    return {
        "project_id": project_id,
        "name": project["name"],
        "building_type": project["type"],
        "total_building_area_sqft": project["total_area"],
        "total_room_area_sqft": round(total_room_area, 2),
        "circulation_area_sqft": round(circulation, 2),
        "room_count": len(project["rooms"]),
        "rooms": project["rooms"],
        "efficiency_ratio": round(total_room_area / project["total_area"] * 100, 1),
        "created_at": project["created_at"]
    }

# ============================================================================
# MCP RESOURCES
# ============================================================================

@mcp.resource("architecture://codes")
async def read_building_codes() -> str:
    """MCP Resource: Access complete building codes database"""
    output = "BUILDING CODES DATABASE (IBC Standards)\n"
    output += "=" * 60 + "\n\n"
    
    for building_type, spaces in BUILDING_CODES.items():
        output += f"\n{building_type.upper()} BUILDING CODES:\n"
        output += "-" * 40 + "\n"
        for space_type, requirements in spaces.items():
            output += f"\n{space_type.upper()}:\n"
            for req, value in requirements.items():
                output += f"  • {req.replace('_', ' ').title()}: {value}\n"
    
    return output

@mcp.resource("architecture://project/{project_id}")
async def read_project(project_id: str) -> str:
    """MCP Resource: Access project details"""
    if project_id not in PROJECTS:
        return f"Project '{project_id}' not found"
    
    project = PROJECTS[project_id]
    output = f"PROJECT: {project['name']}\n"
    output += "=" * 60 + "\n"
    output += f"Type: {project['type']}\n"
    output += f"Total Area: {project['total_area']} sqft\n"
    output += f"Rooms: {len(project['rooms'])}\n"
    output += f"Created: {project['created_at']}\n\n"
    
    if project['rooms']:
        output += "ROOM SCHEDULE:\n"
        output += "-" * 60 + "\n"
        for room in project['rooms']:
            output += f"{room['name']}: {room['dimensions']} = {room['area_sqft']} sqft\n"
    
    return output

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    mcp.run(transport='stdio')
