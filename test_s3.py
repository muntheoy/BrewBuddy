import requests
import json

url = 'http://localhost:5000/products'

files = {
    'image': ('product.jpg', open('product.jpg', 'rb'), 'image/jpeg')
}

data = {
    'name': 'цвиты',
    'price': '100.00'
}

headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0OTA2NzY0NSwianRpIjoiY2YzMzJiYmQtODgxYS00Y2YzLWJkOTEtOGJkMWNhMjZjMTA0IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3NDkwNjc2NDUsImNzcmYiOiJmYzA5ZGFjOC1mMzc1LTRkZjQtYTkyMy00NGRlZmFiNmEzZmYiLCJleHAiOjE3NDk2NzI0NDV9.7QdK4FEi9QUcrbHBY7Vxm7sus-S_bODVg1O6K53Z5fY'
}

try:
    print("Отправка запроса...")
    response = requests.post(url, files=files, data=data, headers=headers)
    
    print(f"\nСтатус ответа: {response.status_code}")
    print(f"Заголовки ответа: {dict(response.headers)}")
    
    try:
        response_json = response.json()
        print("\nСодержимое ответа:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("\nСодержимое ответа (не JSON):")
        print(response.text)
        
except requests.exceptions.RequestException as e:
    print(f"\nОшибка при выполнении запроса: {str(e)}")
finally:
    # Закрываем файл
    files['image'][1].close()