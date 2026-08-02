# System Design

## Modules Overview

The system consists of four main modules: `analyze_module`, `cleaning_module`, `viz_module`, and a research task based on Serper.

### 1. Analyze Module (`analysis.py`)

**Purpose/Scope**: This module is responsible for conducting preliminary analyses on the provided datasets, generating an audit report that encapsulates insights about the data.

- **Function Signature**:
  ```python
  run_analysis(csv_file: str, task_type: str, target: Optional[str] = None, imbalance_threshold: float = 0.2) -> DatasetAudit
  ```

- **Structured Output**: 
  - `DatasetAudit`  
    - Includes statistics such as:
      - Data types
      - Missing value counts
      - Class distributions (for classification tasks)
      - Feature correlations

- **Execution Policy**: 
  - *scaffold only*

- **Guardrails**: 
  - Check for data leakage by assessing feature-target relationships.
  - Identify features with high cardinality to mitigate potential analysis issues.
  - Manage missingness in data by flagging and reporting missing values.

- **Integration & Lazy Imports**: 
  - Imported only when `run_analysis` is called, avoiding preloading of data analysis libraries.

---

### 2. Cleaning Module (`cleaning.py`)

**Purpose/Scope**: This module provides functionality to clean and preprocess datasets, preparing them for further analysis or modeling.

- **Class**: `DataCleaner`

  - **Method Signatures**:
    ```python
    plan(csv_path: str, analysis_kit_json: str) -> dict
    ```
    - **Output**: 
      - `CleaningPlan`  
        - A dictionary containing:
          - Steps for cleaning (e.g., imputation methods, droppings)
          - Justifications for each step
          
    ```python
    apply(csv_path: str, plan: dict) -> str
    ```
    - **Output**: 
      - Path to cleaned CSV (`cleaned_data_ref.json`)
      - Artifacts written to `outputs/cleaned_data_ref.json`

- **Execution Policy**: 
  - *WHEN CALLED*

- **Guardrails**: 
  - Ensure that the cleaning procedure does not induce data leakage.
  - Monitor features for high cardinality that might need special handling.
  - Acknowledge and report missingness.

- **Integration & Lazy Imports**: 
  - Modules loaded when `plan()` or `apply()` is called, enabling efficient resource use.

---

### 3. Viz Module (`viz.py`)

**Purpose/Scope**: This module focuses on visualizing the cleaned data, providing tools to generate insights through graphical representations.

- **Class**: `VizToolKit`

  - **Method Signatures**:
    ```python
    visualization(cleaned_csv_path: str, task_type: str, target: Optional[str] = None) -> dict
    ```
    - **Output**: 
      - A dictionary resembling `VisualSummary`, containing:
        - Paths to generated PNG files
        - Summary statistics based on visualizations
  
- **Frontend**: 
  - File located at `outputs/app.py`, designed to handle user interactions but has no I/O upon import.

- **Function Signature**:
  ```python
  build_demo() -> gr.Blocks
  ```

- **Handler**: 
  ```python
  run_pipeline(csv: str, task_type: str, target: Optional[str], domain: str, company: str)
  ```
  
- **Execution Policy**: 
  - *WHEN CALLED from the UI*

- **Guardrails**: 
  - Prevent outputting misleading visualizations by validating input parameters and cleaning plan.
  - Confirm all visualizations adequately represent corresponding data without bias.

- **Integration & Lazy Imports**: 
  - Visualization libraries are loaded only when `visualization` or `run_pipeline` is invoked.

---

### 4. Research Task (Serper-based)

**Purpose/Scope**: This module conducts further research activities based on details provided in domain and company parameters, generating results in Markdown format.

- **Output**: 
  - Markdown document containing insights, recommendations, or summaries based on the research task.

- **Execution Policy**: 
  - *WHEN CALLED*

- **Integration & Lazy Imports**: 
  - Integrates as needed based on the user’s interaction with the output, with no preloading required.

---

By maintaining structured output, execution policies, and guardrails across all modules, this system will ensure data integrity, provide clarity in data handling, and enhance the user experience through its clean design and output formats.