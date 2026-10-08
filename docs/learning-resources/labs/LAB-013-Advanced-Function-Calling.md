---
Document ID: LAB-013
Title: "LAB-013: Advanced Function Calling"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 7 hours
Tags: ['lab', 'function-calling', 'agents', 'hands-on']
---

# LAB-013: Advanced Function Calling

**Master Tool Use and Orchestration in AI Systems**

---

## Lab Overview

**Time:** 5-6 hours

**Difficulty:** ⭐⭐⭐ Advanced

**Prerequisites:**

- LAB-004: ReAct Agent
- LAB-008: Agent Fleet
- Understanding of JSON schemas
- API development experience

**Learning Objectives:**

- Master OpenAI function calling
- Build sophisticated LangChain tools
- Design custom tool systems
- Implement multi-tool orchestration
- Handle tool errors gracefully
- Deploy tool-enabled agents in production

---

## What You'll Build

By the end of this lab, you will have:

1. **15+ Production Tools** - Database, API, file, web tools
2. **Tool Orchestration Engine** - Coordinate multiple tools
3. **Dynamic Tool Selection** - Choose tools intelligently
4. **Error Recovery System** - Handle tool failures
5. **Production Tool API** - Deployed with monitoring

---

## Part 1: OpenAI Function Calling (120 minutes)

### Understanding Function Calling

Function calling allows LLMs to interact with external tools by outputting structured JSON instead of natural language.

