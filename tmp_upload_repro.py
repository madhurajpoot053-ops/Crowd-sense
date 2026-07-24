import io
from app import app

client = app.test_client()
response = client.post(
    '/upload',
    data={'video': (io.BytesIO(b'123'), 'test_upload.mp4')},
    content_type='multipart/form-data',
)
print('status=', response.status_code)
print('location=', response.headers.get('Location'))
print('body=', response.get_data(as_text=True)[:500])
