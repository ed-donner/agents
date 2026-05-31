# Software Engineering Crew

Welcome to the Software Engineering Crew project, powered by [crewAI](https://crewai.com). This project demonstrates how to use CrewAI to create a complete software engineering team capable of designing, implementing, and testing the backend, as well as building the frontend for complex software projects. Developed with 💜 by Tiago Iesbick.

## 🚀 What This Project Does

This CrewAI project showcases a **multi-agent software engineering team** that can:

1. **Design** a backend architecture based on requirements
2. **Implement** Python modules with proper classes and methods
3. **Write comprehensive unit tests** for all modules
4. **Create a functional frontend** using Gradio to demonstrate the backend

The team consists of specialized AI agents:
- **Engineering Lead**: Designs the system architecture
- **Backend Engineer**: Implements Python modules
- **Test Engineer**: Writes unit tests
- **Frontend Engineer**: Creates a Gradio UI

## 📋 Project Results

This project successfully generated a **complete trading simulation platform** with the following components:

### Generated Backend Modules (`output/backend/`)
- `accounts.py` - AccountService: Manages user accounts, deposits, withdrawals
- `trading.py` - TradingEngine: Executes buy/sell orders with validation
- `portfolio.py` - PortfolioService: Tracks holdings and calculates P/L
- `pricing.py` - PricingService: Provides stock prices for AAPL, TSLA, GOOGL
- `transactions.py` - TransactionLedger: Records all transaction history
- `validation.py` - ValidationRules: Enforces business rules
- `storage.py` - InMemoryStore: Provides data persistence

### Generated Tests (`output/tests/`)
- Complete pytest test suites for all modules
- Tests cover normal operations, edge cases, and error conditions
- All tests are designed to verify the modules fulfill their intended purposes

### Generated Frontend (`output/app.py`)
- Interactive Gradio application
- Dynamically imports and demonstrates all backend modules
- Provides UI for testing account operations, trading, and portfolio management

## 🛠️ Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

First, install uv:
```bash
pip install uv
```

Install the dependencies:
```bash
uv sync
```

**Important**:
- Add your `OPENAI_API_KEY` to a `.env` file in the project root.
- `Docker engine` MUST be running.

## 🏃‍♂️ Running the Project

To start the software engineering crew and generate the complete trading platform:

```bash
crewai run
```

This will:
1. **Design Phase**: Engineering Lead creates a project plan (`output/project_plan.json`)
2. **Implementation Phase**: Backend Engineer creates all Python modules
3. **Testing Phase**: Test Engineer writes comprehensive unit tests
4. **Frontend Phase**: Frontend Engineer creates the Gradio application

## 🧪 Testing the Generated Code

Run the complete test suite to verify all modules work correctly:

```bash
# Run all tests
uv run pytest

# Run tests for a specific module
uv run pytest output/tests/test_pricing.py
```

## 🎮 Using the Generated Application

Launch the Gradio frontend to interact with the trading platform:

```bash
uv run output/app.py
```

This opens a web interface where you can:
- Create and manage accounts
- Deposit and withdraw funds
- Execute buy/sell orders
- View portfolio holdings and P/L
- Check transaction history

## 🔧 How to Create Software Using CrewAI

### 1. Define Your Requirements
Modify `src/software_engineering/main.py` to specify your project requirements:

```python
requirements = """
Your software requirements here.
- Feature 1
- Feature 2
- Business rules
- Constraints
"""
```

### 2. Customize Agents
Edit `src/software_engineering/config/agents.yaml` to:
- Adjust agent roles and expertise
- Modify goals and backstories
- Configure LLM models

### 3. Customize Tasks
Modify `src/software_engineering/config/tasks.yaml` to:
- Define specific task workflows
- Set expected outputs
- Configure task dependencies

### 4. Extend the Crew
Add new agents in `src/software_engineering/crew.py`:
- Database engineers
- DevOps specialists
- Security experts
- Documentation writers

## 📊 Test Results

The generated trading platform includes comprehensive test coverage:

- **7 backend modules** with full functionality
- **7 test files** with 50+ individual test cases
- **100% module coverage** for core functionality
- **Error handling** for edge cases and invalid inputs
- **Thread safety** for concurrent operations

### Sample Test Results
```
test_accounts.py::test_create_account_success PASSED
test_accounts.py::test_deposit_success PASSED
test_trading.py::test_buy_order_success PASSED
test_trading.py::test_sell_order_success PASSED
test_portfolio.py::test_calculate_portfolio_value PASSED
```

## 🎯 Key Features Demonstrated

### Multi-Agent Collaboration
- **Sequential Processing**: Agents work in logical order
- **Dynamic Task Generation**: Tasks created based on design output
- **Callback System**: Automatic progression between phases

### Code Quality
- **Clean Architecture**: Modular, maintainable code
- **Comprehensive Testing**: Unit tests for all functionality
- **Error Handling**: Proper exception management
- **Documentation**: Clear docstrings and comments

### Real-World Application
- **Business Logic**: Complete trading simulation
- **Data Persistence**: In-memory storage with transaction logging
- **User Interface**: Interactive web application
- **Validation**: Business rule enforcement

## 🔄 Customization Examples

### Adding a New Agent
```python
@agent
def database_engineer(self) -> Agent:
    return Agent(
        config=self.agents_config['database_engineer'],
        verbose=True
    )
```

### Creating Custom Tasks
```python
@task
def database_setup_task(self) -> Task:
    return Task(
        description="Set up database schema and migrations",
        expected_output="Database schema files and migration scripts",
        agent=self.database_engineer(),
        output_file="output/database/schema.sql"
    )
```

## 📚 Understanding Your Crew

The software_engineering Crew demonstrates how multiple AI agents can collaborate:

1. **Engineering Lead**: Analyzes requirements and creates system design
2. **Backend Engineer**: Implements the actual code with proper structure
3. **Test Engineer**: Ensures code quality through comprehensive testing
4. **Frontend Engineer**: Creates user interfaces for the backend

Each agent has specialized knowledge and tools, working together to produce a complete, tested, and usable software system.

## 🆘 Support

For support, questions, or feedback regarding the SoftwareEngineering Crew or crewAI:
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI! 🚀
