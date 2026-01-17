backboard.io logobackboard.io

Dashboard
Chat
API Docs
Quickstart SDK
Model Library
Limits
Manage Billing
Manage API Keys
Manage Users
Profile
Logout
Quickstart Guide
Get started with Backboard in minutes. Create an assistant, send messages, call tools, upload documents, and enable persistent memory across conversations.
First Message
Create an assistant, initialize a thread, and send your first message to get a response.
first-message.py
python

# Install: pip install backboard-sdk
import asyncio
from backboard import BackboardClient

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key="YOUR_API_KEY")

    # Create an assistant
    assistant = await client.create_assistant(
        name="My First Assistant",
        system_prompt="A helpful assistant"
    )

    # Create a thread
    thread = await client.create_thread(assistant.assistant_id)

    # Send a message and get the complete response
    response = await client.add_message(
        thread_id=thread.thread_id,
        content="Hello! Tell me a fun fact about space.",
        llm_provider="openai",
        model_name="gpt-4o",
        stream=False
    )

    # Print the AI's response
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
Tool Calls
Define custom functions for your assistant to call. Handle tool call requests and submit outputs to continue the conversation.
tool-calls.py
python

# Install: pip install backboard-sdk
import asyncio
import json
from backboard import BackboardClient

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key="YOUR_API_KEY")

    # Define a tool (function) for the assistant to call
    tools = [{
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }]

    # Create an assistant with the tool
    assistant = await client.create_assistant(
        name="Weather Assistant",
        system_prompt="You are a helpful weather assistant",
        tools=tools
    )

    # Create a thread
    thread = await client.create_thread(assistant.assistant_id)

    # Send a message that triggers the tool call
    response = await client.add_message(
        thread_id=thread.thread_id,
        content="What's the weather in San Francisco?",
        stream=False
    )

    # Check if the assistant requires action (tool call)
    if response.status == "REQUIRES_ACTION" and response.tool_calls:
        tool_outputs = []
        
        # Process each tool call
        for tc in response.tool_calls:
            if tc.function.name == "get_current_weather":
                # Get parsed arguments (required parameters are guaranteed by API)
                args = tc.function.parsed_arguments
                location = args["location"]
                
                # Execute your function and format the output
                weather_data = {
                    "temperature": "68°F",
                    "condition": "Sunny",
                    "location": location
                }
                
                tool_outputs.append({
                    "tool_call_id": tc.id,
                    "output": json.dumps(weather_data)
                })
        
        # Submit the tool outputs back to continue the conversation
        final_response = await client.submit_tool_outputs(
            thread_id=thread.thread_id,
            run_id=response.run_id,
            tool_outputs=tool_outputs
        )
        
        print(final_response.content)

if __name__ == "__main__":
    asyncio.run(main())
Document Upload & Interaction
Upload documents to your assistant and query their contents. Documents are automatically indexed and made searchable.
documents.py
python

# Install: pip install backboard-sdk
import asyncio
import time
from backboard import BackboardClient

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key="YOUR_API_KEY")
    
    # Create an assistant
    assistant = await client.create_assistant(
        name="Document Assistant",
        system_prompt="You are a helpful document analysis assistant"
    )
    
    # Upload a document to the assistant
    document = await client.upload_document_to_assistant(
        assistant.assistant_id,
        "my_document.pdf"
    )
    
    # Wait for the document to be indexed
    print("Waiting for document to be indexed...")
    while True:
        status = await client.get_document_status(document.document_id)
        if status.status == "indexed":
            print("Document indexed successfully!")
            break
        elif status.status == "failed":
            print(f"Document indexing failed: {status.status_message}")
            return
        time.sleep(2)
    
    # Create a thread
    thread = await client.create_thread(assistant.assistant_id)
    
    # Ask a question about the document
    response = await client.add_message(
        thread_id=thread.thread_id,
        content="What are the key points in the uploaded document?",
        stream=False
    )
    
    print(response.content)

if __name__ == "__main__":
    asyncio.run(main())
Memory - Persistent Context
Enable memory to make your assistant remember information across conversations. Set memory="Auto" to automatically save and retrieve relevant context.
memory.py
python

