
import tkinter as tk
from tkinter import *
import cv2
import csv
import os
import numpy as np
from PIL import Image, ImageTk
import pandas as pd
import datetime
import time
import pymysql


# Database Initialization (Normalized Schema)

def initialize_db():
    try:
        connection = pymysql.connect(host='localhost', user='root', password='enter yours', db='attendance_db')
        cursor = connection.cursor()
        # Create Student table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Student (
                Enrollment VARCHAR(100) PRIMARY KEY,
                Name VARCHAR(50) NOT NULL
            );
        """)
        # Create Subject table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Subject (
                SubjectID INT AUTO_INCREMENT PRIMARY KEY,
                SubjectName VARCHAR(100) UNIQUE NOT NULL
            );
        """)
        # Create Attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Attendance (
                AttendanceID INT AUTO_INCREMENT PRIMARY KEY,
                Enrollment VARCHAR(100),
                SubjectID INT,
                Date DATE,
                Time TIME,
                FOREIGN KEY (Enrollment) REFERENCES Student(Enrollment),
                FOREIGN KEY (SubjectID) REFERENCES Subject(SubjectID)
            );
        """)
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print("Error initializing database:", e)

# Call initialization at startup
initialize_db()

# Utility function for obtaining a DB connection
def get_db_connection():
    try:
        connection = pymysql.connect(host='localhost', user='root', password='2003', db='attendance_db')
        return connection
    except Exception as e:
        print("Database connection error:", e)
        return None

# Manual Attendance Section

def manually_fill():
    global sb
    sb = tk.Tk()
    sb.title("Enter Subject Name for Manual Attendance")
    sb.geometry('580x320')
    sb.configure(background='grey80')

    def err_screen_for_subject():
        def ec_delete():
            ec.destroy()
        global ec
        ec = tk.Tk()
        ec.geometry('300x100')
        ec.title('Warning!!')
        ec.configure(background='snow')
        Label(ec, text='Please enter your subject name!!!', fg='red', bg='white',
              font=('times', 16, 'bold')).pack()
        Button(ec, text='OK', command=ec_delete, fg="black", bg="lawn green",
               width=9, height=1, activebackground="Red", font=('times', 15, 'bold')).place(x=90, y=50)

    def fill_attendance():
        ts = time.time()
        date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        time_str = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        global subb
        subb = SUB_ENTRY.get().strip()
        if subb == '':
            err_screen_for_subject()
            return
        
        # Connect to the database and check/insert Subject
        connection = get_db_connection()
        if connection is None:
            return
        cursor = connection.cursor()
        cursor.execute("SELECT SubjectID FROM Subject WHERE SubjectName = %s", (subb,))
        subject_data = cursor.fetchone()
        if subject_data is None:
            cursor.execute("INSERT INTO Subject (SubjectName) VALUES (%s)", (subb,))
            connection.commit()
            cursor.execute("SELECT SubjectID FROM Subject WHERE SubjectName = %s", (subb,))
            subject_data = cursor.fetchone()
        subject_id = subject_data[0]
        
        sb.destroy()  # Close the subject entry window

        # Create the Manual Attendance Window
        MFW = tk.Tk()
        MFW.title("Manual Attendance for " + subb)
        MFW.geometry('880x470')
        MFW.configure(background='grey80')

        def del_errsc2():
            errsc2.destroy()

        def err_screen1():
            global errsc2
            errsc2 = tk.Tk()
            errsc2.geometry('330x100')
            errsc2.title('Warning!!')
            errsc2.configure(background='grey80')
            Label(errsc2, text='Please enter Student Enrollment & Name!!!', fg='black', bg='white',
                  font=('times', 16, 'bold')).pack()
            Button(errsc2, text='OK', command=del_errsc2, fg="black", bg="lawn green",
                   width=9, height=1, activebackground="Red", font=('times', 15, 'bold')).place(x=90, y=50)

        def testVal(inStr, acttyp):
            if acttyp == '1':  # on insert
                if not inStr.isdigit():
                    return False
            return True

        ENR = tk.Label(MFW, text="Enter Enrollment", width=15, height=2, fg="black", bg="grey", font=('times', 15))
        ENR.place(x=30, y=100)
        STU_NAME = tk.Label(MFW, text="Enter Student Name", width=15, height=2, fg="black", bg="grey", font=('times', 15))
        STU_NAME.place(x=30, y=200)

        global ENR_ENTRY
        ENR_ENTRY = tk.Entry(MFW, width=20, validate='key', bg="white", fg="black", font=('times', 23))
        ENR_ENTRY['validatecommand'] = (ENR_ENTRY.register(testVal), '%P', '%d')
        ENR_ENTRY.place(x=290, y=105)

        def remove_enr():
            ENR_ENTRY.delete(0, tk.END)

        STUDENT_ENTRY = tk.Entry(MFW, width=20, bg="white", fg="black", font=('times', 23))
        STUDENT_ENTRY.place(x=290, y=205)

        def remove_student():
            STUDENT_ENTRY.delete(0, tk.END)

        # Insert a new attendance record
        def enter_data_DB():
            enrollment = ENR_ENTRY.get().strip()
            student_name = STUDENT_ENTRY.get().strip()
            if enrollment == '' or student_name == '':
                err_screen1()
            else:
                # Check if student exists in the Student table; if not, insert it.
                cursor.execute("SELECT Enrollment FROM Student WHERE Enrollment = %s", (enrollment,))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO Student (Enrollment, Name) VALUES (%s, %s)", (enrollment, student_name))
                    connection.commit()
                # Insert attendance record into Attendance table
                insert_sql = "INSERT INTO Attendance (Enrollment, SubjectID, Date, Time) VALUES (%s, %s, %s, %s)"
                try:
                    cursor.execute(insert_sql, (enrollment, subject_id, date_str, time_str))
                    connection.commit()
                except Exception as e:
                    print("Error inserting attendance record:", e)
                ENR_ENTRY.delete(0, tk.END)
                STUDENT_ENTRY.delete(0, tk.END)

        def create_csv():
            # Export Attendance records for the given subject and date
            query = """
                SELECT at.AttendanceID, at.Enrollment, s.Name, at.Date, at.Time
                FROM Attendance at 
                LEFT JOIN Student s ON at.Enrollment = s.Enrollment
                LEFT JOIN Subject sub ON at.SubjectID = sub.SubjectID
                WHERE sub.SubjectName = %s AND at.Date = %s
            """
            cursor.execute(query, (subb, date_str))
            records = cursor.fetchall()
            csv_name = 'Attendance/Manual_Attendance_' + subb.replace(" ", "_") + '_' + date_str + '.csv'
            with open(csv_name, "w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["AttendanceID", "Enrollment", "Name", "Date", "Time"])
                csv_writer.writerows(records)
            Notifi.configure(text="CSV created Successfully", bg="Green", fg="white",
                             width=33, font=('times', 19, 'bold'))
            Notifi.place(x=180, y=380)
            # Display CSV content in a new window
            root = tk.Tk()
            root.title("Attendance for " + subb)
            root.configure(background='grey80')
            with open(csv_name, newline="") as file:
                reader = csv.reader(file)
                r = 0
                for row in reader:
                    c = 0
                    for col in row:
                        label = tk.Label(root, width=18, height=1, fg="black", font=('times', 13, 'bold'),
                                         bg="white", text=col, relief=tk.RIDGE)
                        label.grid(row=r, column=c)
                        c += 1
                    r += 1
            root.mainloop()

        Notifi = tk.Label(MFW, text="CSV created Successfully", bg="Green", fg="white",
                          width=33, height=2, font=('times', 19, 'bold'))

        c1ear_enroll = tk.Button(MFW, text="Clear", command=remove_enr, fg="white", bg="black",
                                  width=10, height=1, activebackground="white", font=('times', 15, 'bold'))
        c1ear_enroll.place(x=690, y=100)
        c1ear_student = tk.Button(MFW, text="Clear", command=remove_student, fg="white", bg="black",
                                   width=10, height=1, activebackground="white", font=('times', 15, 'bold'))
        c1ear_student.place(x=690, y=200)
        DATA_SUB = tk.Button(MFW, text="Enter Data", command=enter_data_DB, fg="black", bg="SkyBlue1",
                             width=20, height=2, activebackground="white", font=('times', 15, 'bold'))
        DATA_SUB.place(x=170, y=300)
        MAKE_CSV = tk.Button(MFW, text="Convert to CSV", command=create_csv, fg="black", bg="SkyBlue1",
                             width=20, height=2, activebackground="white", font=('times', 15, 'bold'))
        MAKE_CSV.place(x=570, y=300)

        def attf():
            import subprocess
            subprocess.Popen(r'explorer /select,"D:\project\face attandance project\face attandance project final\Attendance\-------Check atttendance-------"')
        attf_btn = tk.Button(MFW, text="Check Sheets", command=attf, fg="white", bg="black",
                             width=12, height=1, activebackground="white", font=('times', 14, 'bold'))
        attf_btn.place(x=730, y=410)
        MFW.mainloop()
        cursor.close()
        connection.close()

    SUB = tk.Label(sb, text="Enter Subject:", width=15, height=2, fg="black", bg="grey80",
                   font=('times', 15, 'bold'))
    SUB.place(x=30, y=100)
    global SUB_ENTRY
    SUB_ENTRY = tk.Entry(sb, width=20, bg="white", fg="black", font=('times', 23))
    SUB_ENTRY.place(x=250, y=105)
    fill_manual_attendance = tk.Button(sb, text="Fill Attendance", command=fill_attendance, fg="black",
                                       bg="SkyBlue1", width=20, height=2, activebackground="white",
                                       font=('times', 15, 'bold'))
    fill_manual_attendance.place(x=250, y=160)
    sb.mainloop()

# Automatic Attendance Section

def subjectchoose():
    def Fillattendances():
        Subject = tx.get().strip()
        if Subject == '':
            err_screen1()
            return
        
        ts = time.time()
        date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        time_str = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        
        connection = get_db_connection()
        if connection is None:
            return
        cursor = connection.cursor()
        # Check/insert subject into Subject table
        cursor.execute("SELECT SubjectID FROM Subject WHERE SubjectName = %s", (Subject,))
        subject_data = cursor.fetchone()
        if subject_data is None:
            cursor.execute("INSERT INTO Subject (SubjectName) VALUES (%s)", (Subject,))
            connection.commit()
            cursor.execute("SELECT SubjectID FROM Subject WHERE SubjectName = %s", (Subject,))
            subject_data = cursor.fetchone()
        subject_id = subject_data[0]
        
        # Face recognition attendance process
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        try:
            recognizer.read("TrainingImageLabel/Trainner.yml")
        except:
            Notifica.configure(text='Model not found, please train model', bg="red", fg="black",
                              width=33, font=('times', 15, 'bold'))
            Notifica.place(x=20, y=250)
            return

        harcascadePath = "haarcascade_frontalface_default.xml"
        faceCascade = cv2.CascadeClassifier(harcascadePath)
        df = pd.read_csv("StudentDetails/StudentDetails.csv")
        cam = cv2.VideoCapture(0)
        font = cv2.FONT_HERSHEY_SIMPLEX
        col_names = ['Enrollment', 'Name', 'Date', 'Time']
        attendance = pd.DataFrame(columns=col_names)
        now = time.time()
        future = now + 20  # run for 20 seconds

        while True:
            ret, im = cam.read()
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(gray, 1.2, 5)
            for (x, y, w, h) in faces:
                Id, conf = recognizer.predict(gray[y:y+h, x:x+w])
                if conf < 70:
                    ts = time.time()
                    current_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    current_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                    aa = df.loc[df['Enrollment'] == Id]['Name'].values
                    tt = str(Id) + "-" + str(aa)
                    attendance.loc[len(attendance)] = [Id, aa, current_date, current_time]
                    cv2.rectangle(im, (x, y), (x+w, y+h), (0,255,0), 2)
                    cv2.putText(im, str(tt), (x, y-10), font, 1, (255,255,0), 2)
                else:
                    Id = 'Unknown'
                    tt = str(Id)
                    cv2.rectangle(im, (x, y), (x+w, y+h), (0,0,255), 2)
                    cv2.putText(im, str(tt), (x, y-10), font, 1, (0,0,255), 2)
            if time.time() > future:
                break
            attendance = attendance.drop_duplicates(['Enrollment'], keep='first')
            cv2.imshow('Filling Attendance...', im)
            key = cv2.waitKey(30) & 0xff
            if key == 27:
                break

        ts = time.time()
        current_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        current_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        fileName = "Attendance/" + Subject.replace(" ", "_") + "_" + current_date + "_" + current_time.replace(":", "-") + ".csv"
        attendance = attendance.drop_duplicates(['Enrollment'], keep='first')
        attendance.to_csv(fileName, index=False)

        # Insert each attendance record into Attendance table
        for index, row in attendance.iterrows():
            enrollment_val = row['Enrollment']
            student_name_val = row['Name']
            # Check if student exists; if not, insert into Student table
            cursor.execute("SELECT Enrollment FROM Student WHERE Enrollment = %s", (enrollment_val,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO Student (Enrollment, Name) VALUES (%s, %s)", (enrollment_val, str(student_name_val)))
                connection.commit()
            insert_sql = "INSERT INTO Attendance (Enrollment, SubjectID, Date, Time) VALUES (%s, %s, %s, %s)"
            try:
                cursor.execute(insert_sql, (enrollment_val, subject_id, row['Date'], row['Time']))
            except Exception as ex:
                print("Error inserting automatic attendance record:", ex)
        connection.commit()

        Notifica.configure(text='Attendance filled Successfully', bg="Green", fg="white",
                          width=33, font=('times', 15, 'bold'))
        Notifica.place(x=20, y=250)
        cam.release()
        cv2.destroyAllWindows()

        # Display CSV content
        root = tk.Tk()
        root.title("Attendance for " + Subject)
        root.configure(background='grey80')
        with open(fileName, newline="") as file:
            reader = csv.reader(file)
            r = 0
            for row in reader:
                c = 0
                for col in row:
                    label = tk.Label(root, width=10, height=1, fg="black", font=('times', 15, 'bold'),
                                     bg="white", text=col, relief=RIDGE)
                    label.grid(row=r, column=c)
                    c += 1
                r += 1
        root.mainloop()
        cursor.close()
        connection.close()

    def err_screen1():
        global sc2
        sc2 = tk.Tk()
        sc2.geometry('300x100')
        sc2.title('Warning!!')
        sc2.configure(background='grey80')
        Label(sc2, text='Please enter your subject name!!!', fg='black', bg='white', font=('times', 16)).pack()
        Button(sc2, text='OK', command=lambda: sc2.destroy(), fg="black", bg="lawn green",
               width=9, height=1, activebackground="Red", font=('times', 15, 'bold')).place(x=90, y=50)

    windo = tk.Tk()
    windo.title("Enter Subject Name for Automatic Attendance")
    windo.geometry('580x320')
    windo.configure(background='grey80')
    Notifica = tk.Label(windo, text="Attendance filled Successfully", bg="Green", fg="white",
                        width=33, height=2, font=('times', 15, 'bold'))

    def Attf():
        import subprocess
        subprocess.Popen(r'explorer /select,"D:\project\face attandance project\face attandance project final\Attendance\-------Check atttendance-------"')
    attf_btn = tk.Button(windo, text="Check Sheets", command=Attf, fg="white", bg="black",
                         width=12, height=1, activebackground="white", font=('times', 14, 'bold'))
    attf_btn.place(x=430, y=255)
    sub = tk.Label(windo, text="Enter Subject:", width=15, height=2, fg="black", bg="grey",
                   font=('times', 15, 'bold'))
    sub.place(x=30, y=100)
    global tx
    tx = tk.Entry(windo, width=20, bg="white", fg="black", font=('times', 23))
    tx.place(x=250, y=105)
    fill_a = tk.Button(windo, text="Fill Attendance", fg="white", command=Fillattendances, bg="SkyBlue1",
                       width=20, height=2, activebackground="white", font=('times', 15, 'bold'))
    fill_a.place(x=250, y=160)
    windo.mainloop()

# Other Functions

def clear():
    txt.delete(0, tk.END)

def clear1():
    txt2.delete(0, tk.END)

def err_screen():
    global sc1
    sc1 = tk.Tk()
    sc1.geometry('300x100')
    sc1.title('Warning!!')
    sc1.configure(background='grey80')
    Label(sc1, text='Enrollment & Name required!!!', fg='black', bg='white',
          font=('times', 16)).pack()
    Button(sc1, text='OK', command=lambda: sc1.destroy(), fg="black", bg="lawn green",
           width=9, height=1, activebackground="Red", font=('times', 15, 'bold')).place(x=90, y=50)

def take_img():
    l1 = txt.get().strip()
    l2 = txt2.get().strip()
    if l1 == '' or l2 == '':
        err_screen()
    else:
        try:
            cam = cv2.VideoCapture(0)
            detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
            Enrollment = l1
            Name = l2
            sampleNum = 0
            while True:
                ret, img = cam.read()
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    sampleNum += 1
                    cv2.imwrite("TrainingImage/" + Name + "." + Enrollment + '.' + str(sampleNum) + ".jpg", gray)
                    cv2.imshow('Frame', img)
                if cv2.waitKey(1) & 0xFF == ord('q') or sampleNum > 70:
                    break
            cam.release()
            cv2.destroyAllWindows()
            ts = time.time()
            date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            time_str = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            row = [Enrollment, Name, date_str, time_str]
            with open('StudentDetails/StudentDetails.csv', 'a+', newline="") as csvFile:
                writer = csv.writer(csvFile)
                writer.writerow(row)
            # Insert into Student table if not exists
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT Enrollment FROM Student WHERE Enrollment = %s", (Enrollment,))
                if cursor.fetchone() is None:
                    cursor.execute("INSERT INTO Student (Enrollment, Name) VALUES (%s, %s)", (Enrollment, Name))
                    connection.commit()
                cursor.close()
                connection.close()
            res = "Images Saved for Enrollment: " + Enrollment + " Name: " + Name
            Notification.configure(text=res, bg="SpringGreen3", width=50, font=('times', 18, 'bold'))
            Notification.place(x=250, y=400)
        except Exception as e:
            Notification.configure(text=str(e), bg="Red", width=50)
            Notification.place(x=250, y=400)

def admin_panel():
    win = tk.Tk()
    win.title("LogIn")
    win.geometry('880x420')
    win.configure(background='grey80')

    def log_in():
        username = un_entr.get().strip()
        password = pw_entr.get().strip()
        if username == 'rupam' and password == 'rupam123':
            win.destroy()
            root = tk.Tk()
            root.title("Student Details")
            root.configure(background='grey80')
            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM Student")
                records = cursor.fetchall()
                cursor.close()
                connection.close()
            else:
                records = []
            r = 0
            for row in records:
                c = 0
                for col in row:
                    label = tk.Label(root, width=10, height=1, fg="black", font=('times', 15, 'bold'),
                                     bg="white", text=col, relief=RIDGE)
                    label.grid(row=r, column=c)
                    c += 1
                r += 1
            root.mainloop()
        else:
            Nt.configure(text='Incorrect ID or Password', bg="red", fg="white",
                         width=38, font=('times', 19, 'bold'))
            Nt.place(x=120, y=350)

    Nt = tk.Label(win, text="Attendance filled Successfully", bg="Green", fg="white",
                  width=40, height=2, font=('times', 19, 'bold'))
    un = tk.Label(win, text="Enter Username:", width=15, height=2, fg="black", bg="grey",
                  font=('times', 15, 'bold'))
    un.place(x=30, y=50)
    pw = tk.Label(win, text="Enter Password:", width=15, height=2, fg="black", bg="grey",
                  font=('times', 15, 'bold'))
    pw.place(x=30, y=150)
    un_entr = tk.Entry(win, width=20, bg="white", fg="black", font=('times', 23))
    un_entr.place(x=290, y=55)
    pw_entr = tk.Entry(win, width=20, show="*", bg="white", fg="black", font=('times', 23))
    pw_entr.place(x=290, y=155)
    c0 = tk.Button(win, text="Clear", command=lambda: un_entr.delete(0, tk.END), fg="white", bg="black",
                   width=10, height=1, activebackground="white", font=('times', 15, 'bold'))
    c0.place(x=690, y=55)
    c1 = tk.Button(win, text="Clear", command=lambda: pw_entr.delete(0, tk.END), fg="white", bg="black",
                   width=10, height=1, activebackground="white", font=('times', 15, 'bold'))
    c1.place(x=690, y=155)
    Login = tk.Button(win, text="LogIn", fg="black", bg="SkyBlue1", width=20, height=2,
                      activebackground="Red", command=log_in, font=('times', 15, 'bold'))
    Login.place(x=290, y=250)
    win.mainloop()

def trainimg():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    global detector
    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    try:
        global faces, Id
        faces, Id = getImagesAndLabels("TrainingImage")
    except Exception as e:
        Notification.configure(text='Please create "TrainingImage" folder and put Images',
                               bg="SpringGreen3", width=50, font=('times', 18, 'bold'))
        Notification.place(x=350, y=400)
        return
    recognizer.train(faces, np.array(Id))
    try:
        recognizer.save("TrainingImageLabel/Trainner.yml")
    except Exception as e:
        Notification.configure(text='Please create "TrainingImageLabel" folder',
                               bg="SpringGreen3", width=50, font=('times', 18, 'bold'))
        Notification.place(x=350, y=400)
        return
    res = "Model Trained"
    Notification.configure(text=res, bg="olive drab", width=50, font=('times', 18, 'bold'))
    Notification.place(x=250, y=400)

def getImagesAndLabels(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faceSamples = []
    Ids = []
    for imagePath in imagePaths:
        pilImage = Image.open(imagePath).convert('L')
        imageNp = np.array(pilImage, 'uint8')
        Id = int(os.path.split(imagePath)[-1].split(".")[1])
        faces = detector.detectMultiScale(imageNp)
        for (x, y, w, h) in faces:
            faceSamples.append(imageNp[y:y+h, x:x+w])
            Ids.append(Id)
    return faceSamples, Ids

# Main Window Setup

window = tk.Tk()
window.title("FAMS-Face Recognition Based Attendance Management System")
window.geometry('1280x720')
window.configure(background='grey80')
window.grid_rowconfigure(0, weight=1)
window.grid_columnconfigure(0, weight=1)

def on_closing():
    from tkinter import messagebox
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)

message = tk.Label(window, text="Face-Recognition-Based-Attendance-Management-System",
                   bg="black", fg="white", width=50, height=3, font=('times', 30, 'bold'))
message.place(x=80, y=20)

Notification = tk.Label(window, text="All things good", bg="Green", fg="white",
                        width=15, height=3, font=('times', 17))
lbl = tk.Label(window, text="Enter Enrollment:", width=20, height=2, fg="black", bg="grey",
               font=('times', 15, 'bold'))
lbl.place(x=200, y=200)

def testVal(inStr, acttyp):
    if acttyp == '1':
        if not inStr.isdigit():
            return False
    return True

txt = tk.Entry(window, validate="key", width=20, bg="white", fg="black", font=('times', 25))
txt['validatecommand'] = (txt.register(testVal), '%P', '%d')
txt.place(x=550, y=210)
lbl2 = tk.Label(window, text="Enter Name:", width=20, fg="black", bg="grey",
                height=2, font=('times', 15, 'bold'))
lbl2.place(x=200, y=300)
txt2 = tk.Entry(window, width=20, bg="white", fg="black", font=('times', 25))
txt2.place(x=550, y=310)
clearButton = tk.Button(window, text="Clear", command=clear, fg="white", bg="black",
                        width=10, height=1, activebackground="white", font=('times', 15, 'bold'))
clearButton.place(x=950, y=210)
clearButton1 = tk.Button(window, text="Clear", command=clear1, fg="white", bg="black",
                         width=10, height=1, activebackground="white", font=('times', 15, 'bold'))
clearButton1.place(x=950, y=310)
AP = tk.Button(window, text="Check Registered Students", command=admin_panel, fg="black", bg="SkyBlue1",
               width=19, height=1, activebackground="white", font=('times', 15, 'bold'))
AP.place(x=990, y=410)
takeImg = tk.Button(window, text="Take Images", command=take_img, fg="black", bg="SkyBlue1",
                    width=20, height=3, activebackground="white", font=('times', 15, 'bold'))
takeImg.place(x=90, y=500)
trainImg = tk.Button(window, text="Train Images", fg="black", command=trainimg, bg="SkyBlue1",
                     width=20, height=3, activebackground="white", font=('times', 15, 'bold'))
trainImg.place(x=390, y=500)
FA = tk.Button(window, text="Automatic Attendance", fg="black", command=subjectchoose, bg="SkyBlue1",
             width=20, height=3, activebackground="white", font=('times', 15, 'bold'))
FA.place(x=690, y=500)
quitWindow = tk.Button(window, text="Manually Fill Attendance", command=manually_fill, fg="black", bg="SkyBlue1",
                       width=20, height=3, activebackground="white", font=('times', 15, 'bold'))
quitWindow.place(x=990, y=500)

window.mainloop()
