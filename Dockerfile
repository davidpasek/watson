FROM python:3

WORKDIR /usr/src/wattson

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./wattson.py" ]

