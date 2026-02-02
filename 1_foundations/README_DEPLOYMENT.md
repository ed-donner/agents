---
title: Intellecta Career Assistant
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app_new.py
pinned: false
license: mit
---

# 🤖 Intellecta Career Assistant

An intelligent AI-powered career assistant that showcases professional projects and provides interactive consultation through RAG-enhanced conversations.

## ✨ Features

- **📊 Interactive Project Showcase**: Modern carousel displaying 11+ professional projects
- **💬 RAG-Enhanced Chat**: Context-aware conversations powered by OpenAI GPT-4
- **🔐 Secure Access**: Session management with rate limiting
- **📧 Direct Contact**: Email/reason submission for personalized engagement
- **🎯 Visitor Mode**: Free trial access for exploration

## 🚀 Live Demo

Try it now: [Hugging Face Space URL]

## 🛠️ Tech Stack

- **Framework**: Gradio 4.44.0
- **AI**: OpenAI GPT-4 + text-embedding-3-small
- **Backend**: Python, SQLite
- **Security**: bcrypt, session management, rate limiting
- **RAG**: OpenAI Embeddings + cosine similarity search

## 📚 Knowledge Base

The assistant has extensive knowledge about:
- ☁️ Cloud Architecture (AWS, Kubernetes, Terraform)
- 🤖 Gen-AI Systems (RAG, LangChain, Agents)
- 🔄 MLOps/DevOps (CI/CD, monitoring, automation)
- 💻 Software Engineering (Python, Node.js, microservices)

## 🎨 UI Features

### Project Carousel
- 11 featured projects with smooth auto-scroll
- Hover to pause animation
- Click cards for detailed view
- Modal with full project information

### Chat Interface
- Real-time AI responses
- Context-aware conversations
- Follow-up question suggestions
- Session-based memory

### Security Features
- IP-based rate limiting
- Session timeout (30 minutes)
- Query limits for visitors
- Password hashing (bcrypt)

## 🔧 Configuration

### Environment Variables

Required secrets (set in Hugging Face Space settings):

```bash
OPENAI_API_KEY=your_openai_api_key_here
PUSHOVER_USER_KEY=your_pushover_user_key  # Optional for notifications
PUSHOVER_API_TOKEN=your_pushover_api_token  # Optional for notifications
```

### Application Settings

- **Visitor Query Limit**: 10 messages
- **Session Timeout**: 30 minutes
- **Rate Limit**: 10 requests / 60 seconds
- **IP Visitor Cooldown**: 24 hours

## 📊 Usage Statistics

The application tracks:
- Visitor accounts created
- Messages sent
- Email contacts submitted
- Session durations

## 🧪 Testing

Comprehensive test suite included:

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run all tests
bash run_tests.sh

# Or run individually
pytest test_unit.py -v          # Unit tests
pytest test_integration.py -v   # Integration tests
pytest test_ui.py -v            # UI tests (requires app running)
```

## 📦 Deployment

### Local Development

```bash
# Clone repository
git clone https://github.com/xeroxpro/agents.git
cd agents/1_foundations

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key_here

# Run application
python app_new.py
```

### Hugging Face Spaces

1. Fork/clone this repository
2. Create new Space on Hugging Face
3. Connect GitHub repository
4. Set secrets in Space settings:
   - `OPENAI_API_KEY`
   - `PUSHOVER_USER_KEY` (optional)
   - `PUSHOVER_API_TOKEN` (optional)
5. Deploy automatically on push

## 📝 License

MIT License - See LICENSE file for details

## 👨‍💻 Author

**Gonench Aydin**
- LinkedIn: [Your LinkedIn Profile]
- GitHub: [@xeroxpro](https://github.com/xeroxpro)
- Email: [Your Email]

## 🙏 Acknowledgments

- OpenAI for GPT-4 and Embeddings API
- Gradio team for the amazing framework
- Hugging Face for hosting platform

## 📈 Roadmap

- [ ] Multi-language support (Turkish, English)
- [ ] Voice interaction
- [ ] Project filtering by technology
- [ ] Analytics dashboard
- [ ] Integration with LinkedIn API

## 🐛 Known Issues

None currently. Please report issues on GitHub.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## 📞 Support

For questions or support:
- Open GitHub issue
- Contact via email form in app
- LinkedIn message

---

**Note**: This application uses OpenAI API which requires valid API key. Usage costs apply based on OpenAI pricing.