```python
# File: function_calling_foundation.py
"""
OpenAI Function Calling - Complete Implementation
=================================================

Function calling flow:
1. User sends message
2. LLM decides which function to call
3. LLM outputs function name + arguments (JSON)
4. System executes function
5. Results sent back to LLM
6. LLM generates final response
"""

import json
import inspect
from typing import Any, Callable
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from enum import Enum

class ToolRole(Enum):
    """Tool role categories"""
    DATA_ACCESS = "data_access"
    API_CALL = "api_call"
    COMPUTATION = "computation"
    FILE_OPS = "file_ops"
    SEARCH = "search"
    VALIDATION = "validation"

@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    enum: list[Any] | None = None
    default: Any | None = None
    format: str | None = None  # For additional type info

@dataclass
class Tool:
    """Complete tool definition"""
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    function: Callable = None
    role: ToolRole = ToolRole.API_CALL
    examples: list[dict] = field(default_factory=list)
    rate_limit: int | None = None  # Max calls per minute
    timeout: int = 30  # Timeout in seconds
    async_function: bool = False

    def to_openai_schema(self) -> dict:
        """Convert to OpenAI function calling schema"""
        properties = {}
        required = []

        for param in self.parameters:
            prop_def = {
                "type": param.type,
                "description": param.description
            }

            if param.enum:
                prop_def["enum"] = param.enum
            if param.default is not None:
                prop_def["default"] = param.default
            if param.format:
                prop_def["format"] = param.format

            properties[param.name] = prop_def

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def execute(self, **kwargs) -> Any:
        """Execute the tool"""
        if self.function is None:
            raise ValueError(f"Tool {self.name} has no function defined")

        # Validate parameters
        self._validate_parameters(kwargs)

        # Execute
        try:
            result = self.function(**kwargs)
            return {
                "success": True,
                "result": result,
                "tool": self.name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": self.name
            }

    def _validate_parameters(self, params: dict):
        """Validate parameters against schema"""
        provided = set(params.keys())
        required = {p.name for p in self.parameters if p.required}

        missing = required - provided
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

        # Type validation (basic)
        for param in self.parameters:
            if param.name in params:
                value = params[param.name]

                # Check enum
                if param.enum and value not in param.enum:
                    raise ValueError(
                        f"Parameter {param.name} must be one of {param.enum}"
                    )

class ToolRegistry:
    """
    Registry for managing tools.
    """

    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self.tools_by_role: dict[ToolRole, list[str]] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool"""
        self.tools[tool.name] = tool

        if tool.role not in self.tools_by_role:
            self.tools_by_role[tool.role] = []
        self.tools_by_role[tool.role].append(tool.name)

    def get_tool(self, name: str) -> Tool | None:
        """Get tool by name"""
        return self.tools.get(name)

    def get_tools_by_role(self, role: ToolRole) -> list[Tool]:
        """Get all tools for a role"""
        names = self.tools_by_role.get(role, [])
        return [self.tools[name] for name in names]

    def list_tools(self) -> list[str]:
        """List all tool names"""
        return list(self.tools.keys())

    def to_openai_schemas(self) -> list[dict]:
        """Convert all tools to OpenAI schemas"""
        return [tool.to_openai_schema() for tool in self.tools.values()]

class FunctionCallingEngine:
    """
    Complete function calling engine.
    """

    def __init__(
        self,
        client,
        tool_registry: ToolRegistry,
        model: str = "gpt-4"
    ):
        """
        Initialize function calling engine.

        Args:
            client: OpenAI client or compatible
            tool_registry: Tool registry
            model: Model name
        """
        self.client = client
        self.registry = tool_registry
        self.model = model
        self.conversation_history = []

    def chat(
        self,
        user_message: str,
        available_tools: list[str] | None = None,
        max_iterations: int = 10
    ) -> dict:
        """
        Chat with function calling.

        Args:
            user_message: User's message
            available_tools: Tools to make available (None = all)
            max_iterations: Maximum tool call iterations

        Returns:
            Final response with execution trace
        """
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Determine available tools
        if available_tools is None:
            tools = self.registry.to_openai_schemas()
        else:
            tools = [
                self.registry.get_tool(name).to_openai_schema()
                for name in available_tools
            ]

        trace = []

        for iteration in range(max_iterations):
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                tools=tools,
                tool_choice="auto"
            )

            message = response.choices[0].message

            # Check for tool calls
            if not message.tool_calls:
                # No more tool calls, final response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content
                })

                return {
                    "response": message.content,
                    "trace": trace,
                    "iterations": iteration + 1
                }

            # Execute tool calls
            tool_calls = message.tool_calls
            self.conversation_history.append({
                "role": "assistant",
                "tool_calls": tool_calls,
                "content": message.content or ""
            })

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                trace.append({
                    "iteration": iteration,
                    "tool": tool_name,
                    "arguments": tool_args
                })

                # Execute tool
                tool = self.registry.get_tool(tool_name)
                if tool is None:
                    result = {
                        "success": False,
                        "error": f"Unknown tool: {tool_name}"
                    }
                else:
                    result = tool.execute(**tool_args)

                trace[-1]["result"] = result

                # Add tool response to conversation
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        # Max iterations reached
        return {
            "response": "Maximum iterations reached",
            "trace": trace,
            "iterations": max_iterations
        }

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

# Tool decorators for easy definition
def tool(
    name: str,
    description: str,
    parameters: list[ToolParameter],
    role: ToolRole = ToolRole.API_CALL
):
    """
    Decorator to create a tool from a function.

    Usage:
    @tool(
        name="search_web",
        description="Search the web for information",
        parameters=[
            ToolParameter("query", "string", "Search query"),
            ToolParameter("num_results", "number", "Number of results", required=False, default=5)
        ]
    )
    def search_web(query: str, num_results: int = 5):
        # Implementation
        pass
    """
    def decorator(func):
        return Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=func,
            role=role
        )
    return decorator

# Example tools
@tool(
    name="get_weather",
    description="Get current weather for a location",
    parameters=[
        ToolParameter("location", "string", "City name or zip code"),
        ToolParameter("unit", "string", "Temperature unit (celsius or fahrenheit)", required=False, default="celsius", enum=["celsius", "fahrenheit"])
    ],
    role=ToolRole.API_CALL
)
def get_weather(location: str, unit: str = "celsius") -> dict:
    """Get weather for location"""
    # Mock implementation
    import random

    temp = random.randint(10, 30)
    if unit == "fahrenheit":
        temp = temp * 9/5 + 32

    conditions = random.choice(["Sunny", "Cloudy", "Rainy", "Partly cloudy"])

    return {
        "location": location,
        "temperature": temp,
        "unit": unit,
        "conditions": conditions,
        "humidity": random.randint(30, 80)
    }

@tool(
    name="calculate",
    description="Perform mathematical calculations",
    parameters=[
        ToolParameter("expression", "string", "Mathematical expression to evaluate")
    ],
    role=ToolRole.COMPUTATION
)
def calculate(expression: str) -> dict:
    """Safely calculate mathematical expression"""
    try:
        # Only allow safe operations
        allowed_chars = set("0123456789+-*/(). ")

        if not all(c in allowed_chars or c.isalnum() for c in expression):
            return {"error": "Invalid characters in expression"}

        result = eval(expression, {"__builtins__": {}}, {})

        return {
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="search_database",
    description="Search for records in database",
    parameters=[
        ToolParameter("table", "string", "Table name to search"),
        ToolParameter("filters", "object", "Search filters as JSON object", required=False, default={}),
        ToolParameter("limit", "number", "Maximum results", required=False, default=10)
    ],
    role=ToolRole.DATA_ACCESS
)
def search_database(table: str, filters: dict | None = None, limit: int = 10) -> dict:
    """Search database table"""
    # Mock implementation
    return {
        "table": table,
        "filters": filters,
        "results": [
            {"id": 1, "name": f"Record {i}"}
            for i in range(min(limit, 5))
        ],
        "count": min(limit, 5)
    }

# Demo
if __name__ == "__main__":
    from openai import OpenAI

    # Initialize
    client = OpenAI()
    registry = ToolRegistry()

    # Register tools
    registry.register(Tool(
        name="get_weather",
        description="Get current weather for a location",
        parameters=[
            ToolParameter("location", "string", "City name"),
            ToolParameter("unit", "string", "Temperature unit", required=False, default="celsius")
        ],
        function=lambda location, unit="celsius": {
            "location": location,
            "temperature": 22,
            "unit": unit,
            "conditions": "Sunny"
        }
    ))

    registry.register(Tool(
        name="calculate",
        description="Calculate mathematical expression",
        parameters=[
            ToolParameter("expression", "string", "Expression to calculate")
        ],
        function=calculate.function
    ))

    # Create engine
    engine = FunctionCallingEngine(client, registry)

    # Test
    result = engine.chat("What's the weather in Istanbul?")
    print("\n=== Response ===")
    print(result["response"])
    print("\n=== Trace ===")
    for step in result["trace"]:
        print(f"{step['tool']}: {step['result']}")
```

