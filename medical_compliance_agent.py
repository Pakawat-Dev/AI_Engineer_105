import os
from typing import Annotated, List, Dict, Any, TypedDict
import functools
import operator
from dotenv import load_dotenv

# LangChain / LangGraph Imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# AutoGen Imports
import autogen

# --- Configuration ---
load_dotenv()

# LLM configurations for LangChain and AutoGen
llm_config_autogen = {
    "config_list": [{"model": "gpt-5-mini-2025-08-07", "api_key": os.environ["OPENAI_API_KEY"], "max_completion_tokens": 2500}],
}

llm_langchain = ChatOpenAI(model="gpt-5-nano-2025-08-07")

 
# --- MOCK Document Management System Tools (Stage 1 Data Loading) ---

@tool
def fetch_software_requirements_spec(user_request: str) -> str:
    """Fetches the Software Requirements Specification (SRS) based on user request."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a technical writer. Generate a Software Requirements Specification (SRS) document based on the user's medical device software request. Include sections: Functional Requirements, Performance Requirements, Security Requirements, Interface Requirements, and Safety Requirements with IEC 62304 traceability."),
        ("human", "{request}")
    ])
    chain = prompt | llm_langchain
    result = chain.invoke({"request": user_request})
    return result.content

@tool
def fetch_risk_management_file(user_request: str) -> str:
    """Fetches the Risk Management File (RMF) based on user request."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a risk management specialist. Generate a Risk Management File (RMF) document based on the user's medical device software request following ISO 14971. Include a table with columns: ID, Hazard, Cause, Current Control, Risk Level. Identify potential hazards related to the proposed changes."),
        ("human", "{request}")
    ])
    chain = prompt | llm_langchain
    result = chain.invoke({"request": user_request})
    return result.content


# --- LangGraph State Definition ---
# This defines the data structure passed between all stages of workflow.
class ComplianceState(TypedDict):
    user_request: str
    impacted_standards: List[str]
    loaded_documents: Dict[str, str]
    audit_findings: List[Dict[str, Any]]
    final_report_content: str
    # LangGraph message history needed for certain node types
    messages: Annotated[List[BaseMessage], operator.add]


# =========================================
# STAGE 1: Planning and Data Loading Nodes
# =========================================

def orchestrator_planner_node(state: ComplianceState):
    """
    Analyzes user input to determine impacted standards.
    Corresponds to 'Orchestrator (LLM Agent)' in workflow.
    """
    print(f"\n--- [Stage 1] Orchestrator: Planning Compliance Scope ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Regulatory Affairs expert. Analyze the user's requested change and list the medical device standards that are most likely impacted and need re-auditing. Return ONLY a comma-separated list of standards (e.g., 'IEC 62304, ISO 14971')."),
        ("human", "{request}")
    ])
    chain = prompt | llm_langchain
    result = chain.invoke({"request": state["user_request"]})
    standards_list = [s.strip() for s in result.content.split(",")]
    
    print(f"Impacted Standards identified: {standards_list}")
    return {"impacted_standards": standards_list}

def data_loading_node(state: ComplianceState):
    """
    Fetches necessary documents based on the plan.
    Corresponds to 'LoopAgent / Sheets tool / Data' in the workflow.
    """
    print(f"\n--- [Stage 1] Data Loader: Fetching Technical Documentation ---")
    docs = {}
    standards = state["impacted_standards"]
    
    # Read technical specification from file
    spec_file_path = "d:\\AI_Engineer_105\\test_medical_spec.md"
    technical_input = ""
    try:
        with open(spec_file_path, 'r', encoding='utf-8') as f:
            technical_input = f.read()
        print(f"Loaded technical specification from {spec_file_path}")
    except FileNotFoundError:
        print(f"Warning: {spec_file_path} not found, using user request only")
        technical_input = state["user_request"]
    
    # Combine technical spec with user request
    combined_input = f"Technical Specification:\n{technical_input}\n\nUser Request:\n{state['user_request']}"
    
    # Simple logic to decide what docs to fetch based on standards
    if any("62304" in s for s in standards):
        print("Fetching Software Requirements Spec due to IEC 62304 impact...")
        docs["SRS"] = fetch_software_requirements_spec.invoke({"user_request": combined_input})
        
    if any("14971" in s for s in standards):
        print("Fetching Risk Management File due to ISO 14971 impact...")
        docs["RMF"] = fetch_risk_management_file.invoke({"user_request": combined_input})
    
    if any("13485" in s for s in standards):
        print("Fetching Quality Management System documentation due to ISO 13485 impact...")
        docs["QMS"] = "QMS documentation placeholder"
        
    return {"loaded_documents": docs}


# =========================================
# STAGE 2: Iterative Research & QA Loop (AutoGen Integration)
# =========================================

