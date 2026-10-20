import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import ToolMessage

load_dotenv()

SERVERS={
    "math":{
        "transport":"stdio",
        "command":"C:\\Users\\DELL\\AppData\\Local\\Programs\\Python\\Python314\\Scripts\\uv.exe",
        "args":[
            "run",
            "fastmcp",
            "run",
            "C:\\Users\\DELL\\Desktop\\mcp-math-server\\main.py"
        ]
    },
    "expense":{
        "transport":"streamable_http",  #if this fails try "sse" ,imp => [here this expense mcp server is remote mcp server which is deployed on cloud but here it is not deplyed hust wriiten there ]
        "url":"https://splendid-gold-dingo.fastmcp.app/mcp"
    },
    "manim-server":{
        "transport":"stdio",
        "command":"/Library/Frameworks/Python.framework/Versions/3.11/bin/python3",
        "args":[
            "/Users/nitish/desktop/manim-mcp-server/src/manim_server.py"
            ],
        "env":{
            "MANIM_EXECUTABLE":"/Library/Frameworks/Python.framework/Versions/3.11/bin/manim"
        } 
    }
}

async def main():

    client=MultiServerMCPClient(SERVERS)
    tools=await client.get_tools()

    named_tools={}
    for tool in tools:
        named_tools[tool.name]=tool

    print(named_tools)

    llm=ChatOpenAI(model="gpt-5")
    llm_with_tools=llm.bind_tools(tools)

    prompt="add an expense of groceries on 4th november"
    response=await llm_with_tools.ainvoke(prompt)

    if not getattr(response,"tool_calls",None):
        print("\nLLM Reply:",response.content)
        return

    tool_messages=[]
    for tc in response.tool_calls:
        selected_tool=response.tool_calls[0]["name"]
        selected_tool_args=response.tool_calls[0]["args"]
        selected_tool_id=response.tool_calls[0]["id"]


        tool_result=await named_tools[selected_tool].ainvoke(selected_tool_args)

        tool_messages.append(ToolMessage(tool_call_id=selected_tool_id,content=json.dumps(tool_result)))
    
    final_response=await llm_with_tools.ainvoke([prompt,response, *tool_messages])
    print(f"final response:{final_response.content}")


if __name__=="__main__":
    asyncio.run(main())