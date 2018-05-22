# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render,redirect,HttpResponseRedirect,HttpResponse
from forms import SignUpForm
from models import UserModel,DateModel
import cv2
import numpy as np
import os
import PIL.Image
import datetime
import sendgrid
from sendgrid.helpers.mail import *
# Create your views here.

def landing_view(request):
    return render(request, 'index.html')


module_dir = os.path.dirname(__file__)  # get current directory
face_path = os.path.join(module_dir, 'haarcascade_frontalface_default.xml')
eye_path = os.path.join(module_dir, 'haarcascade_eye.xml')
dataset_path=os.path.join(module_dir,'dataset')
face_detect = cv2.CascadeClassifier(face_path)
eye_cascade = cv2.CascadeClassifier(eye_path)

def face_detector(request):
    if request.method == "POST":
        print "post"
        form= SignUpForm(request.POST)
        if form.is_valid():
            print"valid"
            email=form.cleaned_data['email']
            name=form.cleaned_data['name']
            unique_id=form.cleaned_data['unique_id']
            number=form.cleaned_data['number']
            department=form.cleaned_data['department']
            print name+unique_id
            # saving data to DB
            user = UserModel(name=name,email=email,unique_id=unique_id,number=number,department=department)
            user.save()
            detect_face(name,unique_id)
    return HttpResponse("Face Data has been recorded by machine")

def detect_face(name,unique_id,sampleNumber=0):
        cam = cv2.VideoCapture(0);
        name = name
        id = unique_id
        while (True):
            ret, img = cam.read();
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_detect.detectMultiScale(gray, 1.2, 5)
            for (x, y, w, h) in faces:
                sampleNumber = sampleNumber + 1
                cv2.imwrite(dataset_path + "/" + name + "." + str(id) + "." + str(sampleNumber) + ".jpg",
                            gray[y:y + h, x:x + h])
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = img[y:y + h, x:x + w]
                eyes = eye_cascade.detectMultiScale(roi_gray)
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
                cv2.waitKey(100)
            cv2.imshow("Face", img);
            cv2.waitKey(1)
            if (sampleNumber > 60):
                break;
        cam.release()
        cv2.destroyAllWindows()


def trainer(request):
    recognizer = cv2.createLBPHFaceRecognizer()
    dataset_path = os.path.join(module_dir, 'dataset')
    training_dataset_path = os.path.join(module_dir, 'recognizer')


    Ids, faces = trainer2(dataset_path)
    recognizer.train(faces, np.array(Ids))
    recognizer.save(training_dataset_path+'/trainingdata.yml')
    cv2.destroyAllWindows()
    return HttpResponse("Machine has learned from Face Data")

def trainer2(dataset_path):
        imagePaths = [os.path.join(dataset_path, f) for f in os.listdir(dataset_path)]
        print imagePaths
        faces = []
        IDs = []
        for imagePath in imagePaths:
            faceImg = PIL.Image.open(imagePath).convert('L');
            faceNp = np.array(faceImg, 'uint8')
            id = int(os.path.split(imagePath)[-1].split('.')[1])
            faces.append(faceNp)
            print id
            IDs.append(id)
            cv2.imshow("training", faceNp)
            cv2.waitKey(10)
        return IDs, faces




def recg(request):
    cam = cv2.VideoCapture(0)
    rec = cv2.createLBPHFaceRecognizer()
    training_dataset_path = os.path.join(module_dir, 'recognizer')
    rec.load(training_dataset_path+'\\trainingdata.yml')
    id = 0
    font = cv2.cv.InitFont(cv2.cv.CV_FONT_HERSHEY_SIMPLEX, 1, .5, 0, 1, 1)
    current_date = datetime.date.today()
    users=UserModel.objects.all()
    for user in users:
        check_user=DateModel.objects.filter(user=user,date=current_date,is_present=False)
        if not check_user:
            mark_absent = DateModel.objects.create(user=user, date=current_date, is_present=False)
            mark_absent.save()
    while (True):
        ret, img = cam.read();
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_detect.detectMultiScale(gray, 1.2, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = img[y:y + h, x:x + w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            id, conf = rec.predict(gray[y:y + h, x:x + h])
            str(id)
            user_found=UserModel.objects.filter(unique_id=id).first()
            if user_found:
                cv2.cv.PutText(cv2.cv.fromarray(img), "Name:"+str(user_found.name), (x, w + h+10), font, (0,255,0))
                cv2.cv.PutText(cv2.cv.fromarray(img), "Id:"+str(user_found.unique_id), (x, w + h+35), font, (0,255,0))
                cv2.cv.PutText(cv2.cv.fromarray(img), "Email:"+str(user_found.email), (x, w + h+60), font, (0,255,0))
                cv2.cv.PutText(cv2.cv.fromarray(img), "Number:"+str(user_found.number), (x, w + h+80), font, (0,255,0))
                cv2.cv.PutText(cv2.cv.fromarray(img), "Department:"+str(user_found.department), (x, w + h+100), font, (0,255,0))
                print str(user_found.name)
                try:
                    existing_user=DateModel.objects.filter(user=user_found,date=current_date,is_present=True).first()
                    print"not present till now"
                    if not existing_user:
                        date_model = DateModel.objects.filter(date=current_date, user=user_found).first()
                        date_model.is_present= True
                        date_model.save()
                        print str(date_model.user.name) + " " + str(date_model.is_present)

                except:
                    print "user not found"
        cv2.imshow("Face", img);
        if (cv2.waitKey(1) == ord("q")):
            break;
    cam.release()
    cv2.destroyAllWindows()


    return render(request, 'index.html')





def sendmail(request):
    current_date = datetime.date.today()
    #present_users=DateModel.objects.filter(date=current_date,is_present=True).all()
    absent_users = DateModel.objects.filter(date=current_date, is_present=False).all()
    absent_list=[]
    for user in absent_users:
        absent_person=user.user.email
        print absent_person
        absent_list.append(user.user.name)
        mail_absentise(absent_person)
    names='\n'.join(absent_list)
    print names
    mail_head(names)

    return HttpResponse("Mails Sent")


def mail_absentise(absent_person):
    sg = sendgrid.SendGridAPIClient(apikey="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")
    from_email = Email("rohit.malhotra1420@gmail.com")
    to_email = Email(absent_person)
    subject = "Not attended Class"
    content = Content("text/plain", "You have not attended the class today and marked absent.")
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)

def mail_head(names):
    sg = sendgrid.SendGridAPIClient(apikey="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")
    from_email = Email("rohit.malhotra1420@gmail.com")
    to_email = Email("rohit.malhotra1420@gmail.com")
    subject = "Absentise List"
    content = Content("text/plain", names)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)