# Install: pip install backboard-sdk
import asyncio
from backboard import BackboardClient

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key="YOUR_API_KEY")
    
    # Create an assistant
    assistant = await client.create_assistant(
        name="Memory Assistant",
        system_prompt="You are a helpful assistant with persistent memory"
    )
    
    # Create first thread and share information
    thread1 = await client.create_thread(assistant.assistant_id)
    
    # Share information with memory enabled
    response1 = await client.add_message(
        thread_id=thread1.thread_id,
        content="My name is Sarah and I work as a software engineer at Google.",
        memory="Auto",  # Enable memory - automatically saves relevant info
        stream=False
    )
    print(f"AI: {response1.content}")
    
    # Optional: Poll for memory operation completion
    # memory_op_id = response1.memory_operation_id
    # if memory_op_id:
    #     import time
    #     while True:
    #         status_response = requests.get(
    #             f"{base_url}/assistants/memories/operations/{memory_op_id}",
    #             headers={"X-API-Key": api_key}
    #         )
    #         if status_response.status_code == 200:
    #             data = status_response.json()
    #             if data.get("status") in ("COMPLETED", "ERROR"):
    #                 print(f"Memory operation: {data.get('status')}")
    #                 break
    #         time.sleep(1)
    
    # Create a new thread to test memory recall
    thread2 = await client.create_thread(assistant.assistant_id)
    
    # Ask what the assistant remembers (in a completely new thread!)
    response3 = await client.add_message(
        thread_id=thread2.thread_id,
        content="What do you remember about me?",
        memory="Auto",  # Searches and retrieves saved memories
        stream=False
    )
    print(f"AI: {response3.content}")
    # Should mention: Sarah, Google, software engineer

if __name__ == "__main__":
    asyncio.run(main())



backboard.io logobackboard.io

Dashboard
Chat
API Docs
Quickstart SDK
Model Library
Limits
Manage Billing
Manage API Keys
Manage Users
Profile
Logout
Quickstart Guide
Get started with Backboard in minutes. Create an assistant, send messages, call tools, upload documents, and enable persistent memory across conversations.
First Message
Create an assistant, initialize a thread, and send your first message to get a response.
first-message.py
python

# Install: pip install backboard-sdk
import asyncio
from backboard import BackboardClient

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key="YOUR_API_KEY")

    # Create an assistant
    assistant = await client.create_assistant(
        name="My First Assistant",
        system_prompt="A helpful assistant"
    )

    # Create a thread
    thread = await client.create_thread(assistant.assistant_id)

    # Send a message and stream the response
    async for chunk in await client.add_message(
        thread_id=thread.thread_id,
        content="Tell me a short story about a robot learning to paint.",
        llm_provider="openai",
        model_name="gpt-4o",
        stream=True
    ):
        # Print each chunk of content as it arrives
        if chunk['type'] == 'content_streaming':
            print(chunk['content'], end='', flush=True)
        elif chunk['type'] == 'message_complete':
            break

if __name__ == "__main__":
    asyncio.run(main())
Tool Calls
Define custom functions for your assistant to call. Handle tool call requests and submit outputs to continue the conversation.
tool-calls.py
python

# Install: pip install backboard-sdk
import asyncio
import json
from backboard import BackboardClient

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key="YOUR_API_KEY")

    # Define a tool (function) for the assistant to call
    tools = [{
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }]

    # Create an assistant with the tool
    assistant = await client.create_assistant(
        name="Weather Assistant",
        system_prompt="You are a helpful weather assistant",
        tools=tools
    )

    # Create a thread
    thread = await client.create_thread(assistant.assistant_id)

    # Send a message and stream the response
    async for chunk in await client.add_message(
        thread_id=thread.thread_id,
        content="What's the weather in San Francisco?",
        stream=True
    ):
        # Stream content chunks
        if chunk['type'] == 'content_streaming':
            print(chunk['content'], end='', flush=True)
        
        # Handle tool call requirement
        elif chunk['type'] == 'tool_submit_required':
            run_id = chunk['run_id']
            tool_calls = chunk['tool_calls']
            
            # Process each tool call
            tool_outputs = []
            for tc in tool_calls:
                function_name = tc['function']['name']
                function_args = json.loads(tc['function']['arguments'])
                
                if function_name == 'get_current_weather':
                    # Execute your function
                    location = function_args['location']
                    weather_data = {
                        "temperature": "68°F",
                        "condition": "Sunny",
                        "location": location
                    }
                    
                    tool_outputs.append({
                        "tool_call_id": tc['id'],
                        "output": json.dumps(weather_data)
                    })
            
            # Submit tool outputs and stream the final response
            async for tool_chunk in await client.submit_tool_outputs(
                thread_id=thread.thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                stream=True
            ):
                if tool_chunk['type'] == 'content_streaming':
                    print(tool_chunk['content'], end='', flush=True)
                elif tool_chunk['type'] == 'message_complete':
                    break
            break

