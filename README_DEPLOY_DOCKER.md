# Docker Deployment for Crowd-sense

## Build the Docker image

From the project root:

```bash
docker build -t crowd-sense .
```

> Note: `gunicorn` is required by the Docker startup command and is installed from `requirements.txt`.

## Run the container

```bash
docker run -p 5000:5000 -v %cd%\uploads:/app/uploads -e SECRET_KEY=your_secret_key crowd-sense
```

## Use docker-compose

```bash
docker-compose up --build
```

## Access the app

Open:

```text
http://localhost:5000
```

## Notes

- `yolov8n.pt` must exist in the project root.
- The Docker image installs OpenCV system libraries needed by `opencv-python`.
- The `uploads` folder is mounted so uploaded videos persist.
- If you deploy in production, use a strong `SECRET_KEY` and consider a managed volume for uploads.

## Cloud deployment options

### DigitalOcean App Platform / Render / Fly.io / AWS ECS / Google Cloud Run

1. Push repo to GitHub.
2. Create a new service and point it to the repo.
3. Use the Dockerfile as the build configuration.
4. Expose port `5000`.

### GPU support

If you need GPU acceleration for the YOLO model, deploy to a host with GPU support and install a CUDA-enabled Torch wheel instead of the CPU-only wheel in `requirements.txt`.
