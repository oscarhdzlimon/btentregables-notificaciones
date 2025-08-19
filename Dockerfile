FROM python:3.13-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8005

ENTRYPOINT ["python", "manage.py"]
CMD ["start_scheduler"]