**Checkpoint 1:** ✅ Function calling foundation working

---

## Part 2: Advanced Tool Development (120 minutes)

### Building Production Tools

```python
# File: production_tools.py
"""
Production-Ready Tool Suite
===========================

Categories:
- Database Tools (PostgreSQL, MongoDB, Redis)
- API Tools (REST, GraphQL)
- File Tools (S3, local filesystem)
- Web Tools (scraping, search)
- Validation Tools
"""

import os
import json
import hashlib
import requests
from typing import Any
from datetime import datetime, timedelta
import sqlite3
from functools import wraps
import time

# Rate limiting decorator
def rate_limit(max_calls: int = 10, period: int = 60):
    """
    Rate limit decorator.

    Args:
        max_calls: Maximum calls allowed
        period: Time period in seconds
    """
    calls = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()

            # Remove old calls
            calls[:] = [c for c in calls if c > now - period]

            if len(calls) >= max_calls:
                wait_time = period - (now - calls[0])
                raise Exception(f"Rate limit exceeded. Wait {wait_time:.1f}s")

            calls.append(now)
            return func(*args, **kwargs)

        return wrapper

    return decorator

# Retry decorator
def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator for resilient tool execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (attempt + 1))

            raise last_exception

        return wrapper

    return decorator

# ============= DATABASE TOOLS =============

class PostgreSQLTool:
    """PostgreSQL database operations"""

    def __init__(self, connection_string: str):
        import psycopg2
        self.conn = psycopg2.connect(connection_string)

    @retry(max_attempts=3)
    @rate_limit(max_calls=20, period=60)
    def query(self, sql: str, params: tuple | None = None) -> list[dict]:
        """Execute SQL query"""
        cursor = self.conn.cursor()
        cursor.execute(sql, params or ())

        # Get column names
        columns = [desc[0] for desc in cursor.description]

        # Fetch results
        rows = cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    def execute(self, sql: str, params: tuple | None = None) -> dict:
        """Execute SQL statement"""
        cursor = self.conn.cursor()
        cursor.execute(sql, params or ())
        self.conn.commit()

        return {
            "rows_affected": cursor.rowcount,
            "success": True
        }

class RedisTool:
    """Redis cache operations"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        import redis
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    @rate_limit(max_calls=100, period=60)
    def get(self, key: str) -> str | None:
        """Get value from Redis"""
        return self.client.get(key)

    @rate_limit(max_calls=100, period=60)
    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in Redis"""
        return self.client.setex(key, ttl, value) if ttl else self.client.set(key, value)

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        return self.client.delete(key) > 0

# ============= API TOOLS =============

class HTTPTool:
    """HTTP API client with error handling"""

    def __init__(self, base_url: str = None, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()

    @retry(max_attempts=3, delay=0.5)
    def get(
        self,
        endpoint: str,
        params: dict | None = None,
        headers: dict | None = None
    ) -> dict:
        """Make GET request"""
        url = f"{self.base_url}/{endpoint}" if self.base_url else endpoint

        response = self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=self.timeout
        )

        response.raise_for_status()

        return {
            "status": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }

    @retry(max_attempts=3, delay=0.5)
    def post(
        self,
        endpoint: str,
        data: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None
    ) -> dict:
        """Make POST request"""
        url = f"{self.base_url}/{endpoint}" if self.base_url else endpoint

        response = self.session.post(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=self.timeout
        )

        response.raise_for_status()

        return {
            "status": response.status_code,
            "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }

# ============= FILE TOOLS =============

class FileTool:
    """File system operations"""

    def __init__(self, base_path: str = "."):
        self.base_path = os.path.abspath(base_path)
        # Ensure base path exists
        os.makedirs(self.base_path, exist_ok=True)

    def read(self, filepath: str) -> dict:
        """Read file content"""
        full_path = os.path.join(self.base_path, filepath)

        # Security check
        if not os.path.abspath(full_path).startswith(self.base_path):
            raise ValueError("Access denied: path outside base directory")

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "path": filepath,
            "content": content,
            "size": len(content)
        }

    def write(self, filepath: str, content: str) -> dict:
        """Write content to file"""
        full_path = os.path.join(self.base_path, filepath)

        # Security check
        if not os.path.abspath(full_path).startswith(self.base_path):
            raise ValueError("Access denied: path outside base directory")

        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "path": filepath,
            "size": len(content),
            "success": True
        }

    def list_dir(self, dirpath: str = ".") -> list[dict]:
        """List directory contents"""
        full_path = os.path.join(self.base_path, dirpath)

        if not os.path.exists(full_path):
            raise ValueError(f"Directory not found: {dirpath}")

        items = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            items.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
            })

        return items

class S3Tool:
    """AWS S3 operations"""

    def __init__(self, bucket: str, region: str = "us-east-1"):
        import boto3
        self.s3 = boto3.client('s3', region_name=region)
        self.bucket = bucket

    @retry(max_attempts=3)
    def upload(self, key: str, filepath: str) -> dict:
        """Upload file to S3"""
        self.s3.upload_file(filepath, self.bucket, key)

        return {
            "bucket": self.bucket,
            "key": key,
            "success": True
        }

    @retry(max_attempts=3)
    def download(self, key: str, filepath: str) -> dict:
        """Download file from S3"""
        self.s3.download_file(self.bucket, key, filepath)

        return {
            "bucket": self.bucket,
            "key": key,
            "path": filepath,
            "success": True
        }

    def list_objects(self, prefix: str = "") -> list[dict]:
        """List objects in bucket"""
        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix
        )

        objects = []
        for obj in response.get("Contents", []):
            objects.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"]
            })

        return objects

# ============= WEB TOOLS =============

class WebSearchTool:
    """Web search using various APIs"""

    def __init__(self, api_key: str = None, engine: str = "google"):
        self.api_key = api_key
        self.engine = engine

    @rate_limit(max_calls=10, period=60)
    def search(self, query: str, num_results: int = 10) -> list[dict]:
        """Search the web"""
        # Mock implementation - replace with actual API
        return [
            {
                "title": f"Result {i} for '{query}'",
                "url": f"https://example.com/{i}",
                "snippet": f"This is result {i}"
            }
            for i in range(num_results)
        ]

class WebScraperTool:
    """Web scraping with BeautifulSoup"""

    def __init__(self):
        from bs4 import BeautifulSoup
        self.BeautifulSoup = BeautifulSoup

    @rate_limit(max_calls=5, period=60)
    def scrape(self, url: str, selectors: dict | None = None) -> dict:
        """Scrape web page"""
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = self.BeautifulSoup(response.content, 'html.parser')

        results = {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "extracted": {}
        }

        if selectors:
            for name, selector in selectors.items():
                elements = soup.select(selector)
                results["extracted"][name] = [e.get_text(strip=True) for e in elements]

        return results

# ============= VALIDATION TOOLS =============

class ValidationTool:
    """Data validation utilities"""

    @staticmethod
    def validate_email(email: str) -> dict:
        """Validate email address"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        is_valid = bool(re.match(pattern, email))

        return {
            "email": email,
            "valid": is_valid
        }

    @staticmethod
    def validate_phone(phone: str, country: str = "US") -> dict:
        """Validate phone number"""
        import phonenumbers

        try:
            parsed = phonenumbers.parse(phone, country)
            is_valid = phonenumbers.is_valid_number(parsed)

            return {
                "phone": phone,
                "valid": is_valid,
                "formatted": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL) if is_valid else None
            }
        except Exception:
            return {
                "phone": phone,
                "valid": False
            }

    @staticmethod
    def validate_json(data: str) -> dict:
        """Validate JSON string"""
        try:
            parsed = json.loads(data)
            return {
                "valid": True,
                "parsed": parsed
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": str(e)
            }

# ============= TOOL FACTORY =============

class ToolFactory:
    """Factory for creating tool instances"""

    @staticmethod
    def create_tool(tool_type: str, config: dict | None = None) -> Any:
        """
        Create tool instance.

        Args:
            tool_type: The kind of tool to create
            config: Configuration dictionary

        Returns:
            Tool instance
        """
        config = config or {}

        if tool_type == "postgresql":
            return PostgreSQLTool(config.get("connection_string"))
        elif tool_type == "redis":
            return RedisTool(
                host=config.get("host", "localhost"),
                port=config.get("port", 6379),
                db=config.get("db", 0)
            )
        elif tool_type == "http":
            return HTTPTool(
                base_url=config.get("base_url"),
                timeout=config.get("timeout", 30)
            )
        elif tool_type == "file":
            return FileTool(base_path=config.get("base_path", "."))
        elif tool_type == "s3":
            return S3Tool(
                bucket=config["bucket"],
                region=config.get("region", "us-east-1")
            )
        elif tool_type == "web_search":
            return WebSearchTool(
                api_key=config.get("api_key"),
                engine=config.get("engine", "google")
            )
        elif tool_type == "web_scraper":
            return WebScraperTool()
        elif tool_type == "validation":
            return ValidationTool()
        else:
            raise ValueError(f"Unknown tool type: {tool_type}")

# Demo
if __name__ == "__main__":
    # File tool demo
    file_tool = ToolFactory.create_tool("file", {"base_path": "./data"})

    # Write file
    file_tool.write("test.txt", "Hello, World!")
    print("✓ File written")

    # Read file
    content = file_tool.read("test.txt")
    print(f"✓ File read: {content['content']}")

    # List directory
    items = file_tool.list_dir()
    print(f"✓ Directory listed: {len(items)} items")

    # HTTP tool demo
    http_tool = ToolFactory.create_tool("http", {"base_url": "https://api.github.com"})
    result = http_tool.get("repos/anthropics/claude-code")
    print(f"\n✓ API call: {result['status']}")

    # Validation tool demo
    validation_tool = ToolFactory.create_tool("validation")
    email_result = validation_tool.validate_email("test@example.com")
    print(f"\n✓ Email validation: {email_result['valid']}")
```

