# 🎨 AI Visual Art Studio IDE

A simplified creative IDE that uses **OpenAI Agents SDK** with intelligent delegation flow for multi-agent creative collaboration. Instead of rigid pipelines, agents naturally delegate to each other based on task requirements and expertise.

## 🌟 **Key Features**

### **🤖 Intelligent Agent Delegation**
- **Concept Artist**: Creative director who can delegate specialized tasks
- **Sketch Artist**: Visual creator who can delegate refinement work
- **Refinement Artist**: Detail specialist who can delegate evaluation
- **Curator**: Final evaluator who can request improvements from any agent

### **🔄 Natural Delegation Flow**
- **No fixed order** - agents decide when to delegate based on task needs
- **Intelligent handoffs** - each agent focuses on their expertise
- **Collaborative creation** - multiple agents work together naturally
- **Flexible workflows** - adapts to different creative requirements

### **🔧 OpenAI Agents SDK Integration**
- **Built-in tracing** for all executions and delegations
- **Decorator-based tools** (`@tool`, `@guardrail`, `@trace`)
- **Agent-to-agent communication** through delegation tools
- **Content safety** with built-in guardrails

### **🎨 Creative Workflow Examples**
- **Concept → Sketch → Refinement → Curator** (full creative process)
- **Concept → Curator** (quick evaluation)
- **Sketch → Refinement → Curator** (visual improvement focus)
- **Curator → Refinement** (quality improvement requests)

## 🚀 **Quick Start**

### **1. Setup Environment**
```bash
# Clone the repository
git clone <your-repo>
cd art_studio

# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env
```

### **2. Run the Studio**
```bash
# Launch the Gradio web interface
python main.py

# Or run examples directly
python example_usage.py
```

### **3. Use the Delegation Flow**
1. **Start with any agent** as your primary creative partner
2. **Describe your vision** - agents will delegate as needed
3. **Watch the collaboration** unfold naturally
4. **Review the results** with full execution tracing

## 🏗️ **Architecture**

### **Core Components**
```
ArtStudio
├── Agent Management (OpenAI Agents SDK)
├── Delegation Flow Engine
├── Tool System (@tool decorators)
├── Guardrails (@guardrail decorators)
├── Tracing (@trace decorators)
└── Gradio Web Interface
```

### **Delegation Patterns**
```
Concept Artist
├── Can delegate to: Sketch Artist, Refinement Artist, Curator
└── Role: Creative direction and coordination

Sketch Artist
├── Can delegate to: Refinement Artist, Curator
└── Role: Visual creation and composition

Refinement Artist
├── Can delegate to: Curator
└── Role: Technical improvement and detail work

Curator
├── Can delegate to: Concept Artist, Sketch Artist, Refinement Artist
└── Role: Quality evaluation and improvement requests
```

## 🎯 **Usage Examples**

### **Basic Delegation Flow**
```python
from src.core.art_studio import ArtStudio

# Initialize the studio
studio = ArtStudio()

# Execute delegation flow
result = await studio.execute_delegation_flow(
    "Design a magical forest scene with glowing mushrooms",
    "concept_artist"  # Start with concept artist
)

# Agents will automatically delegate as needed
print(f"Completed in {result['total_iterations']} iterations")
```

### **Single Agent Execution**
```python
# Execute a specific agent
result = await studio.execute_agent(
    "sketch_artist",
    "Create a sketch based on this concept: futuristic cityscape"
)
```

### **Agent Information**
```python
# Get agent capabilities
agent_info = studio.get_agent_info("concept_artist")
print(f"Can delegate to: {agent_info['can_delegate_to']}")
```

## 🔍 **Tracing & Debugging**

### **Built-in Tracing**
- **All agent executions** are automatically traced
- **Delegation decisions** are logged and tracked
- **Performance metrics** for each agent
- **Full execution chain** visibility

### **Debug Information**
- **Agent delegation patterns**
- **Tool usage statistics**
- **Execution time tracking**
- **Error handling and recovery**

## 🛡️ **Safety & Guardrails**

### **Content Safety**
- **Built-in filtering** for inappropriate content
- **Bias detection** and mitigation
- **Copyright protection** measures
- **Quality standards** enforcement

### **Guardrail System**
- **@guardrail decorators** for input/output filtering
- **Configurable safety rules**
- **Automatic content review**
- **Escalation procedures**

## 🎨 **Creative Workflows**

### **Full Creative Process**
1. **Concept Artist** generates creative vision
2. **Delegates to Sketch Artist** for visual representation
3. **Sketch Artist delegates to Refinement Artist** for details
4. **Refinement Artist delegates to Curator** for evaluation
5. **Curator may request improvements** from any agent

### **Quick Evaluation**
1. **Concept Artist** creates concept
2. **Delegates directly to Curator** for assessment
3. **Curator provides feedback** and recommendations

### **Visual Improvement Focus**
1. **Sketch Artist** creates initial sketch
2. **Delegates to Refinement Artist** for enhancement
3. **Refinement Artist delegates to Curator** for final review

## 🚀 **Advanced Features**

### **Custom Tools**
- **Easy tool creation** with `@tool` decorator
- **Agent-specific tools** for specialized tasks
- **Tool composition** and chaining
- **External API integration**

### **Model Configuration**
- **Per-agent model selection**
- **Parameter customization**
- **Hot-swapping capabilities**
- **Performance optimization**

### **Extensibility**
- **Plugin system** for custom agents
- **External tool integration**
- **Workflow customization**
- **API endpoints** for external access

## 📊 **Performance & Monitoring**

### **Execution Metrics**
- **Agent response times**
- **Delegation frequency**
- **Tool usage patterns**
- **Error rates and recovery**

### **Resource Management**
- **Memory usage optimization**
- **Concurrent execution** support
- **Rate limiting** and throttling
- **Resource cleanup** and management

## 🔮 **Roadmap**

### **Phase 1: Core Delegation** ✅
- [x] Basic delegation flow
- [x] Agent-to-agent communication
- [x] Built-in tracing
- [x] Content safety

### **Phase 2: Advanced Features**
- [ ] Multi-modal support (images, audio)
- [ ] Advanced guardrails
- [ ] Performance optimization
- [ ] External tool integration

### **Phase 3: Enterprise Features**
- [ ] Team collaboration
- [ ] Advanced analytics
- [ ] Custom agent training
- [ ] Enterprise security

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black src/
isort src/
```

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **OpenAI Agents SDK** for the powerful agent framework
- **Gradio** for the beautiful web interface
- **Community contributors** for ideas and feedback

---

**🎨 Create, Collaborate, Delegate - Let AI agents work together naturally!**
