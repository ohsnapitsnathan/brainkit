import serial
import time
ser=serial.Serial()
stimulator=False
import serial.tools.list_ports

def closeConnection():
    ser.close()
    
def getConnection(port):
    print("Connecting...")
    ser.port=port
    ser.baudrate=115200
    ser.open()

def startStim(mode):
    ser.flushInput()
    poll=0
    succeeded=False
    ser.write(str(mode))
    while not succeeded and poll < 50 and mode != 300:
        theData=ser.readline()
        if str(mode) in theData:
            succeeded=True
        poll=poll+1
    if (poll > 50):
        print("Command "+mode+" failed!")
    
def flushData():
    ser.flushInput()
def getPorts():
    
    return (list(serial.tools.list_ports.comports()))
def getData():
        theData=ser.readline()
        if not stimulator:
            outData=[]
            formatted=theData.replace("\n","").split(",")
            for item in formatted:
                if len(item) > 1:
                    if "SHUTDOWN" not in item:
                        outData.append(float(item))
                    else:
                        outData.append(item)
            return outData
        else:
            formatted=theData.replace("\n","")
            return theData