if __name__ == "__main__":
    asyncio.run(main())
Document Upload & Interaction
Upload documents to your assistant and query their contents. Documents are automatically indexed and made searchable.
documents.py
python

# Install: pip install backboard-sdk
import asyncio
import time
from backboard import BackboardClient

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key="YOUR_API_KEY")
    
    # Create an assistant
    assistant = await client.create_assistant(
        name="Document Assistant",
        system_prompt="You are a helpful document analysis assistant"
    )
    
    # Upload a document to the assistant
    document = await client.upload_document_to_assistant(
        assistant.assistant_id,
        "my_document.pdf"
    )
    
    # Wait for the document to be indexed
    print("Waiting for document to be indexed...")
    while True:
        status = await client.get_document_status(document.document_id)
        if status.status == "indexed":
            print("Document indexed successfully!")
            break
        elif status.status == "failed":
            print(f"Indexing failed: {status.status_message}")
            return
        time.sleep(2)
    
    # Create a thread
    thread = await client.create_thread(assistant.assistant_id)
    
    # Ask a question about the document and stream the response
    async for chunk in await client.add_message(
        thread_id=thread.thread_id,
        content="What are the key points in the document?",
        stream=True
    ):
        if chunk['type'] == 'content_streaming':
            print(chunk['content'], end='', flush=True)
        elif chunk['type'] == 'message_complete':
            break

if __name__ == "__main__":
    asyncio.run(main())
Memory - Persistent Context
Enable memory to make your assistant remember information across conversations. Set memory="Auto" to automatically save and retrieve relevant context.
memory.py
python

# Install: pip install backboard-sdk
import asyncio
from backboard import BackboardClient

async def main():
    # Initialize the Backboard client
    client = BackboardClient(api_key="YOUR_API_KEY")
    
    # Create an assistant
    assistant = await client.create_assistant(
        name="Memory Assistant",
        system_prompt="You are a helpful assistant with persistent memory"
    )
    
    # Create first thread and share information
    thread1 = await client.create_thread(assistant.assistant_id)
    
    # Share information with memory enabled (streaming)
    print("Sharing info...")
    memory_op_id = None
    async for chunk in await client.add_message(
        thread_id=thread1.thread_id,
        content="My name is Sarah and I work as a software engineer at Google.",
        memory="Auto",  # Enable memory - automatically saves relevant info
        stream=True
    ):
        if chunk['type'] == 'content_streaming':
            print(chunk['content'], end='', flush=True)
        elif chunk['type'] == 'memory_retrieved':
            # Shows when memories are being searched
            memories = chunk.get('memories', [])
            if memories:
                print(f"\n[Found {len(memories)} memories]")
        elif chunk['type'] == 'run_ended':
            memory_op_id = chunk.get('memory_operation_id')
    print("\n")
    
    # Optional: Poll for memory operation completion
    # if memory_op_id:
    #     import time
    #     while True:
    #         status_response = requests.get(
    #             f"{base_url}/assistants/memories/operations/{memory_op_id}",
    #             headers={"X-API-Key": api_key}
    #         )
    #         if status_response.status_code == 200:
    #             data = status_response.json()
    #             if data.get("status") in ("COMPLETED", "ERROR"):
    #                 print(f"Memory operation: {data.get('status')}")
    #                 break
    #         time.sleep(1)
    
    # Create a new thread to test memory recall
    thread2 = await client.create_thread(assistant.assistant_id)
    
    # Ask what the assistant remembers (streaming)
    print("Testing memory recall...")
    async for chunk in await client.add_message(
        thread_id=thread2.thread_id,
        content="What do you remember about me?",
        memory="Auto",  # Searches and retrieves saved memories
        stream=True
    ):
        if chunk['type'] == 'content_streaming':
            print(chunk['content'], end='', flush=True)
    print("\n")
    # Should mention: Sarah, Google, software engineer

