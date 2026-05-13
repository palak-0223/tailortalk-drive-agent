import os
import json
from typing import Any, Dict, List, Optional, TypedDict, Annotated
import operator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from drive_tool import search_drive_files, build_query_from_params


# ─── Tool Definition ────────────────────────────────────────────────────────

@tool
def drive_search_tool(query: str, max_results: int = 15) -> str:
    """
    Search files in Google Drive using a properly formatted Drive API query string.

    The query string supports:
    - name = 'exact name'                        → exact file name match
    - name contains 'partial'                    → partial name match
    - mimeType = 'application/pdf'               → filter by file type
    - fullText contains 'keyword'                → search inside file content
    - modifiedTime > '2024-01-01T00:00:00'       → files modified after date
    - modifiedTime < '2024-12-31T23:59:59'       → files modified before date
    - Combine clauses with 'and' / 'or'

    Common MIME types:
    - PDF: application/pdf
    - Google Doc: application/vnd.google-apps.document
    - Google Sheet: application/vnd.google-apps.spreadsheet
    - Google Slides: application/vnd.google-apps.presentation
    - Image (JPEG): image/jpeg
    - Image (PNG): image/png

    Args:
        query: A valid Google Drive API q parameter string.
        max_results: Maximum number of files to return (default 15).

    Returns:
        JSON string with list of matching files.
    """
    try:
        files = search_drive_files(query_string=query, max_results=max_results)
        if not files:
            return json.dumps({"found": 0, "files": [], "message": "No files found matching your query."})
        return json.dumps({"found": len(files), "files": files})
    except Exception as e:
        return json.dumps({"error": str(e), "found": 0, "files": []})


TOOLS = [drive_search_tool]


# ─── LLM Setup ───────────────────────────────────────────────────────────────

def get_llm():
    """Return the configured LLM with tool binding."""
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()

    if provider == "openai":
        llm = ChatOpenAI(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.environ.get("OPENAI_API_KEY"),
            temperature=0,
        )
    elif provider == "gemini":
        llm = ChatGoogleGenerativeAI(
            model=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            temperature=0,
        )
    else:  # default: groq
        llm = ChatGroq(
            model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0,
        )

    return llm.bind_tools(TOOLS)


# ─── Agent State ─────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[List[Any], operator.add]
    files_found: List[dict]


# ─── System Prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are TailorTalk, an intelligent Google Drive file discovery assistant. Your job is to help users find files in their Google Drive through natural, friendly conversation.

## Your Capabilities
You can search Google Drive files by:
- **Name**: Exact or partial file name matching
- **Type**: PDFs, Google Docs, Sheets, Slides, Images, etc.
- **Content**: Keywords inside document text (fullText)
- **Date**: Files modified before/after a specific date
- **Combinations**: Mix any of the above

## How to Search
When a user asks to find files, you MUST call the `drive_search_tool` with a properly formatted Google Drive API query string.

### Query Examples:
| User Request | Query String |
|---|---|
| "Find budget spreadsheets" | `name contains 'budget' and mimeType = 'application/vnd.google-apps.spreadsheet'` |
| "Show me all PDFs" | `mimeType = 'application/pdf'` |
| "Files about marketing" | `fullText contains 'marketing'` |
| "Recent docs from this month" | `mimeType = 'application/vnd.google-apps.document' and modifiedTime > '2025-05-01T00:00:00'` |
| "Find invoice PDF" | `name contains 'invoice' and mimeType = 'application/pdf'` |
| "Images uploaded last week" | `mimeType = 'image/jpeg' and modifiedTime > '2025-05-06T00:00:00'` |

### MIME Types Reference:
- PDF: `application/pdf`
- Google Doc: `application/vnd.google-apps.document`
- Google Sheet: `application/vnd.google-apps.spreadsheet`
- Google Slides: `application/vnd.google-apps.presentation`
- JPEG Image: `image/jpeg`
- PNG Image: `image/png`
- Text file: `text/plain`
- CSV: `text/csv`

## Response Style
- Be friendly, concise, and helpful
- After getting search results, summarize what you found clearly
- If no files are found, suggest alternative search strategies
- Ask clarifying questions if the request is ambiguous
- Provide clickable links when files are found
- Format file lists in a readable way

## Important Notes
- Always translate natural language into proper Drive API query syntax
- Combine clauses with `and` or `or`
- String values in queries must be wrapped in single quotes
- Dates must be in RFC 3339 format: `YYYY-MM-DDTHH:MM:SS`
- Do NOT add trashed = false — it's handled automatically
- Keep conversations natural and helpful
"""


# ─── Graph Nodes ─────────────────────────────────────────────────────────────

def should_continue(state: AgentState) -> str:
    """Decide whether to call tools or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def call_model(state: AgentState) -> AgentState:
    """Call the LLM with current state."""
    llm = get_llm()
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response], "files_found": state.get("files_found", [])}


def process_tool_results(state: AgentState) -> AgentState:
    """Extract file data from tool results."""
    files_found = []
    for msg in reversed(state["messages"]):
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                if "files" in data:
                    files_found = data["files"]
            except Exception:
                pass
            break
    return {"messages": [], "files_found": files_found}


# ─── Build Graph ─────────────────────────────────────────────────────────────

def build_agent_graph():
    tool_node = ToolNode(TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.add_node("process_tools", process_tool_results)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "process_tools")
    graph.add_edge("process_tools", "agent")

    return graph.compile()


# ─── DriveAgent Class ─────────────────────────────────────────────────────────

class DriveAgent:
    def __init__(self):
        self.graph = build_agent_graph()
        self.system_message = SystemMessage(content=SYSTEM_PROMPT)

    async def chat(self, user_message: str, history: List[Dict]) -> Dict:
        """Process a chat message and return response with any found files."""
        messages = [self.system_message]

        # Add conversation history
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        # Run agent
        state = await self.graph.ainvoke(
            {"messages": messages, "files_found": []},
            config={"recursion_limit": 10},
        )

        # Extract final AI response
        final_response = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                final_response = msg.content
                break

        return {
            "response": final_response or "I encountered an issue processing your request. Please try again.",
            "files": state.get("files_found", []),
        }
