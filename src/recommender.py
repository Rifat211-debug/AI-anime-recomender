from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from src.prompt_template import get_anime_prompt


def build_anime_retriever_tool(retriever):
    """
    Returns a LangChain tool to retrieve anime information from the vector store.
    """
    @tool
    def anime_retriever_tool(query: str) -> str:
        """
        Use this tool to search the anime knowledge base.
        
        Always call this tool for anime-related questions such as:
        recommendations, similarity search, genres, or plot summaries.

        Input:
        - query: User's anime preference or question.

        Output:
        - Relevant anime information retrieved from the vector database.
        """

        docs = retriever.invoke(query)
        return "\n\n".join(doc.page_content for doc in docs)

    return anime_retriever_tool


class AnimeRecommender:
    def __init__(self, retriever, model_name: str):
        self.retriever = retriever
        self.prompt_template = get_anime_prompt()
        self.llm = init_chat_model(model_name)
        self.anime_tool = build_anime_retriever_tool(self.retriever)
        self.chain_with_tools = self.llm.bind_tools([self.anime_tool])

    def get_recommendation(self, query: str) -> str:
        """
        Generates anime recommendations for a query using the LLM + tool chain.
        """
        try:
            system_instruction = self.prompt_template.template
            messages = [
                SystemMessage(content = system_instruction),
                HumanMessage(content = query)
            ]

            ai_msg = self.chain_with_tools.invoke(messages)
            messages.append(ai_msg)

            if ai_msg.tool_calls:
                for tool_call in ai_msg.tool_calls:
                    if tool_call['name'] == "anime_retriever_tool":
                        tool_result = self.anime_tool.invoke(messages)
                        messages.append(tool_result)

                response = self.chain_with_tools.invoke(messages)
                return response.content

            return ai_msg.content
        except Exception as e:
            raise Exception(f"LLM recommendation: {e}") 
               




         
    