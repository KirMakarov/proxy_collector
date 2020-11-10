FROM python:3.8-slim
EXPOSE 7878
WORKDIR /server_src
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .

CMD ["python", "./server.py"]
