# Audio Digits
An interactive speech recognition web app that teaches you to train a machine learning model and recognize spoken digits.<br />
View it on devpost: https://devpost.com/software/audiodigits<br />
View it on youtube: https://youtu.be/Fg1XOgJK8do<br />
<br />
Instructions for local use <br />
* Install python 3.6.6 (suggested install some kind of virtualenv)
* `pip install Flask scikit-learn` flask to serve the dynamic webapp and scikit-learn that includes other necessary modules scipy and numpy
* Clone this repository
* Navigate to the root of the repository
* `set FLASK_ENV=development`
* `set FLASK_APP=./webapp.py`
* `flask run`

Note:<br />
* The "documents" directory contains prior research that inspired the project. The directory can be ignored.
* Ignore the ".idea" directory unless you want it for development in pycharm.
