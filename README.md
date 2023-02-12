<!-- ABOUT THE PROJECT -->
## About the project

Many great weather apps exist. However, using them requires a lot of effort, especially in the morning.

That was exactly my problem.

I got tired of opening my phone menu, clicking on the app and manually refreshing the weather forecast. Instead, I have decided to simplify this procedure by creating an application that would send me a text message with the weather forecast if it is going to rain for the next 12 hours every single day at 07:00.

My biggest issue was that I could not know if I have to pick up my rain coat to go to work that day or not...

With this project, I propose a way to get informed about the upcoming weather changes, without putting that much effort in the morning. 
This can help the user to prevent from getting soaked but also save 1-2 minutes every single morning before going to work.

The model is trained on daily hourly timeseries data from 07:00 to 16:00. The training set consists of 8677, validation set of 2170 and test set of 4650 rows of data.
The model is trained with a simple Random Forest Classifier, reaching an accuracy of ~85% on the test set.

The scope of the project was not to build a very precise weather forecaster, but to get my hands on Kubernetes and build a pipeline with which I could mine data, track the performance of the model and in the end implement CI/CD.

In this repository, one can get inspired to create something similar himself, as the source code includes:
1. Timeseries data processing
2. Model training
3. Data loading and storing in a local SQL server
4. Results visualization
5. Scheduling with Kubernetes

I have used minikubes for local Kubernetes on 2x Raspberry pi 4. 
A guide how to build a Raspberrypi cluster can be found:
https://ubuntu.com/tutorials/how-to-kubernetes-cluster-on-raspberry-pi#1-overview

### Workflow 
Every single morning there is a scheduled Kubernetes cronjob which creates a new pod and runs the Docker container. Inside the Docker container, newest weather data is pulled and stored in a local database hosted on one of Raspberry pi's. Next, the received data is passed to the model, which at 07:00 predicts if there is going to be rain for the next 12 hours to cover the full work-day. The predictions are stored and the next day compared with the actual values. Since this is a classification problem, only the accuracy is computed as the evaluation metric. 

By slightly modifying the source code, one can achieve the same on the local computer for a specifically selected area of interest. Just make sure to get the API Keys from visualcrossing Twilio. 

However, due to the current time and hardware limits, creation of the CI/CD pipeline is postponed until autumn. Of course, it would be possible to put this on a cloud, but I wanted to utilize my own hardware. To train a RF ML model a fast proccessing time is required, thus a hardware upgrade is needed. 

The pipeline for the project is as follows:
![alt text](https://github.com/Bagiukstis/rain_clustering/blob/main/graphics/pipeline.png)

Outcome:

<img src="https://github.com/Bagiukstis/rain_clustering/blob/main/graphics/sms.jpg" width="512"/>

## Built with
The tech stack used for this project:
1. sklearn
2. MLflow
3. MySQL
4. Docker
5. Kubernetes (with minikube and kubectl)

## Results

D-1 Evaluation for the entire month of January reaches a mean accuracy of 94%:
<img src="https://github.com/Bagiukstis/rain_clustering/blob/main/graphics/accuracy.png" width="1024"/>

## Future improvements

Train the model with more data (autumn).
Implement a CI/CD pipeline to regularly retrain new models and check their performance (autumn).
