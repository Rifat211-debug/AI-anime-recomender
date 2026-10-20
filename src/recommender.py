from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from src.prompt_template import get_anime_prompt


def build_anime_retriever_tool(retriever):
    @tool
    def anime_retriever_tool(query: str) -> str:
        """Search the anime knowledge base for relevant titles."""
        docs = retriever.invoke(query)

        if not docs:
            return "No relevant anime documents were found."

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
            model_provider="groq"
        )

        self.anime_tool = build_anime_retriever_tool(
            self.retriever
        )

        self.chain_with_tools = self.llm.bind_tools(
            [self.anime_tool]
        )

    def get_recommendation(self, query: str) -> str:
        try:
            messages = [
                SystemMessage(
                    content=self.prompt_template.template
                ),
                HumanMessage(content=query),
            ]

            # Ask the model whether to call the retriever
            ai_msg = self.chain_with_tools.invoke(messages)
            messages.append(ai_msg)

            # Execute requested tools
            if ai_msg.tool_calls:
                for tool_call in ai_msg.tool_calls:
                    if tool_call["name"] == "anime_retriever_tool":
                        tool_result = self.anime_tool.invoke(
                            tool_call["args"]
                        )

                        messages.append(
                            ToolMessage(
                                content=str(tool_result),
                                tool_call_id=tool_call["id"],
                            )
                        )

                # Generate the final answer using retrieved data
                response = self.chain_with_tools.invoke(messages)
                return response.content

            # Model may answer without using the tool
            return ai_msg.content

        except Exception as e:
            raise RuntimeError(
                f"LLM recommendation failed: {e}"
            ) from e
