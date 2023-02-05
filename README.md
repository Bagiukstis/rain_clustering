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

The scope of the project was not to build a very precise weather forecaster, but to build a pipeline with which I could mine data, track the performance of the model and implement CI/CD.
However, due to the current time limits, creation of the CI/CD pipeline is currently postponed. 

The pipeline for the project is as follows:
![alt text](https://github.com/Bagiukstis/rain_clustering/blob/main/graphics/pipeline.png)

Outcome:

<img src="https://github.com/Bagiukstis/rain_clustering/blob/main/graphics/sms.jpg" width="512"/>

## Built with
The tech stack for this project is:
1. sklearn
2. MLflow
3. MySQL
4. Docker
5. Kubernetes (with minikube and kubectl)


## Getting started

TBD.


## Results


D-1 Evaluation for the entire month of January reaches a mean accuracy of 94%:
<img src="https://github.com/Bagiukstis/rain_clustering/blob/main/graphics/accuracy.png" width="1024"/>

## Future improvements

TBD.
