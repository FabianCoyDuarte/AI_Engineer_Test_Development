FROM python:3.10.4-alpine3.15

COPY . .
RUN python3 -m pip install --upgrade pip
RUN python3 -m venv venv  # Create virtual environment
RUN source venv/bin/activate  # Activate virtual environment
RUN pip3 install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