if __name__ == "__main__":
    asyncio.run(main())


    Open SearchSearch
Keyboard Shortcut:Command⌘ k

Close Group
Welcome to Backboard API

Endpoint URL

Core Features

Quickstart

Close Group
Threads

List Threads
HTTP Method: GET

Get Thread
HTTP Method: GET

Delete Thread
HTTP Method: DEL

List Thread Documents
HTTP Method: GET

Add Message to Thread with Optional Attachments
HTTP Method: POST

Submit Tool Outputs for a Run
HTTP Method: POST

Open Group
Documents

Open Group
Assistants

Open Group
Memories

Open Group
Models

v1.0.0
OAS 3.1.0
Backboard API
Welcome to Backboard API
Build conversational AI applications with persistent memory and intelligent document processing.

Endpoint URL
https://app.backboard.io/api
Core Features
Persistent Conversations
Create conversation threads that maintain context across multiple messages and support file attachments.

Intelligent Document Processing
Upload and process documents (PDF, text, Office files) with automatic chunking and indexing for retrieval.

AI Assistants
Create specialized assistants with custom instructions, document access, and tool capabilities.

Quickstart
import requests

API_KEY = "your_api_key"
BASE_URL = "https://app.backboard.io/api"
HEADERS = {"X-API-Key": API_KEY}

# 1) Create assistant
response = requests.post(
    f"{BASE_URL}/assistants",
    json={"name": "Support Bot", "system_prompt": "After every response, pass a joke at the end of the response!"},
    headers=HEADERS,
)
assistant_id = response.json()["assistant_id"]

# 2) Create thread
response = requests.post(
    f"{BASE_URL}/assistants/{assistant_id}/threads",
    json={},
    headers=HEADERS,
)
thread_id = response.json()["thread_id"]

# 3) Send message
response = requests.post(
    f"{BASE_URL}/threads/{thread_id}/messages",
    headers=HEADERS,
    data={"content": "Tell me about Canada in detail.", "stream": "false", "memory": "Auto"},
)
print(response.json().get("content"))
Explore the Assistants, Threads, and Documents sections in the sidebar.

Server
Server:
https://app.backboard.io/api
Production


Authentication
Required
Selected Auth Type:APIKeyHeader
Name
:
X-API-Key
Clear Value
Value
:
QUxMIFlPVVIgQkFTRSBBUkUgQkVMT05HIFRPIFVT
Show Password
Client Libraries
Python http.client
Threads ​Copy link
ThreadsOperations
get
/threads
get
/threads/{thread_id}
delete
/threads/{thread_id}
get
/threads/{thread_id}/documents
post
/threads/{thread_id}/messages
post
/threads/{thread_id}/runs/{run_id}/submit-tool-outputs
List Threads​Copy link
List all threads for the currently authenticated user.

Query Parameters
skipCopy link to skip
Type:Skip
default: 
0
Integer numbers.

limitCopy link to limit
Type:Limit
default: 
100
Integer numbers.

Headers
AcceptCopy link to Accept
Example
Responses

200
Successful Response

422
Validation Error
Request Example forget/threads
Python http.client

import http.client

conn = http.client.HTTPSConnection("app.backboard.io")

headers = {
    'Accept': "*/*",
    'X-API-Key': "YOUR_SECRET_TOKEN"
}

