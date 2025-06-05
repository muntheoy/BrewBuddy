import os
from flask import current_app
import uuid
from werkzeug.utils import secure_filename

def save_file(file, folder="products"):
    """
    Сохраняет файл в локальное хранилище и возвращает URL
    """
    try:
        # Создаем директорию, если она не существует
        upload_folder = os.path.join(current_app.static_folder, 'uploads', folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Генерируем уникальное имя файла
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Сохраняем файл
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Формируем URL для доступа к файлу
        file_url = f"/static/uploads/{folder}/{unique_filename}"
        return file_url
        
    except Exception as e:
        current_app.logger.error(f"Error saving file: {str(e)}")
        raise 