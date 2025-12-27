# Chatforge Testing Notebooks

This directory contains Jupyter notebooks for testing and exploring Chatforge functionality.

## Quick Start

```bash
# Install Jupyter
pip install jupyter notebook

# Install optional analysis packages
pip install pandas matplotlib numpy

# Start Jupyter
jupyter notebook

# Open: chatforge_testing_guide.ipynb
```

## Available Notebooks

### `chatforge_testing_guide.ipynb`
**Comprehensive testing and analysis guide**

**What it covers**:
- ✅ Environment setup and verification
- ✅ Simple LLM testing (chatforge.llm)
- ✅ Agent testing with tools (ReActAgent)
- ✅ Middleware testing (PII, Safety, Injection)
- ✅ Performance analysis (tokens, latency, costs)
- ✅ Model comparison (different providers)
- ✅ Reusable testing utilities
- ✅ Results export

**When to use**:
- Exploring Chatforge APIs
- Analyzing LLM performance
- Comparing models/providers
- Prototyping features
- Creating documentation/tutorials
- Visualizing token usage and costs

## Notebooks vs ChatTerm CLI

**Use Jupyter Notebooks when**:
- 📊 You need data analysis and visualization
- 🔬 You're exploring and experimenting
- 📖 You're creating documentation
- 🎓 You're learning or teaching
- 📈 You need to compare multiple models

**Use ChatTerm CLI when**:
- ⚡ You need quick iteration (30 second test cycles)
- 💬 You're testing conversation flow
- 🔧 You're debugging in development
- 🤖 You're testing in CI/CD pipelines
- 🛡️ You're validating middleware behavior

**Best Practice: Use Both!**
```
1. Explore in Jupyter → Prototype and analyze
2. Validate in ChatTerm → Quick testing and debugging
3. Production Code → Integrate validated approach
4. Monitor in Jupyter → Analyze production metrics
5. Regression in ChatTerm → Automated testing
```

## Recommended Workflow

### Week 1: Exploration (Jupyter)
```python
# In notebook: chatforge_testing_guide.ipynb
# - Test different models (GPT-4o, Claude 3.5, etc.)
# - Try various system prompts
# - Experiment with tools
# - Visualize token usage and costs
# - Compare 5-10 different configurations
```

### Week 2: Validation (ChatTerm)
```bash
# Extract best config from notebook, test in ChatTerm
chatterm \
  --mode agent \
  --model gpt-4o \
  --tools search,calculator \
  --middleware pii,safety \
  --debug

# Create test script for CI/CD
./test-chatforge.sh < test_scenarios.txt
```

### Week 3: Production
```python
# Integrate validated approach into application
# Add unit tests (pytest)
# Monitor with Jupyter notebooks
# Regression test with ChatTerm
```

## Notebook Structure Best Practices

### Organization
```
notebooks/
├── exploration/           # Experimental notebooks
│   ├── 01_llm_comparison.ipynb
│   ├── 02_prompt_engineering.ipynb
│   └── 03_tool_testing.ipynb
├── analysis/             # Analysis notebooks
│   ├── token_usage_analysis.ipynb
│   └── response_quality_metrics.ipynb
├── tutorials/            # Documentation notebooks
│   ├── getting_started.ipynb
│   └── advanced_agents.ipynb
└── production/           # Production monitoring
    └── daily_metrics.ipynb
```

### Naming Convention
- **Prefix with number**: `01_`, `02_` for ordered execution
- **Descriptive names**: `llm_comparison` not `test1`
- **Purpose suffix**: `_exploration`, `_analysis`, `_tutorial`

### Cell Organization
1. **Imports and Setup** - First cell
2. **Configuration** - Second cell
3. **Main Logic** - Organized sections with markdown headers
4. **Cleanup/Export** - Last cell

### Making Notebooks Reproducible

```python
# Always include at the start:

# 1. Version information
import sys
print(f"Python: {sys.version}")
print(f"Chatforge: {chatforge.__version__}")

# 2. Random seeds
import random, numpy as np
random.seed(42)
np.random.seed(42)

# 3. API configuration
import os
assert os.getenv("OPENAI_API_KEY"), "Set OPENAI_API_KEY"

# 4. Clear output before running
from IPython.display import clear_output
```

## Useful Extensions

Install these for better notebook experience:

```bash
# Code formatting
pip install jupyter-black

# Notebook diffing (for git)
pip install nbdime
nbdime config-git --enable

# Parameterized notebooks
pip install papermill

# Table of contents
jupyter labextension install @jupyterlab/toc

# Variable inspector
pip install jupyter_contrib_nbextensions
jupyter contrib nbextension install --user
```