**Checkpoint 2:** ✅ Advanced tools working

---

## Part 3: Tool Orchestration (90 minutes)

### Coordinating Multiple Tools

```python
# File: tool_orchestration.py
"""
Tool Orchestration Engine
=========================

Coordinates multiple tools:
- Parallel execution
- Dependency resolution
- Error recovery
- Result aggregation
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

class ExecutionStrategy(Enum):
    """Tool execution strategy"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DEPENDENCY_GRAPH = "dependency_graph"

@dataclass
class ToolCall:
    """Single tool call definition"""
    tool_name: str
    parameters: dict[str, Any]
    depends_on: list[str] = field(default_factory=list)
    retry_on_failure: bool = True
    continue_on_failure: bool = False
    timeout: int = 30

@dataclass
class ExecutionResult:
    """Result of tool execution"""
    tool_name: str
    success: bool
    result: Any = None
    error: str | None = None
    duration: float = 0.0

class ToolOrchestrator:
    """
    Orchestrates execution of multiple tools.
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry
        self.executor = ThreadPoolExecutor(max_workers=10)

    def execute_plan(
        self,
        calls: list[ToolCall],
        strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    ) -> list[ExecutionResult]:
        """
        Execute a plan of tool calls.

        Args:
            calls: The tool calls to execute
            strategy: Execution strategy

        Returns:
            The execution results
        """
        if strategy == ExecutionStrategy.SEQUENTIAL:
            return self._execute_sequential(calls)
        elif strategy == ExecutionStrategy.PARALLEL:
            return self._execute_parallel(calls)
        elif strategy == ExecutionStrategy.DEPENDENCY_GRAPH:
            return self._execute_with_dependencies(calls)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _execute_sequential(
        self,
        calls: list[ToolCall]
    ) -> list[ExecutionResult]:
        """Execute calls sequentially"""
        results = []

        for call in calls:
            result = self._execute_call(call)
            results.append(result)

            if not result.success and not call.continue_on_failure:
                break

        return results

    def _execute_parallel(
        self,
        calls: list[ToolCall]
    ) -> list[ExecutionResult]:
        """Execute calls in parallel"""
        futures = {}
        results = {}

        # Submit all calls
        for call in calls:
            future = self.executor.submit(self._execute_call, call)
            futures[future] = call

        # Collect results
        for future in as_completed(futures):
            call = futures[future]
            try:
                result = future.result(timeout=call.timeout)
                results[call.tool_name] = result
            except Exception as e:
                results[call.tool_name] = ExecutionResult(
                    tool_name=call.tool_name,
                    success=False,
                    error=str(e)
                )

        # Return in original order
        return [results[call.tool_name] for call in calls]

    def _execute_with_dependencies(
        self,
        calls: list[ToolCall]
    ) -> list[ExecutionResult]:
        """Execute calls respecting dependencies"""
        # Build dependency graph
        graph = self._build_dependency_graph(calls)

        # Execute in topological order
        execution_order = self._topological_sort(graph)

        results_map = {}

        for call_name in execution_order:
            call = next(c for c in calls if c.tool_name == call_name)

            # Check if dependencies succeeded
            dependencies_met = all(
                results_map.get(dep, ExecutionResult(dep, True)).success
                for dep in call.depends_on
            )

            if not dependencies_met:
                results_map[call_name] = ExecutionResult(
                    tool_name=call_name,
                    success=False,
                    error="Dependencies failed"
                )
                continue

            # Execute call
            result = self._execute_call(call)
            results_map[call_name] = result

            if not result.success and not call.continue_on_failure:
                break

        return [results_map[call.tool_name] for call in calls]

    def _execute_call(self, call: ToolCall) -> ExecutionResult:
        """Execute a single tool call"""
        import time
        start_time = time.time()

        tool = self.registry.get_tool(call.tool_name)
        if tool is None:
            return ExecutionResult(
                tool_name=call.tool_name,
                success=False,
                error=f"Tool not found: {call.tool_name}"
            )

        try:
            result = tool.execute(**call.parameters)
            duration = time.time() - start_time

            return ExecutionResult(
                tool_name=call.tool_name,
                success=result.get("success", True),
                result=result,
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                tool_name=call.tool_name,
                success=False,
                error=str(e),
                duration=duration
            )

    def _build_dependency_graph(self, calls: list[ToolCall]) -> dict[str, list[str]]:
        """Build dependency graph from calls"""
        graph = {call.tool_name: call.depends_on for call in calls}
        return graph

    def _topological_sort(self, graph: dict[str, list[str]]) -> list[str]:
        """Topological sort of dependency graph"""
        visited = set()
        result = []

        def visit(node):
            if node in visited:
                return
            visited.add(node)

            for dep in graph.get(node, []):
                visit(dep)

            result.append(node)

        for node in graph:
            visit(node)

        return result

class Workflow:
    """
    Complex workflow orchestration.
    """

    def __init__(self, orchestrator: ToolOrchestrator):
        self.orchestrator = orchestrator
        self.steps = []
        self.context = {}

    def add_step(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        depends_on: list[str] = None,
        store_as: str = None
    ) -> 'Workflow':
        """Add a step to the workflow"""
        step = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            depends_on=depends_on or []
        )

        self.steps.append(step)

        if store_as:
            step.store_as = store_as

        return self

    def execute(self) -> dict:
        """Execute the workflow"""
        results = self.orchestrator.execute_plan(
            self.steps,
            strategy=ExecutionStrategy.DEPENDENCY_GRAPH
        )

        # Update context with results
        for i, result in enumerate(results):
            if hasattr(self.steps[i], 'store_as'):
                self.context[self.steps[i].store_as] = result.result

        return {
            "results": results,
            "context": self.context
        }

# Demo workflows
if __name__ == "__main__":
    # Create registry and orchestrator
    registry = ToolRegistry()
    orchestrator = ToolOrchestrator(registry)

    # Register some tools
    registry.register(Tool(
        name="fetch_data",
        description="Fetch data from API",
        parameters=[
            ToolParameter("url", "string", "API endpoint URL")
        ],
        function=lambda url: {"data": [1, 2, 3, 4, 5]}
    ))

    registry.register(Tool(
        name="transform_data",
        description="Transform data",
        parameters=[
            ToolParameter("data", "array", "Input data"),
            ToolParameter("operation", "string", "Operation to apply")
        ],
        function=lambda data, operation: {
            "result": [x * 2 for x in data] if operation == "double" else data
        }
    ))

    registry.register(Tool(
        name="save_data",
        description="Save data to storage",
        parameters=[
            ToolParameter("data", "array", "Data to save"),
            ToolParameter("location", "string", "Storage location")
        ],
        function=lambda data, location: {"saved": True, "count": len(data)}
    ))

    # Create workflow
    workflow = Workflow(orchestrator)
    workflow.add_step(
        "fetch_data",
        {"url": "https://api.example.com/data"},
        store_as="raw_data"
    )
    workflow.add_step(
        "transform_data",
        {"data": "${raw_data.data}", "operation": "double"},
        depends_on=["fetch_data"],
        store_as="transformed_data"
    )
    workflow.add_step(
        "save_data",
        {"data": "${transformed_data.result}", "location": "s3://bucket/data"},
        depends_on=["transform_data"]
    )

    # Execute
    print("=== Executing Workflow ===")
    result = workflow.execute()

    print("\n=== Results ===")
    for r in result["results"]:
        status = "✓" if r.success else "✗"
        print(f"{status} {r.tool_name}: {r.duration:.2f}s")
```