conn.request("GET", "/api/threads", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

Test Request
(get /threads)
Status:200
Status:422

[
  {
    "metadata_": {
      "propertyName*": "anything"
    },
    "thread_id": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2026-01-17T00:16:04.450Z",
    "messages": []
  }
]
Successful Response

Get Thread​Copy link
Retrieve a specific thread by its UUID, including all its messages.

Path Parameters
thread_idCopy link to thread_id
Type:Thread Id
Format:uuid
required
Responses

200
Successful Response

422
Validation Error
Request Example forget/threads/{thread_id}
Python http.client

import http.client

conn = http.client.HTTPSConnection("app.backboard.io")

headers = { 'X-API-Key': "YOUR_SECRET_TOKEN" }

conn.request("GET", "/api/threads/123e4567-e89b-12d3-a456-426614174000", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

Test Request
(get /threads/{thread_id})
Status:200
Status:422

{
  "metadata_": {
    "propertyName*": "anything"
  },
  "thread_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2026-01-17T00:16:04.450Z",
  "messages": []
}
Successful Response

Delete Thread​Copy link
Permanently delete a thread and all its associated messages.

Path Parameters
thread_idCopy link to thread_id
Type:Thread Id
Format:uuid
required
Responses

200
Successful Response

422
Validation Error
Request Example fordelete/threads/{thread_id}
Python http.client

import http.client

conn = http.client.HTTPSConnection("app.backboard.io")

headers = { 'X-API-Key': "YOUR_SECRET_TOKEN" }

conn.request("DELETE", "/api/threads/123e4567-e89b-12d3-a456-426614174000", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

Test Request
(delete /threads/{thread_id})
Status:200
Status:422

{
  "message": "string",
  "thread_id": "123e4567-e89b-12d3-a456-426614174000",
  "deleted_at": "2026-01-17T00:16:04.450Z"
}
Successful Response

List Thread Documents​Copy link
List all documents associated with a specific thread.

Path Parameters
thread_idCopy link to thread_id
Type:Thread Id
Format:uuid
required
Responses

200
Successful Response

422
Validation Error
Request Example forget/threads/{thread_id}/documents
Python http.client

import http.client

conn = http.client.HTTPSConnection("app.backboard.io")

headers = { 'X-API-Key': "YOUR_SECRET_TOKEN" }

conn.request("GET", "/api/threads/123e4567-e89b-12d3-a456-426614174000/documents", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

Test Request
(get /threads/{thread_id}/documents)
Status:200
Status:422

[
  {
    "metadata_": {
      "propertyName*": "anything"
    },
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "string",
    "status": "pending",
    "status_message": "string",
    "summary": "string",
    "created_at": "2026-01-17T00:16:04.450Z",
    "updated_at": "2026-01-17T00:16:04.450Z"
  }
]
Successful Response

Add Message to Thread with Optional Attachments​Copy link
Add a user message to an existing thread with optional file attachments. Can send text only, attachments only, or both. Documents must be indexed before further messages are allowed. To choose a model, set llm_provider and model_name. If omitted, defaults are llm_provider=openai and model_name=gpt-4o. Set memory='Auto' to enable memory search and automatic memory operations. See the Model Library page in the dashboard (model-library page) for a current list of supported models and providers.

Path Parameters
thread_idCopy link to thread_id
Type:Thread Id
Format:uuid
required
Body
multipart/form-data
contentCopy link to content
Type:Content
nullable
filesCopy link to files
Type:array Files[]
default: 
[]
llm_providerCopy link to llm_provider
Type:Llm Provider
nullable
LLM provider name (nullable). Default: openai.

memoryCopy link to memory
Type:Memory
default: 
"off"
nullable
Memory mode: 'Auto' (search and write), 'off' (disabled), 'Readonly' (search only). Default: off.

metadataCopy link to metadata
Type:Metadata
nullable
Optional metadata as JSON string. Can include custom_timestamp (ISO 8601 format) and other custom fields.

model_nameCopy link to model_name
Type:Model Name
nullable
Model name (nullable). Default: gpt-4o.

send_to_llmCopy link to send_to_llm
Type:Send To Llm
default: 
"true"
nullable
Whether to send the message to the LLM for a response. If 'false', the message is saved but no AI response is generated. Default: true.

streamCopy link to stream
Type:Stream
default: 
false
web_searchCopy link to web_search
Type:Web Search
default: 
"off"
nullable
Web search mode: 'Auto' (enables web search tool for LLM), 'off' (disabled). Default: off.

Responses

200
Successful Response

422
Validation Error
Request Example forpost/threads/{thread_id}/messages
Python http.client

import http.client

conn = http.client.HTTPSConnection("app.backboard.io")

payload = ""

headers = {
    'Content-Type': "multipart/form-data",
    'X-API-Key': "YOUR_SECRET_TOKEN"
}

conn.request("POST", "/api/threads/123e4567-e89b-12d3-a456-426614174000/messages", payload, headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

Test Request
(post /threads/{thread_id}/messages)
Status:200
Status:422

{
  "message": "string",
  "thread_id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "string",
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "user",
  "status": "IN_PROGRESS",
  "tool_calls": [
    {
      "propertyName*": "anything"
    }
  ],
  "run_id": "string",
  "memory_operation_id": "string",
  "retrieved_memories": [
    {
      "id": "string",
      "memory": "string",
      "score": 1
    }
  ],
  "model_provider": "string",
  "model_name": "string",
  "input_tokens": 1,
  "output_tokens": 1,
  "total_tokens": 1,
  "created_at": "2026-01-17T00:16:04.450Z",
  "attachments": [
    {
      "document_id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "string",
      "status": "string",
      "file_size_bytes": 1,
      "summary": "string"
    }
  ],
  "timestamp": "2026-01-17T00:16:04.450Z"
}
Successful Response

Submit Tool Outputs for a Run​Copy link
Submit the outputs of tool calls that an assistant message previously requested. This will continue the run. If stream=true, returns a Server-Sent Events stream.

Path Parameters
thread_idCopy link to thread_id
Type:Thread Id
Format:uuid
required
run_idCopy link to run_id
Type:Run Id
required
Query Parameters
streamCopy link to stream
Type:Stream
default: 
false
Body
required
application/json
tool_outputsCopy link to tool_outputs
Type:array Tool Outputs[]
required
A list of tool outputs to submit.

Show ToolOutputfor tool_outputs
Responses

200
Successful Response

422
Validation Error
Request Example forpost/threads/{thread_id}/runs/{run_id}/submit-tool-outputs
Python http.client

import http.client

conn = http.client.HTTPSConnection("app.backboard.io")

payload = "{\"tool_outputs\":[{\"tool_call_id\":\"\",\"output\":\"\"}]}"

headers = {
    'Content-Type': "application/json",
    'X-API-Key': "YOUR_SECRET_TOKEN"
}

conn.request("POST", "/api/threads/123e4567-e89b-12d3-a456-426614174000/runs/%7Brun_id%7D/submit-tool-outputs", payload, headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

Test Request
(post /threads/{thread_id}/runs/{run_id}/submit-tool-outputs)
Status:200
Status:422

{
  "message": "string",
  "thread_id": "123e4567-e89b-12d3-a456-426614174000",
  "run_id": "string",
  "content": "string",
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "user",
  "status": "IN_PROGRESS",
  "tool_calls": [
    {
      "propertyName*": "anything"
    }
  ],
  "memory_operation_id": "string",
  "retrieved_memories": [
    {
      "id": "string",
      "memory": "string",
      "score": 1
    }
  ],
  "model_provider": "string",
  "model_name": "string",
  "input_tokens": 1,
  "output_tokens": 1,
  "total_tokens": 1,
  "created_at": "2026-01-17T00:16:04.450Z",
  "timestamp": "2026-01-17T00:16:04.450Z"
}
Successful Response

Documents (Collapsed)​Copy link
DocumentsOperations
post
/threads/{thread_id}/documents
delete
/documents/{document_id}
get
/documents/{document_id}/status
Show More
Assistants (Collapsed)​Copy link
AssistantsOperations
post
/assistants
get
/assistants
get
/assistants/{assistant_id}
put
/assistants/{assistant_id}
delete
/assistants/{assistant_id}
post
/assistants/{assistant_id}/threads
get
/assistants/{assistant_id}/documents
post
/assistants/{assistant_id}/documents
Show More
Memories (Collapsed)​Copy link
MemoriesOperations
get
/assistants/{assistant_id}/memories
post
/assistants/{assistant_id}/memories
get
/assistants/{assistant_id}/memories/{memory_id}
delete
/assistants/{assistant_id}/memories/{memory_id}
put
/assistants/{assistant_id}/memories/{memory_id}
get
/assistants/{assistant_id}/memories/stats
get
/assistants/memories/operations/{operation_id}
Show More
Models (Collapsed)​Copy link
ModelsOperations
get
/models
get
/models/providers
get
/models/provider/{provider_name}
get
/models/{model_name}
get
/models/embedding/all
get
/models/embedding/providers
get
/models/embedding/{model_name}
Show More