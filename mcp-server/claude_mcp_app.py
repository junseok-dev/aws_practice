import asyncio
import os
from pathlib import Path
import anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv(Path(__file__).parent.parent / ".env")
api_key = os.getenv("CLAUDE_API_KEY")


async def run():
    # MCP 서버 연결 설정
    server_params = StdioServerParameters(
        command="python",
        args=["calculator_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # MCP 서버에서 도구 목록 가져오기
            tools_result = await session.list_tools()
            tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in tools_result.tools
            ]

            print("사용 가능한 도구:", [t["name"] for t in tools])
            print("-" * 40)

            client = anthropic.Anthropic(api_key=api_key)
            messages = []

            # 대화 루프
            while True:
                user_input = input("\n질문 입력 (종료: q): ").strip()
                if user_input.lower() == "q":
                    break

                messages.append({"role": "user", "content": user_input})

                # Claude API 호출
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    tools=tools,
                    messages=messages,
                )

                # 도구 호출 처리
                while response.stop_reason == "tool_use":
                    tool_uses = [b for b in response.content if b.type == "tool_use"]
                    messages.append({"role": "assistant", "content": response.content})

                    tool_results = []
                    for tool_use in tool_uses:
                        print(f"[도구 호출] {tool_use.name}({tool_use.input})")
                        result = await session.call_tool(tool_use.name, tool_use.input)
                        result_text = str(result.content[0].text)
                        print(f"[결과] {result_text}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": result_text,
                        })

                    messages.append({"role": "user", "content": tool_results})

                    response = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1024,
                        tools=tools,
                        messages=messages,
                    )

                # 최종 응답 출력
                final_text = next(b.text for b in response.content if hasattr(b, "text"))
                messages.append({"role": "assistant", "content": final_text})
                print(f"\nClaude: {final_text}")


if __name__ == "__main__":
    asyncio.run(run())
