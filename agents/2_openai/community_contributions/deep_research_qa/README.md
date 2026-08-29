---
title: Deep_Research_Assistant
app_file: app.py
sdk: gradio
sdk_version: 5.29.0
---
# 🔍 Deep Research Assistant

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces)
[![Gradio](https://img.shields.io/badge/Gradio-Interface-orange)](https://gradio.app)

A comprehensive AI-powered research assistant that delivers high-quality, well-researched reports with built-in quality assurance and email delivery capabilities.

## 🚀 Features

### 🤖 Enhanced AI Research System
- **Quality Evaluation**: Every report is automatically assessed for completeness, accuracy, and clarity
- **Smart Optimization**: Reports scoring below 7/10 are automatically improved
- **Multi-Strategy Search**: Uses multiple search approaches for comprehensive coverage
- **Email Delivery**: Optional email delivery of research reports

### 🎯 Research Modes

1. **🚀 Interactive Research with Clarification** (Recommended)
   - Generates clarifying questions to focus your research
   - Provides more targeted and relevant results
   - Uses the enhanced quality assurance pipeline

2. **🤖 Enhanced Direct Research**
   - Advanced AI system with automatic quality evaluation
   - Iterative improvement when needed
   - Full traceability with OpenAI traces

3. **⚡ Quick Research**
   - Fast research for simple queries
   - Legacy compatibility mode
   - Good for straightforward questions

## 🛠️ Setup

### Environment Variables

You'll need to set up the following environment variables:

```bash
# Required - OpenAI API for research
OPENAI_API_KEY=your_openai_api_key_here

# Optional - SendGrid for email delivery
SENDGRID_API_KEY=your_sendgrid_api_key_here
SENDGRID_FROM_EMAIL=your_verified_sender_email@example.com
```

### For Hugging Face Spaces Deployment

1. **Fork this space** or create a new one
2. **Add your secrets** in the Space settings:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SENDGRID_API_KEY`: Your SendGrid API key (optional)
   - `SENDGRID_FROM_EMAIL`: Your verified sender email (optional)
3. **Deploy** - The space will automatically install dependencies and launch

### For Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd deep_research
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

## 📊 Quality Assurance System

Our enhanced research system includes automatic quality evaluation:

### Evaluation Criteria
- **Completeness**: How thoroughly the query is addressed
- **Accuracy**: Factual correctness and source reliability  
- **Clarity**: Writing quality and organization
- **Depth**: Analysis depth and insight quality
- **Relevance**: Content alignment with the original query

### Scoring Scale
- **9-10**: Excellent (no refinement needed)
- **7-8**: Good (minor improvements)
- **5-6**: Adequate (refinement recommended)
- **1-4**: Poor (automatic refinement triggered)

## 🎮 How to Use

1. **Enter Your Research Query**: Describe what you want to research
2. **Configure Email (Optional)**: Set up email delivery if desired
3. **Choose Research Mode**:
   - Click "🚀 Start Research" for interactive clarification mode
   - Use "🤖 Enhanced Research" for direct advanced research
   - Use "⚡ Quick Research" for fast results

4. **Get Results**: 
   - View comprehensive research report
   - Receive email delivery (if configured)
   - Access detailed trace logs for transparency

## 🔧 Technical Architecture

Built with:
- **Frontend**: Gradio for interactive web interface
- **Backend**: OpenAI Agents framework for modular AI system
- **Quality Assurance**: Automated evaluation and optimization pipeline
- **Email**: SendGrid integration for report delivery
- **Tracing**: OpenAI trace integration for full transparency

### Agent-Based Architecture

The system uses specialized AI agents:
- **Research Manager**: Orchestrates the entire research process
- **Planner Agent**: Creates strategic search plans
- **Search Agent**: Performs web searches
- **Writer Agent**: Generates comprehensive reports
- **Evaluator Agent**: Assesses report quality
- **Optimizer Agent**: Improves reports when needed
- **Email Agent**: Handles report delivery

## 📝 Example Queries

Try these example research queries:

- "Latest developments in renewable energy storage technology"
- "Impact of AI on healthcare industry in 2024"
- "Sustainable urban planning strategies for climate change"
- "Cybersecurity trends and threats in financial services"
- "Electric vehicle market analysis and future projections"

## 🤝 Contributing

We welcome contributions! Areas for improvement:
- Additional research sources and tools
- Enhanced evaluation criteria
- New output formats
- UI/UX improvements
- Performance optimizations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♀️ Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: Check out the enhanced README in the repository
- **Trace Logs**: Use the provided trace IDs to debug research processes

---

**Built with ❤️ using OpenAI Agents, Gradio, and modern AI research techniques.** 