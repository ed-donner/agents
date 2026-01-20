# 🏗️ The Architect of the Server

**By ERICKSONG ARCHITECTS INC.**

---

## 📋 Overview

The **Architect of the Server** is the **first MCP (Model Context Protocol) server built specifically for architecture and construction professionals**. It brings AI-powered building code compliance, material estimation, and architectural calculations directly into your AI agent workflows.

### 🎯 Why This Matters

After researching **3,000+ MCP servers** across all major marketplaces (MCP.so, Smithery, Glama, etc.) and analyzing major architecture platforms (Autodesk, Grasshopper, Finch3D, Giraffe.build), we found:

- ❌ **ZERO** MCP servers for architecture
- ❌ **ZERO** AI-powered building code compliance tools
- ❌ **ZERO** natural language architectural validation

**This server fills that gap.**

---

## ✨ Features

### 🧮 **Architectural Calculations**
- Area calculations (sqft, sqm, sqin)
- Volume calculations with unit conversion
- Support for imperial and metric units

### 📐 **Building Code Compliance**
- IBC (International Building Code) standards
- Automatic room/space verification
- Residential and commercial building types
- Detailed violation reporting

### 🔨 **Material Estimation**
- Drywall (4x8 sheets, 15% waste factor)
- Paint (350 sqft/gallon coverage, 5% waste)
- Flooring (10% waste factor)
- Roofing (15% waste factor)

### 📊 **Project Management**
- Multi-project tracking
- Room-by-room organization
- Area schedules generation
- Building summaries

---

## 🚀 Quick Start

### Installation

```bash
# The server is already in the repository
cd 6_mcp/community_contributions/architect_of_the_server_ericksong

# Install dependencies (if needed)
pip install mcp fastmcp
```

### Usage with Agents SDK

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

# Start the architecture MCP server
arch_params = {"command": "uv", "args": ["run", "architecture_server.py"]}

async with MCPServerStdio(params=arch_params, client_session_timeout_seconds=60) as mcp_server:
    agent = Agent(
        name="arch_assistant",
        instructions="You are an expert architectural assistant.",
        model="gpt-4o-mini",
        mcp_servers=[mcp_server]
    )
    
    result = await Runner.run(
        agent, 
        "Check if a 12ft x 14ft bedroom with 8ft ceilings meets residential code"
    )
    print(result.final_output)
