from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingManager:
    """
    Отвечает за преобразование текста в векторные представления (эмбеддинги).
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Инициализирует менеджер и загружает модель для эмбеддингов.

        Args:
            model_name: Название модели из библиотеки sentence-transformers.
        """
        self.model = SentenceTransformer(model_name)

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Создает векторное представление для заданного текста.

        Args:
            text: Текст для преобразования.

        Returns:
            Numpy-массив, представляющий вектор.
        """
        return self.model.encode(text)
