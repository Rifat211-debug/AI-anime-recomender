from src.recommender import AnimeRecommender
from src.vectore_store import VectoreStoreBuilder
from config.config import model_name
from utils.logger import get_logger
from utils.custom_exception import CustomeException

logger = get_logger(__name__)

class AnimeRecommendationPipeline:
    def __init__(self, persist_dir = 'chroma_db'):
        try:
            logger.info("Initializing Recommendation Pipeline")
            vector_builder = VectoreStoreBuilder(
                csv_path = "", persist_dir = persist_dir
            )
            retriever = vector_builder.load_vector_store().as_retriever()
            self.recommender = AnimeRecommender(
                retriever = retriever,
                model_name = model_name
            )

            logger.info("Pipeline Initialized Successfully!")

        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {str(e)}")
            raise CustomeException(
                "Error during pipeline initialization", e
            ) 

    def recommend(self, query: str) -> str:
         try:
            logger.info(f"Received Query: {query}")
            return self.recommender.get_recommendation(query)
         except Exception as e:
            logger.error(f"Failed Recommedation: {str(e)}")
            raise CustomeException(
                    "Error during recommendation", e
                )
                             
