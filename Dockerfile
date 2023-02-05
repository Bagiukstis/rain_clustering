FROM python:3.8
RUN mkdir -p /k8s_rain_clustering/
RUN apt-get update
RUN apt-get install -y python3-pymysql
WORKDIR /k8s_rain_clustering/
COPY requirements.txt /k8s_rain_clustering/
RUN pip install no-cache-dir -r requirements.txt
COPY . /k8s_rain_clustering/
ENV APP_ENV development
EXPOSE 4025
VOLUME ["/app-data"]
CMD ["python", "./src/inference.py"]