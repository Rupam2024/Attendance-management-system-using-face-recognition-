Code Requirements

To run this project, ensure you have the following installed:
OpenCV: Install using pip install opencv-python
Tkinter: Comes pre-installed with Python
Pillow (PIL): Install using pip install Pillow
Pandas: Install using pip install pandas
Steps to Run the Project
Clone this repository to your local system.
Create a folder named TrainingImage in the project directory to store the face data.
Open the AMS_Run.py file and update all file paths to match your system's file structure.
Run the AMS_Run.py file to start the application.
How It Works

Collect Face Data:
Enter your ID and Name in the input fields.
Click the Take Images button to capture 200 facial images.
The captured images will be stored in the TrainingImage folder.

Train the Model:
Click the Train Image button to train the face recognition model.
The training process takes approximately 5-10 minutes, depending on the amount of data.
Once complete, the trained model will be saved in the TrainingImageLabel folder.

Automatic Attendance:
Click the Automatic Attendance button to recognize faces and mark attendance using the trained model.
The system will generate a .csv file containing attendance records based on the detected faces, time, and subject.

Manual Attendance:
Use the Manually Fill Attendance button in the UI to record attendance without face recognition.
This also generates a .csv file and stores attendance data in the database.

Database Integration
To store attendance data in a database, install WAMP or any other MySQL server.
Update the database name and connection details in the AMS_Run.py file to match your setup.
Project Structure
The project includes GUI options to capture images, train models, and automate attendance marking.
Attendance data is securely stored in .csv files and can optionally be saved in a MySQL database.
