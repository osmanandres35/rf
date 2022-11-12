from time import sleep
import _thread
import RPi.GPIO as GPIO
import MFRC522
import signal
import serial
import string
import pynmea2
from datetime import datetime

def uidToString(uid):
    mystring = ""
    for i in uid:
        mystring = format(i, '02X') + mystring
    return mystring

ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=.5)


MIFAREReader = MFRC522.MFRC522()
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
buzzer=26
GPIO.setup(buzzer,GPIO.OUT)
file = open("/home/pi/Desktop/geo.csv", "a")
 
def core0_thread():

    while True:
        hora = datetime.now().strftime('%d/%m/%Y,%H:%M:%S')
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

        if status == MIFAREReader.MI_OK:
            
            (status, uid) = MIFAREReader.MFRC522_SelectTagSN()

            if status == MIFAREReader.MI_OK:
                print("ID " + uidToString(uid))
                file = open("/home/pi/Desktop/geo.csv", "a")
                file.write(str("labor")+","+uidToString(uid)+","+str("10")+","+str(hora)+"\n")
                file.flush()
                file.close()
                GPIO.output(buzzer,GPIO.HIGH)
                sleep(0.3) 
                GPIO.output(buzzer,GPIO.LOW)
                sleep(3)
            else:
                print("Authentication error")
     
     
def core1_thread():

    while True:
        hora = datetime.now().strftime('%d/%m/%Y,%H:%M:%S')
        dataout = pynmea2.NMEAStreamReader()
        newdata=ser.readline().decode('unicode_escape')
        
        if newdata[0:6] == "$GPRMC":
            newmsg=pynmea2.parse(newdata)
            lat=newmsg.latitude
            lng=newmsg.longitude
            gps = "Latitude=" + str(lat) + " and Longitude=" + str(lng)
            file = open("/home/pi/Desktop/geo.csv", "a")
            file.write(str(lat)+","+str(lng)+","+str("10")+","+str(hora)+"\n")
            file.flush()
            file.close()
            print("guardado")
            leep(5) 
     
second_thread = _thread.start_new_thread(core1_thread, ())
 
core0_thread()