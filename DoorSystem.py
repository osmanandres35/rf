#!/usr/bin/env python3
# -*- coding: utf8 -*-
#
#    Copyright 2018 Daniel Perron
#
#    Base on Mario Gomez <mario.gomez@teubi.co>   MFRC522-Python
#
#    This file use part of MFRC522-Python
#    MFRC522-Python is a simple Python implementation for
#    the MFRC522 NFC Card Reader for the Raspberry Pi.
#
#    DoorSytem is an implementation of MFRC-Python modifie to used spidev instead of spi 
#    to be able to use python3
#
#    MFRC522-Python is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    MFRC522-Python is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with MFRC522-Python.  If not, see <http://www.gnu.org/licenses/>.
#

import RPi.GPIO as GPIO
import MFRC522
import pymysql
import signal
import time



#relay definition

RELAY_PIN = 12
RELAY_ON  = 0
RELAY_OFF = 1

relay_time=time.time()
relay_status = False


# function to set relay
def setRelay(value):
   global relay_status
   global relay_time
   if value:
     relay_status = True
     relay_time = time.time()
   else:
     relay_status = False
   GPIO.output(RELAY_PIN, RELAY_ON if relay_status else  RELAY_OFF )
#   print("relay status = {}".format(led_status))


#LED DEFINITION

LED_R_PIN = 16
LED_G_PIN = 20
LED_B_PIN = 21
LED_ON = 0
LED_OFF = 1


#set GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN,GPIO.OUT)
GPIO.output(RELAY_PIN,RELAY_OFF)
GPIO.setup(LED_R_PIN,GPIO.OUT)
GPIO.setup(LED_G_PIN,GPIO.OUT)
GPIO.setup(LED_B_PIN,GPIO.OUT)


led_status = False
led_time = time.time()
#FUNCTION TO SET LED

def setLed(R,G,B):
  global led_time
  global led_status
  GPIO.output(LED_R_PIN, LED_ON if R>0 else  LED_OFF)
  GPIO.output(LED_G_PIN, LED_ON if G>0 else  LED_OFF)
  GPIO.output(LED_B_PIN, LED_ON if B>0 else  LED_OFF)
  led_status =  (R+G+B) > 0
  if led_status:
   led_time= time.time();
#  print("ledstatus = {}".format(led_status))

setLed(0,0,0)





continue_reading=True


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    print("Ctrl+C captured, ending read.")
    continue_reading = False
    setRelay(False)
    setLed(0,0,0)
    GPIO.cleanup()

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

# Welcome message
print("Door System using Raspberry Pi")
print("Press Ctrl-C to stop.")



# open an sql session

sql_con = pymysql.connect(host='localhost', user='rfidreader',
                          passwd='password', db='rfidcardsdb')
cur = sql_con.cursor()





# function to read uid an conver it to a string

def uidToString(uid):
  mystring=""
  for i in uid:
    mystring = format(i,'02X') + mystring
  return mystring




# function to read a card and if a new one is in then report it
# otherwise report NULL
# If no card is read after .5 sec clear the old  card info

current_card=None
last_time=time.time()


def readCard():

    global current_card
    global last_time
    # Scan for cards
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
#      print ("Card detected")

      # Get the UID of the card
      (status,uid) = MIFAREReader.MFRC522_SelectTagSN()
      # If we have the UID, continue
      if status == MIFAREReader.MI_OK:
#        print("current_card {}".format(current_card))
#        print("uid {}".format(uid))
        last_time=time.time() #bounce delay to detect no card
        if current_card == uid :
           return None  #same card
        else:
#           print("Card read UID:", uid)
           current_card=uid
           # return a  string of the key
           return uidToString(uid)
#      else:
#        print("Authentication error")

    else:
      #no card
      if abs(time.time() - last_time) > 0.5 :
#        print("no card")
        current_card=None
    #if we are here we didn't detect anything
    return None





###########################
# Check Card
#
# function to check  the RFID card from  the sql database
#
# return true if valid otherwise false

def validateCard(sqlcursor,serial_id):
    global  cardId
    global  userID
    global  serial_no

    #request if the card is valie
    sql_request ='SELECT card_id,serial_no,user_id,valid' + \
          ' FROM cards  WHERE serial_no = "' + serial_id + '"'

    count = sqlcursor.execute(sql_request)

    #how many record we have
    if count == 0:
      print("Card ?:{} from unknown  Refused!".format(serial_id))
      return False


    #ok we have a record
    card = sqlcursor.fetchone()

    #is the card valid
    if card[3]>0 :
      print("Card {}:{} from user {} Accepted!".format(card[0],card[1],card[2]))
      return True;
    else:
      print("Card {}:{} from user {} Invalid".format(card[0],card[1],card[2]))
    return False





while continue_reading:

   card_read =readCard()

   if card_read is not None:
      setLed(1,0,0)
      #print(card_read)
      if validateCard(cur,card_read):
        setLed(0,1,0)
        setRelay(True)
      else:
        setRelay(False)
        setLed(1,0,0)

   #check led turn if off after 5 sec
   if led_status:
     if abs(time.time() - led_time) > 5 :
       setLed(0,0,0)

   #check for relay turn it off after 5 sec
   if relay_status:
     if abs(time.time() - relay_time) > 5:
       setRelay(False)