def autogen_auditor_node(state: ComplianceState):
    """
    Bridging function. Spins up AutoGen agents to conduct the audit.
    Corresponds to the 'ResearchPipeline' box in workflow.
    """
    print(f"\n--- [Stage 2] AutoGen: Iterative Audit & QA Loop ---")
    
    loaded_docs_text = "\n\n".join([f"--- Document: {k} ---\n{v}" for k, v in state["loaded_documents"].items()])
    standards_to_audit = ", ".join(state["impacted_standards"])

    # 1. Define AutoGen Agents
    
    # The bridge agent between humans/LangGraph and the auditor agents
    user_proxy = autogen.UserProxyAgent(
        name="Compliance_Manager",
        system_message="A human compliance manager overseeing the audit process. Terminate chat when the audit is complete and findings are summarized.",
        human_input_mode="NEVER", # Fully automated for this pipeline loop
        code_execution_config=False,
        is_termination_msg=lambda x: "AUDIT_COMPLETE" in x.get("content", ""),
    )

    # Specialized IEC 62304 Auditor Agent
    software_auditor = autogen.AssistantAgent(
        name="IEC62304_Auditor",
        llm_config=llm_config_autogen,
        system_message="""You are an expert IEC 62304 Medical Device Software auditor.
        Your job is to review provided documentation against standard clauses 5-9.
        Identify gaps where documents do not meet the standard.
        Ensure traceability exists between requirements and risks.
        If satisfied, state COMPLIANT. If not, explicitly state NON-COMPLIANT and the reason.
        """
    )

    # Specialized ISO 14971 Auditor Agent
    risk_auditor = autogen.AssistantAgent(
        name="ISO14971_Auditor",
        llm_config=llm_config_autogen,
        system_message="""You are an expert ISO 14971 Risk Management auditor.
        Review the provided Risk Management File and ensure that new features identified in documentation have corresponding risk assessments.
        Ensure mitigations are verified.
        """
    )

    # Specialized ISO 13485 Auditor Agent
    qms_auditor = autogen.AssistantAgent(
        name="ISO13485_Auditor",
        llm_config=llm_config_autogen,
        system_message="""You are an expert ISO 13485 Quality Management System auditor.
        Review documentation for compliance with QMS requirements in clause 4-8.
        Verify that proper procedures are followed for medical device development.
        If satisfied, state COMPLIANT. If not, explicitly state NON-COMPLIANT and the reason.
        """
    )

    # The "Evaluation" and "Pass/Fail" logic from the blueprint happens in the group chat interaction.
    groupchat = autogen.GroupChat(
        agents=[user_proxy, software_auditor, risk_auditor, qms_auditor], 
        messages=[], 
        max_round=4
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config_autogen)

    # 2. Initiate the AutoGen Loop
    audit_prompt = f"""
    Please conduct a compliance audit for only the following standards: {standards_to_audit}.
    
    Here is the documentation to review:
    {loaded_docs_text}
    
    Auditors, be concise. Review your respective areas and collaborate if software changes affect risk.
    Summarize findings as "COMPLIANT" or "NON-COMPLIANT" for key clauses.
    End with "AUDIT_COMPLETE".
    """
    
    chat_result = user_proxy.initiate_chat(
        manager,
        message=audit_prompt
    )
    
    # 3. Extract results from AutoGen history to pass back to LangGraph
    # In a production system, you would use structured parsing here.
    # For this demo, we take the last informative message as the findings summary.
    final_summary_msg = next((msg['content'] for msg in reversed(chat_result.chat_history) if "AUDIT_COMPLETE" in msg['content']), "No summary found.")
    
    finding = {
        "stage": "Stage 2 Audit Loop",
        "details": final_summary_msg.replace("AUDIT_COMPLETE", "").strip()
    }

    return {"audit_findings": [finding], "messages": [HumanMessage(content=final_summary_msg)]}


# =========================================
# STAGE 3: Report Compilation and Briefing
# =========================================

def report_compiler_node(state: ComplianceState):
    """
    Generates the final formatted report.
    Corresponds to 'ReportCompiler' and 'Final Report' in the blueprint.
    """
    print(f"\n--- [Stage 3] Report Compiler: Generating Final Compliance Report ---")
    
    findings_text = "\n".join([f"- {f['details']}" for f in state["audit_findings"]])
    
    report_template = f"""
# Medical Device Compliance Audit Report

**Date:** 2026-01-27
**Trigger:** User Request - "{state['user_request']}"
**Scope:** {', '.join(state['impacted_standards'])}

## Executive Summary
An audit was conducted on the updated technical documentation. Below are the findings from the automated specialist agents.

## Audit Findings Summary

{findings_text}

## Next Actions
Review NON-COMPLIANT items and initiate CAPA (Corrective and Preventive Action) process if necessary. Update documentation before submission.
    """
    
    print("Report generated successfully.")
    # In a real app, you might save this to a .docx file here.
    return {"final_report_content": report_template}


# ===============================
# Building the LangGraph Workflow
# ===============================

workflow = StateGraph(ComplianceState)

# Add Nodes
workflow.add_node("planner", orchestrator_planner_node)
workflow.add_node("data_loader", data_loading_node)
workflow.add_node("autogen_auditor", autogen_auditor_node)
workflow.add_node("compiler", report_compiler_node)

# Define Flow (Edges) 
# Start -> Stage 1 (Planning)
workflow.set_entry_point("planner")

# Stage 1 -> Stage 1 Data Loading
workflow.add_edge("planner", "data_loader")

# Stage 1 Data -> Stage 2 (The Loop/Pipeline)
workflow.add_edge("data_loader", "autogen_auditor")

# Stage 2 -> Stage 3 (Reporting)
# Note: The internal "looping" happens *inside* the autogen_auditor_node's GroupChat.
# LangGraph manages the transition once AutoGen finishes its job.
workflow.add_edge("autogen_auditor", "compiler")

# Stage 3 -> End
workflow.add_edge("compiler", END)

# Compile the graph
app = workflow.compile()


if __name__ == "__main__":
    print("Medical Device Compliance Agent")
    print("Type 'quit' or 'exit' to stop\n")
    
    while True:
        user_input = input("Enter your compliance request: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("Exiting Compliance System.")
            break
            
        if not user_input:
            continue
        
        initial_state: ComplianceState = {
            "user_request": user_input,
            "impacted_standards": [],
            "loaded_documents": {},
            "audit_findings": [],
            "final_report_content": "",
            "messages": []
        }

        print(f"\nStarting Compliance System with input: '{user_input}'\n")
        
        final_state = app.invoke(initial_state)

        print("\n\n================ GENERATED FINAL REPORT ================\n")
        print(final_state["final_report_content"])
        print("========================================================\n")