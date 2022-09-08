FROM python:3-slim

COPY ./ ./flash-sale-concierge

WORKDIR /flash-sale-concierge

RUN pip3 install pip --upgrade && pip3 install -r requirements.txt

EXPOSE 8080

CMD ["python3", "main.py", "BOT", "TELEGRAM"] 