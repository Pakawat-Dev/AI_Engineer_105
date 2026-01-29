# AI_Engineer_105
Automated compliance auditing system for medical device software using LangGraph and AutoGen multi-agent framework.
## Overview

This agent automates compliance auditing for medical device software against regulatory standards (IEC 62304, ISO 14971, ISO 13485). It uses AI agents to analyze documentation, identify gaps, and generate compliance reports.

## Architecture

**3-Stage Pipeline:**
1. **Planning & Data Loading** - Identifies impacted standards and fetches documentation
2. **Iterative Audit** - Multi-agent collaboration for compliance review
3. **Report Generation** - Compiles findings into audit report

## Prerequisites

- Python 3.10+
- OpenAI API key

## Step-by-Step Setup

### Step 1: Clone/Download the Project

```bash
cd AI_Engineer_105
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
```

### Step 3: Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Unix/macOS:**
```bash
source .venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

### Step 6: Prepare Technical Specification (Optional)

The agent reads technical details from `test_medical_spec.md`. You can:
- Use the provided sample specification
- Modify it for your medical device
- Create your own specification file

### Step 7: Run the Agent

```bash
python medical_compliance_agent.py
```

## Usage

### Interactive Mode

1. Run the script
2. Enter your compliance request when prompted
3. Wait for the agent to process (3 stages)
4. Review the generated compliance report
5. Type 'quit' or 'exit' to stop

### Example Input

```
We are developing Stress Monitoring System v3.0 with cloud integration, 
AI-based stress detection, mobile app, upgraded AES-256 encryption, 
and multi-user access with role-based permissions.
```

### Example Output

The agent will:
- Identify impacted standards (IEC 62304, ISO 14971, ISO 13485)
- Load technical specification from `test_medical_spec.md`
- Generate SRS and RMF documents based on combined input
- Run 3 specialized auditor agents
- Produce a compliance audit report with COMPLIANT/NON-COMPLIANT findings

## Agent Components

### Stage 1: Planning
- **Orchestrator** - Analyzes request and identifies standards
- **Data Loader** - Reads technical specification and generates documentation

### Stage 2: Audit Loop (AutoGen)
- **IEC62304_Auditor** - Software lifecycle compliance
- **ISO14971_Auditor** - Risk management compliance
- **ISO13485_Auditor** - Quality management compliance
- **Compliance_Manager** - Oversees audit process

### Stage 3: Reporting
- **Report Compiler** - Generates final audit report

## Configuration

### Token Limits
- Max completion tokens: 2500 per agent response
- Max rounds: 4 iterations in audit loop

### Technical Specification File
- Location: `test_medical_spec.md`
- Format: Markdown
- Sections: Product Overview, Proposed Changes, Technical Requirements, Safety Considerations

### Supported Standards
- IEC 62304 (Medical Device Software)
- ISO 14971 (Risk Management)
- ISO 13485 (Quality Management Systems)

## File Structure

```
AI_Engineer_105/
├── medical_compliance_agent.py    # Main agent script
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── test_medical_spec.md          # Technical specification (input)
└── README.md                     # This file
```

## How It Works

1. **User Input**: Enter a brief compliance request
2. **Technical Spec Loading**: Agent reads detailed requirements from `test_medical_spec.md`
3. **Standard Identification**: AI identifies which regulatory standards are impacted
4. **Document Generation**: AI generates SRS and RMF documents using LLM
5. **Multi-Agent Audit**: Three specialized auditor agents review documents
6. **Report Generation**: Findings compiled into compliance audit report

## Troubleshooting

### Issue: OpenAI API Error
**Solution:** Verify your API key in `.env` file

### Issue: Module Not Found
**Solution:** Ensure virtual environment is activated and dependencies installed

### Issue: Agent Doesn't Terminate
**Solution:** Check that agents include "AUDIT_COMPLETE" in final message

### Issue: File Not Found (test_medical_spec.md)
**Solution:** Ensure `test_medical_spec.md` exists in the project root. Agent will fall back to user request only if file is missing.

## Customization

### Add New Standards
1. Add condition in `data_loading_node()`
2. Create new auditor agent in `autogen_auditor_node()`
3. Add agent to `groupchat`

### Modify Token Limits
Update `max_completion_tokens` in `llm_config_autogen`

### Change Audit Rounds
Update `max_round` in `groupchat` initialization

### Update Technical Specification Path
Modify `spec_file_path` in `data_loading_node()` function

## Dependencies

- `langchain-core` - LangChain framework
- `langchain-openai` - OpenAI integration
- `langgraph` - Graph-based workflows
- `autogen` - Multi-agent framework
- `autogen-agentchat` - AutoGen agent chat
- `autogen-ext[openai]` - AutoGen OpenAI extension
- `python-dotenv` - Environment management
- `openai` - OpenAI API client

## Notes

- This is a demonstration system with AI-generated documentation
- Technical specifications are read from `test_medical_spec.md` for realistic audits
- In production, connect to real document management systems (Jira, Confluence, SharePoint)
- Audit findings should be reviewed by qualified regulatory professionals
- Token usage is controlled to optimize costs