**Checkpoint 3:** ✅ Tool orchestration working

---

## Part 4: Production Deployment (60 minutes)

### Deploying Tool-Enabled Agent

```python
# File: tool_agent_api.py
"""
Production Tool-Enabled Agent API
==================================
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any
import uvicorn

# Global registry and engine
registry = ToolRegistry()
engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize tools on startup"""
    global engine

    # Register tools (load from config)
    # ...

    from openai import OpenAI
    client = OpenAI()

    engine = FunctionCallingEngine(client, registry)

    yield


# on_event("startup") is deprecated - lifespan owns startup AND shutdown
app = FastAPI(title="Tool-Enabled Agent API", lifespan=lifespan)


class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: dict[str, Any]


class WorkflowRequest(BaseModel):
    steps: list[dict]


class ChatRequest(BaseModel):
    message: str
    tools: list[str] | None = None

@app.post("/tools/execute")
async def execute_tool(request: ToolCallRequest) -> dict:
    """Execute a single tool"""
    tool = registry.get_tool(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    result = tool.execute(**request.parameters)
    return result

@app.post("/tools/workflow")
async def execute_workflow(request: WorkflowRequest) -> dict:
    """Execute a workflow"""
    orchestrator = ToolOrchestrator(registry)
    workflow = Workflow(orchestrator)

    for step in request.steps:
        workflow.add_step(**step)

    return workflow.execute()

@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    """Chat with function calling"""
    result = engine.chat(request.message, request.tools)
    return result

@app.get("/tools")
async def list_tools() -> list[str]:
    """List available tools"""
    return registry.list_tools()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Checkpoint 4:** ✅ Production deployment ready

---

## Lab Completion Checklist

- [ ] Part 1: OpenAI function calling
- [ ] Part 2: Production tool suite (15+ tools)
- [ ] Part 3: Tool orchestration engine
- [ ] Part 4: Production API deployment

---

## Summary

In this lab, you learned:

1. **Function Calling** - OpenAI's function calling system
2. **Tool Development** - Building production tools
3. **Orchestration** - Coordinating multiple tools
4. **Error Handling** - Retries, rate limiting, validation
5. **Production Deployment** - Tool-enabled API

---

## Next Steps

1. **LAB-014: AI Evaluation & Safety** - Test your tools
2. **LAB-011: Multi-Modal** - Add vision tools
3. Build complete agent with 20+ tools

---

**Lab:** 013 - Advanced Function Calling

**Time Estimate:** 7 hours

**Difficulty:** ⭐⭐⭐ Advanced
