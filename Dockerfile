FROM python:3.9

# Copy repo
WORKDIR /code
COPY . .

# For OpenCV
RUN apt-get update && \
    apt-get -y install libgl1-mesa-glx libglib2.0-0

# Install python dependencies
RUN pip install -r requirements.txt

# Run container
EXPOSE 80
CMD ["python", "-m", "uvicorn", "main:app", "--port", "80", "--host", "0.0.0.0"]
