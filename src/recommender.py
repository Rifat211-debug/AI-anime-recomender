from datetime import date

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from src.prompt_template import get_anime_prompt
from src.external_tools import build_external_tools
from memory.mem0_manager import Mem0Manager


def build_anime_retriever_tool(retriever):
    @tool
    def anime_retriever_tool(query: str) -> str:
        """Search the local anime knowledge base for relevant titles."""

        docs = retriever.invoke(query)

        if not docs:
            return (
                "No relevant anime documents were found "
                "in the local anime dataset."
            )

        return "\n\n".join(
            doc.page_content for doc in docs
        )

    return anime_retriever_tool


class AnimeRecommender:
    def __init__(self, retriever, model_name: str):
        self.retriever = retriever
        self.prompt_template = get_anime_prompt()

        self.llm = init_chat_model(
            model_name,
            model_provider="groq",
        )

        self.memory = Mem0Manager()

        self.anime_tool = build_anime_retriever_tool(
            self.retriever
        )

        self.external_tools = build_external_tools()

        self.tools = [
            self.anime_tool,
            *self.external_tools,
        ]

        self.tools_by_name = {
            selected_tool.name: selected_tool
            for selected_tool in self.tools
        }

        self.chain_with_tools = self.llm.bind_tools(
            self.tools
        )

    def get_recommendation(
        self,
        query: str,
        user_id: str,
    ) -> str:

        if not user_id or not user_id.strip():
            raise ValueError("A valid user_id is required.")

        try:
            # 1. Retrieve memories belonging to this user.
            memories = self.memory.search_memories(
                query=query,
                user_id=user_id,
                limit=5,
            )

            # 2. Prepare the system prompt.
            system_prompt = self.prompt_template.template

            system_prompt += f"""

Today's date is {date.today().isoformat()}.

You are AniBaba, an anime recommendation assistant.

AVAILABLE TOOLS:
- anime_retriever_tool: Search the local anime knowledge base.
- search_latest_anime: Search the live web for recent anime,
  upcoming releases, announcements, release dates, and sources.
- get_current_weather: Retrieve current weather for a city.

TOOL USAGE RULES:
- Use anime_retriever_tool for relevant information in the local dataset.
- Use search_latest_anime for recent releases, upcoming anime,
  current anime news, and information that may be missing locally.
- Use get_current_weather when the user requests weather information
  or weather-based recommendations.
- For weather-based recommendations, use actual returned conditions.
- If a city is required but missing, ask the user which city they mean.
- Do not invent release dates, weather readings, ratings, or sources.
- Include useful source URLs when using web search.
- Clearly distinguish movies already released from upcoming movies.
- Treat search results as evidence, not guaranteed facts.
- If a tool fails, explain the limitation honestly.
- Follow the user's current request over older preferences.
- After receiving useful tool results, answer the user instead of
  repeatedly requesting the same information.
"""

            if memories:
                memory_context = "\n".join(
                    f"- {memory}" for memory in memories
                )

                system_prompt += (
                    "\n\nRelevant preferences remembered for this user:\n"
                    f"{memory_context}\n"
                    "Use these preferences to personalize answers when "
                    "relevant. Do not let old preferences override "
                    "the user's current request."
                )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query),
            ]

            # 3. Ask the model whether tools are needed.
            response = self.chain_with_tools.invoke(messages)

            # Prevent repeated execution of identical tool requests.
            tool_cache = {}
            seen_tool_calls = set()
            max_tool_rounds = 5

            # 4. Execute tool calls and return their results to the model.
            for round_number in range(max_tool_rounds):
                if not response.tool_calls:
                    break

                messages.append(response)

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_call_id = tool_call["id"]

                    print(
                        f"TOOL CALLED (round "
                        f"{round_number + 1}): {tool_name}"
                    )

                    # A stable key for the tool name and its arguments.
                    call_key = (
                        tool_name,
                        repr(sorted(tool_args.items())),
                    )

                    if call_key in tool_cache:
                        tool_result = tool_cache[call_key]
                        print(f"REUSING CACHED RESULT: {tool_name}")

                    elif call_key in seen_tool_calls:
                        tool_result = (
                            "This exact tool request has already been "
                            "executed. Use the previous tool results "
                            "to answer the user without repeating it."
                        )

                    else:
                        seen_tool_calls.add(call_key)

                        selected_tool = self.tools_by_name.get(
                            tool_name
                        )

                        if selected_tool is None:
                            tool_result = (
                                f"Unknown tool: {tool_name}"
                            )

                        else:
                            try:
                                tool_result = selected_tool.invoke(
                                    tool_args
                                )

                                if not isinstance(tool_result, str):
                                    tool_result = str(tool_result)

                                # Limit the amount of tool output sent
                                # back to the model.
                                tool_result = tool_result[:8000]

                                tool_cache[call_key] = tool_result

                                print(
                                    f"TOOL RESULT ({tool_name}): "
                                    f"{tool_result[:300]}"
                                )

                            except Exception as tool_error:
                                tool_result = (
                                    f"Tool execution failed: {tool_error}"
                                )

                                print(
                                    f"TOOL ERROR ({tool_name}): "
                                    f"{tool_error}"
                                )

                    messages.append(
                        ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call_id,
                        )
                    )

                # Make exactly one model call after each tool round.
                response = self.chain_with_tools.invoke(messages)

            # 5. If the model still requests tools, stop tool execution
            # and ask for a final answer using the collected results.
            if response.tool_calls:
                messages.append(response)

                messages.append(
                    SystemMessage(
                        content=(
                            "The tool-call limit has been reached. "
                            "Do not call any more tools. Answer the "
                            "original user question using the results "
                            "already collected. Include source URLs "
                            "and verified dates where available. "
                            "Do not invent missing information."
                        )
                    )
                )

                # Invoke the base model, not the tool-bound model.
                response = self.llm.invoke(messages)

            # 6. Extract the final answer.
            answer = response.content

            if not isinstance(answer, str):
                answer = str(answer)

            if not answer.strip():
                answer = (
                    "I couldn't generate a recommendation from the "
                    "available results. Please try again."
                )

            # 7. Save the conversation to this user's Mem0 memory.
            self.memory.save_conversation(
                query=query,
                response=answer,
                user_id=user_id,
            )

            return answer

        except Exception as e:
            raise RuntimeError(
                f"LLM recommendation failed: {e}"
            ) from e
