from ai_anime_recomender.data_loader import AnimeDataLoader
from ai_anime_recomender.vectore_store import VectoreStoreBuilder
from utils.logger import get_logger
from utils.custom_exception import CustomeException

from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

def main():
    try:
        logger.info("Starting to build pipeline...")
        loader = AnimeDataLoader("data/anime_with_synopsis.csv", "data/anime_updated.csv")
        processed_csv = loader.load_and_process()

        logger.info("Data  loaded and processed...")

        vectoer_builder = AnimeDataLoader(processed_csv)
        vectoer_builder.load_and_process()

        logger.info("Vector store Built sucesfully....")
        logger.info("Pipeline built sucessfully....")

    except Exception as e:
        logger.error(f"Failed to execute pipeline {str(e)}")
        raise CustomeException("Error during pipeline ", e)


if __name__ == "__main__":
    main()