## Tips and Tricks

### 1. Extract Reusable Code

Instead of copying cells:
```python
# Create utilities module
# chatforge_test_utils.py

def create_test_agent(model="gpt-4o-mini"):
    from chatforge import get_llm
    from chatforge import ReActAgent
    llm = get_llm(provider="openai", model_name=model)
    return ReActAgent(llm=llm, tools=[])

# Use in notebooks
from chatforge_test_utils import create_test_agent
agent = create_test_agent()
```

### 2. Use Magic Commands

```python
# Timing
%time response = llm.invoke([message])
%timeit -n 10 llm.invoke([message])

# Debugging
%debug  # Enter debugger on exception

# Reload modules (during development)
%load_ext autoreload
%autoreload 2

# Display variables
%whos  # List all variables

# Shell commands
!pip list | grep chatforge
!ls -la ../chatforge/
```

### 3. Save Outputs

```python
# Save figures
import matplotlib.pyplot as plt
plt.savefig('token_usage.png', dpi=300, bbox_inches='tight')

# Save data
df.to_csv('results.csv', index=False)
df.to_excel('results.xlsx', index=False)
df.to_json('results.json', orient='records')

# Save entire notebook outputs
# File > Export Notebook As > HTML/PDF
```

### 4. Parameterize Notebooks

```bash
# Run notebook with parameters
papermill \
  chatforge_testing_guide.ipynb \
  output.ipynb \
  -p model "gpt-4o" \
  -p provider "openai"
```

## Common Issues

### Issue: Kernel Keeps Dying
**Cause**: Too much memory usage (large DataFrames)
**Solution**:
- Process data in chunks
- Use `del` to free memory
- Restart kernel between large operations

### Issue: API Rate Limits
**Cause**: Too many requests to LLM API
**Solution**:
- Add `time.sleep(1)` between calls
- Use smaller batch sizes
- Cache results

### Issue: Import Errors
**Cause**: Wrong Python environment
**Solution**:
```bash
# Check which Python Jupyter is using
jupyter kernelspec list

# Install in correct environment
conda activate myenv  # or: source venv/bin/activate
pip install chatforge jupyter

# Create kernel for this environment
python -m ipykernel install --user --name=myenv
```

## Examples from Notebook

### Quick LLM Test
```python
from chatforge import get_llm
from langchain_core.messages import HumanMessage

llm = get_llm(provider="openai", model_name="gpt-4o-mini")
response = llm.invoke([HumanMessage(content="Hello!")])
print(response.content)
```

### Agent with Tools
```python
from chatforge import ReActAgent
from chatforge import get_llm
from langchain_core.tools import tool

@tool
def calculator(expr: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expr))

llm = get_llm(provider="openai", model_name="gpt-4o-mini")
agent = ReActAgent(llm=llm, tools=[calculator])

response, trace_id = agent.process_message(
    "What's 25 times 17?",
    conversation_history=[]
)
print(response)
```

### Performance Analysis
```python
import pandas as pd
import time

results = []
for prompt in test_prompts:
    start = time.time()
    response = llm.invoke([HumanMessage(content=prompt)])
    latency = time.time() - start

    results.append({
        'prompt': prompt,
        'tokens': response.usage_metadata.get('total_tokens', 0),
        'latency_ms': latency * 1000,
    })

df = pd.DataFrame(results)
print(df.describe())
```

## Contributing

When adding new notebooks:

1. **Use the template structure** from `chatforge_testing_guide.ipynb`
2. **Clear all outputs** before committing (Cell > All Output > Clear)
3. **Add to this README** with description and use case
4. **Test the notebook** from fresh kernel (Kernel > Restart & Run All)
5. **Add to `.gitignore`**: `*.ipynb_checkpoints/`, large data files

## Resources

- **Chatforge Docs**: `../devdocs/`
- **ChatTerm CLI Docs**: `../devdocs/enhancements/chatterm/`
- **Jupyter Docs**: https://jupyter.org/documentation
- **Pandas Docs**: https://pandas.pydata.org/docs/
- **Matplotlib Docs**: https://matplotlib.org/stable/contents.html

## Questions?

- **For notebook usage**: See Jupyter documentation
- **For Chatforge APIs**: See `../devdocs/` and docstrings
- **For ChatTerm CLI**: Run `chatterm --help`
- **For testing strategy**: See `../devdocs/enhancements/chatterm/chatterm_implementation_high_lvl_plan.md`

---

**Remember**: Jupyter notebooks are for exploration and analysis. Use ChatTerm CLI for quick testing and CI/CD integration. Use both together for the best development experience!
