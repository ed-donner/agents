# 🧳 TravelMate

**AI-powered travel planning with intelligent agents**

Create comprehensive travel guides using 7 specialized AI agents that work together to plan your perfect trip.

## 🤖 AI Agents

### Information Gatherers
- **🏛️ Travel Guide** - Top attractions and destinations
- **🍽️ Food Guide** - Local cuisine and restaurants  
- **🏨 Stay Guide** - Hotels and accommodations

### Trip Planners  
- **🗺️ Travel Planner** - Complete itineraries
- **🎯 Activity Planner** - Daily activities and schedules
- **🍴 Food Planner** - Dining experiences
- **💰 Budget Planner** - Cost estimates and money-saving tips

## 🚀 Quick Start

### 1. Install
```bash
pip install 'crewai[tools]' markdown weasyprint jinja2
```

### 2. Setup API Key
```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### 3. Run
```bash
python src/travelmate/main.py
```

## ⚙️ Customize

**Change destination** in `src/travelmate/main.py`:
```python
inputs = {
    'location': 'Your Destination',
    'typeOfTourism': 'adventurous'  # or 'cultural', 'relaxing', 'family'
}
```

## 📄 Output

Generates a complete travel package as a Markdown file:
- `output/complete_travel_package_[Destination].md`

## 🔧 Configuration

- **Agents**: Edit `src/travelmate/config/agents.yaml`
- **Tasks**: Edit `src/travelmate/config/tasks.yaml`

## ❓ Troubleshooting

**Missing crewai**: `pip install crewai[tools]`  
**API key error**: Check your `.env` file has `OPENAI_API_KEY=your_key`

---

**Happy Traveling! 🌍✈️**

*Powered by CrewAI*