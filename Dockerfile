FROM sanicframework/sanic:3.9-latest

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir /src
COPY /src /src

EXPOSE 8080

ENTRYPOINT ["python3", "/src/server.py"]