```

---

## 🛠️ Available Tools

### 1. `calculate_area`
Calculate area with unit conversion support.

**Parameters:**
- `length` (float): Length dimension
- `width` (float): Width dimension
- `unit` (str): "feet", "meters", or "inches"

**Example:**
```
"Calculate the area of a room that is 12 feet by 14 feet"
```

### 2. `calculate_volume`
Calculate volume for 3D spaces.

**Parameters:**
- `length`, `width`, `height` (float): Dimensions
- `unit` (str): Unit of measurement

**Example:**
```
"What's the volume of a 15ft x 20ft room with 9ft ceilings?"
```

### 3. `lookup_building_code`
Get IBC code requirements for specific spaces.

**Parameters:**
- `building_type` (str): "residential" or "commercial"
- `space_type` (str): "bedroom", "office", "corridor", etc.

**Example:**
```
"What are the code requirements for a commercial corridor?"
```

### 4. `check_code_compliance`
Verify if a space meets building codes.

**Parameters:**
- `building_type`, `space_type`, `area_sqft`, `ceiling_height_ft`, `width_inches`

**Example:**
```
"Does an 8ft x 10ft bedroom with 7ft ceilings meet code?"
```

### 5. `estimate_materials`
Calculate material quantities with waste factors.

**Parameters:**
- `material_type` (str): "drywall", "paint", "flooring", "roofing"
- `area` (float): Area to cover
- `wall_height` (float, optional): For paint calculations

**Example:**
```
"How much paint do I need for 400 sqft of walls?"
```

### 6. `create_project`
Start tracking a new architectural project.

**Parameters:**
- `name`, `building_type`, `total_area`, `description`

**Example:**
```
"Create a residential project called 'Downtown Loft' with 2400 sqft"
```

### 7. `add_room_to_project`
Add rooms to track in a project.

**Parameters:**
- `project_id`, `room_name`, `length`, `width`, `height`, `space_type`

**Example:**
```
"Add a 12x14 master bedroom with 9ft ceilings to project 1"
```

### 8. `get_project_summary`
Generate area schedules and project reports.

**Parameters:**
- `project_id` (str): Project identifier

**Example:**
```
"Give me a summary of project 1"
```

---

## 📚 Example Workflows

### Workflow 1: Quick Room Check
```python
request = """
I'm designing a bedroom that is 11 feet by 12 feet with 8-foot ceilings.
Can you:
1. Calculate the area and volume
2. Check if it meets residential building code
3. Estimate paint needed for the walls
"""
```

### Workflow 2: Complete Project
```python
request = """
Create a new residential project called 'Maple Street House' with 2,800 sqft total.
Add these rooms:
- Master Bedroom: 14ft x 16ft, 9ft ceilings
- Guest Bedroom: 10ft x 12ft, 8ft ceilings
- Kitchen: 12ft x 15ft, 9ft ceilings
- Living Room: 18ft x 22ft, 10ft ceilings

Check all rooms for code compliance and give me a project summary.
"""
```

### Workflow 3: Material Takeoff
```python
request = """
I have a commercial office that is 40ft x 60ft with 9ft ceilings.
Calculate:
1. Total floor area
2. Flooring material needed
3. Drywall sheets for perimeter walls
4. Paint needed for all walls
"""
```

---

## 🎓 What I Learned Building This

### Technical Insights
- **FastMCP makes server creation simple** - Just decorators and async functions
- **OpenAI schema requirements are strict** - All parameters must be in `required` array
- **WSL has MCP stdio issues** - Required Linux npm/npx instead of Windows versions
- **Type hints are critical** - They auto-generate the MCP tool schemas

### Architecture Knowledge Applied
- **IBC standards integration** - Real building code requirements
- **Material waste factors** - Industry-standard allowances (5-15%)
- **Unit conversions** - Supporting both imperial and metric
- **Multi-project architecture** - In-memory storage with unique IDs

### Research Findings
- **No MCP competition** - First architecture server in 3,000+ servers
- **Complementary to existing tools** - Works WITH Revit, Grasshopper, etc.
- **Unique market position** - Bridge between AI agents and architecture

---

## 🔮 Future Enhancements

### Phase 1: Database & Expansion (Planned)
- [ ] PostgreSQL persistence (replace in-memory storage)
- [ ] Complete IBC code database
- [ ] Additional material types (lumber, concrete, steel)
- [ ] Structural calculations (beams, columns)

### Phase 2: CAD Integration (Planned)
- [ ] Revit API integration (bidirectional)
- [ ] IFC file import/export
- [ ] AutoCAD DXF support
- [ ] 3D model validation

### Phase 3: Advanced Features (Vision)
- [ ] 3D point cloud processing (laser scanning)
- [ ] AI room type classification
- [ ] Energy code compliance (LEED, ASHRAE)
- [ ] MEP calculations (HVAC, electrical, plumbing)

### Phase 4: Enterprise (Vision)
- [ ] Cloud deployment (AWS/Azure)
- [ ] Multi-user collaboration
- [ ] Team permissions
- [ ] Integration with cost APIs

---

## 📊 Test Results

Comprehensive testing shows:
- ✅ **Accuracy: 9/10** - Calculations are precise and reliable
- ✅ **Flexibility: 8/10** - Supports diverse projects and room types
- ✅ **Code Compliance: 7/10** - Accurate but needs richer feedback
- ✅ **Scalability: 8/10** - Handles both simple and complex scenarios
- ✅ **Practical Usability: 7/10** - Strong foundation, needs UI integration

**Tests Performed:**
1. Small residential renovation (5 rooms, 850 sqft) - ✅ PASSED
2. Commercial office takeoff (3240 sqft, 98 drywall sheets) - ✅ PASSED
3. Edge cases & code violations (6 scenarios, 3 failures caught) - ✅ PASSED
4. Metric vs imperial conversions - ✅ PASSED
5. Multi-building complex (3 houses, 9 rooms) - ✅ PASSED

---

## 🏆 Competitive Analysis

### Researched Platforms
- **Autodesk (Revit, AutoCAD)** - No MCP, traditional CAD
- **Grasshopper (Rhino)** - No MCP, visual programming
- **Finch3D** - No MCP, generative AI (closed platform)
- **Giraffe.build** - No MCP, urban planning scale

### Result
**ZERO MCP servers for architecture exist.**

This server creates an entirely new category: **AI-Powered Architecture Validation via MCP**

---

## 🤝 Contributing

This is a community project! Contributions welcome:

### Ideas for Contributors
- Add more building code standards (Eurocodes, Australian codes, etc.)
- Implement structural calculations
- Add energy modeling capabilities
- Create visualization tools
- Integrate with more CAD platforms

### How to Contribute
1. Fork the repository
2. Create a feature branch
3. Test thoroughly with realistic architectural scenarios
4. Submit a pull request

---

## 📝 License

This MCP server is part of the **Week 6 Agents Course** community contributions.

Feel free to use, modify, and extend for your own projects!

---

## 👤 Author

**ERICKSONG ARCHITECTS INC.**

Built during Week 6 of the AI Agents course as a demonstration of:
- MCP protocol implementation
- Real-world architectural problem-solving
- AI agent integration for professional workflows

---

## 🙏 Acknowledgments

- **Ed Donner** - For creating this incredible AI Agents course
- **Anthropic** - For developing the MCP protocol
- **OpenAI** - For the Agents SDK
- **The Course Community** - For inspiration and support

---

## 📞 Questions?

If you have questions about using this MCP server or want to discuss architecture + AI:
- Check the course Discord
- Review the test notebooks in this folder
- Experiment with the example workflows above
- For more information, visit the ERICKSONG ARCHITECTS Blog at https://ericksong.com/blogging-architect-toronto-zoning-building-permit/

**Let's build the future of architecture together!** 🏗️✨

---

*"The best buildings are designed with both creativity and precision. Now AI can help with the precision, so architects can focus on the creativity."*

— ERICKSONG ARCHITECTS INC.
