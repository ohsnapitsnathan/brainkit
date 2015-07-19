from __future__ import division
from itertools import islice, tee
import headset
import time
import urllib2
import numpy as np
import msvcrt
imprintSham=False
current_milli_time = lambda: int(round(time.time() * 1000))
stimModes={"F4":0,"C4":1,"O2":2,"C3":3,"F3":4,"O1":5,"Reference electrode":6}
electrodeNames=["F3","C3","O1","F4","C4","O2"]
offsets={"F3":5,"C3":15,"O1":25,"F4":35,"C4":45,"O2":55}
nyquist=5
shamTimer=current_milli_time()
try:
    from scipy import stats, special
    from scipy.fftpack import rfft,rfftfreq
    from scipy import stats, special
    from scipy.signal import butter, lfilter, firwin
    from math import sqrt
    from scipy.fftpack import rfft,rfftfreq
except ImportError:
    print("There seems to be a problem with the scipy installation. Please download and install scipy-stack.")
    raw_input()
    quit()
from random import *
try:
    import easygui as eg
except ImportError:
    print("There seems to be a problem with the EasyGui installation. Please download and install it.")
    raw_input()
    quit()
try:
    import serial
except ImportError:
    print("There seems to be a problem with the PySerial installation. Please download and install it.")
    raw_input()
    quit()
import math
import os
import subprocess
import thread
import time

def connectStim():
    accepted=False
    choice=""

    while not accepted:
        thePorts=headset.getPorts()
        if len(thePorts) < 1:
            eg.msgbox(title="No devices connected",msg="No devices were detected. Make sure the BrainKit stimulator is connected and powered on and try again")
            portSelect="Cancel"
        else:
            print(str(thePorts))
            portSelect=eg.buttonbox(title="Stimulator port", msg="Select the port to which the stimulator is connected. If you do not know the port, connected or unplug the stimultor and click refresh", choices=[thePorts, "Refresh"])
        if portSelect and "Refresh" not in portSelect:
            accepted=True
            choice=portSelect
    if "Cancel" not in portSelect:
            try:
                print(str(choice))
                print("Attempting to connect to stimulator...")
                headset.getConnection(choice[0][0])
                return True
            except Exception:
                return False
def recordData(filename):
    outFile=open(filename,'w')
    started=time.time()*1000.0
    lastAQ=started
    updateTime=started
    
    keepRunning=True
    headset.startStim(300)
    headset.flushData()
    print("Data aquistion is running, press space to stop.")
    samples=0
    while msvcrt.kbhit():
        msvcrt.getch()
    while keepRunning:
        samples=samples+1
        if msvcrt.kbhit():
            theKey=msvcrt.getch()
            if " " in theKey:
                keepRunning=False
                print("Interrupt")
        theData=headset.getData()
        theData.append("\t0") #for compatibility with old version data files that used this as a trigger code
        theData.append((time.time()*1000.0)-started) #Time since start
        theData.append((time.time()*1000.0)-lastAQ) #Time since last sample
        srate=1000/((time.time()*1000.0)-(lastAQ+1))
        if (time.time()*1000.0)-updateTime > 2000:
            if (srate < 10):
                print("SAMPLE RATE TOO LOW, REDUCE PROCESSING LOAD")
            print("Effective sample rate:"+str(srate)+" Hz")
            updateTime=time.time()*1000.0
        lastAQ=time.time()*1000.0
        for item in theData:
            outFile.write(str(item)+"\t")
        outFile.write("\n")

    outFile.flush()
    outFile.close()
    headset.closeConnection()
        
def createProtocol(preselected_channels=False, preselected_powers=None):
    electrodes=[]
    powers=[]
    outcomes=[]
    anodeChoice=eg.multchoicebox(title="Select electrodes", msg="Select the locations that you want to recieve stimulation. You can set them as anodes or cathodes in the next step.", choices=['F4','C4','O2','C3','F3','O1'])
    if anodeChoice:
        for item in anodeChoice:
            electrodes.append(stimModes[item])
        choices=anodeChoice
        choices.append("Ramp up/down duration (set to 0 for no ramping)")
        choices.append("Stimulation duration (minutes)")
        choices.append("Sham probability(set to 0 for no sham trials")
        choices.append("Frequency (set to 0 for dc stimulation)")
        powers=eg.multenterbox("Enter the power that should be used for each electrode. Positive values represent anodal stimulation, and negative values represent cathodal stimulation. You can also set the duration, ramping parameters, and sham probability of the protocol","Stimulation parameters",choices)
        if powers:
            exMode=eg.ynbox(title="Outcome measures",msg="Do you want to add outcome measures to this protocol?")
            if exMode:
                
                outcomes=[]
                selected=""
                keepPrompting=True
                while keepPrompting:
                    keepPrompting=False
                    prompt=eg.buttonbox(title="Select outcome measures",msg="Current outcome measures:\n"+selected,choices=["Add","Done"])
                    if prompt:
                        keepPrompting=True
                        if "Add" in prompt:
                            name=eg.enterbox(title="Outcome measure name",msg="Enter the name for this outcome measure. Enter NPHYS to use automatically collected neurophsyiological measurements")
                            if name:
    
                                details=eg.buttonbox(title="Logging options",msg="How do you want to collect data on this measure?",choices=['Before stimulation only','After stimulation only','Both before and after stimulation'])
                                name=name.replace("/","")
                                selected=selected+name+ " "+details.lower()+"\n"
                                
                                if 'Before stimulation only' in details:
                                    name=name+"/1"
                                elif 'After stimulation only' in details:
                                    name=name+"/2"
                                else:
                                    name=name+"/3"
                                outcomes.append(name)
                        else:
                            keepPrompting=False
            pwrite=eg.filesavebox(title="Where do you want to save this protocol?",msg="Where do you want to save this protocol?")
            if pwrite:
                outFile=open(pwrite,'w')
                outstring=""
                outstring=outstring+("phaselength:60\n")
                outstring=outstring+("duration:"+powers[len(powers)-3]+"\n")
                outstring=outstring+("rampdur:"+powers[len(powers)-4]+"\n")
                outstring=outstring+("sham:"+powers[len(powers)-2]+"\n")
                outstring=outstring+("frequency:"+powers[len(powers)-1]+"\n")
                outstring=outstring+("****\n")
                for item in outcomes:
                    outstring=outstring+(item+"\n")
                outstring=outstring+("****\n")
                for item in range(0,len(choices)):
                    outstring=outstring+(choices[item]+":"+powers[item]+"\n")
                outFile.write(outstring)
                outFile.flush()
                outFile.close()
def qmean(num):
	return sqrt(float(sum(n*n for n in num))/float(len(num)))
def averageArray(theInput):
    items=0
    total=0
    for item in theInput:
        try:
            total=total+float(item)
            items=items+1
        except Exception:
            1+1
    if (items > 0):
        return total/float(items)
    else:
        return -1
    
def preprocess(lines):
    dataOut=[]
    tempFile=""
    lastLine=""
    deviation=0.0
    lc=0
    for line in lines:
        skipThis=False

        line=line.replace("\t\n","\n") #prevent error from converting \n to float when processing new format files
        splitup=line.split("\t")
        
        lastItem=len(splitup)

        

        timestamp=float(splitup[lastItem-1].replace("\n",""))
        diff=100-timestamp
        deviation=deviation+diff
        if (deviation > 50):
            tempFile=tempFile+line+"\n"
            deviation=deviation-timestamp
        elif (deviation < -50):
            #skipThis=True
            #deviation=deviation+timestamp
            1+1
        if not skipThis :
            tempFile=tempFile+line+"\n"
    lines=tempFile.split("\n")
    
    #now just pull out the data that we want
    for line in lines:
        splitup=line.split("\t")
        if len(splitup) >= 10:
            dataOut.append(splitup[0]+"\t"+splitup[1]+"\t"+splitup[2]+"\t"+splitup[3]+"\t"+splitup[4]+"\t"+splitup[5]+"\t"+splitup[7]+"\n")
    return dataOut
def permCorrelation(data1,data2,permutations, teststat):
    rs=[]
    wtf1=data1
    wtf2=data2
    for perm in range(0,permutations):
        temp1=[]
        temp2=[]
        buf1=wtf1
        buf2=wtf2
        while len(temp1) < len(buf1):
            temp1.append(choice(buf1+buf2))
        #temp1.append(buf1[0])

        while len(temp2) < len(buf2):
            temp2.append(choice(buf2+buf1))
        #temp2.append(buf2[0])
        slope, intercept, r_value, p_value, std_err =stats.linregress(temp1, temp2)
     
        rs.append(r_value)
        #print("Computed permutation "+str(perm)+" of "+str(permutations))
    pval=float(0)
    for item in rs:
        if (abs(item) >= abs(teststat)):
            pval=pval+1
    pval=float(pval)/float(permutations)
    return pval

def permttest(data1,data2,permutations, teststat):
    rs=[]
    wtf1=data1
    wtf2=data2
    for perm in range(0,permutations):
        temp1=[]
        temp2=[]
        buf1=wtf1
        buf2=wtf2
        while len(temp1) < len(buf1):
            temp1.append(choice(buf1+buf2))
        #temp1.append(buf1[0])

        while len(temp2) < len(buf2):
            temp2.append(choice(buf2+buf1))
        #temp2.append(buf2[0])
        tval,pval=stats.ttest_rel(temp1,temp2)
        rs.append(tval)
        #print("Computed permutation "+str(perm)+" of "+str(permutations))
    pval=float(0)

    for item in rs:
        if (abs(item) >= abs(teststat)):
            pval=pval+1
    pval=float(pval)/float(permutations)
    return pval
def getPhysData(filename, winLength,thresh,mode): #get neurophys measures from a file
    thefilter=firwin(251, 0.05, pass_zero=False,nyq=nyquist)
    closedset=[]
    openset=[]
    elecOut=[]
    try:
        print(filename)
        print(os.getcwd())
        theFile=open(filename,'r')
        fileLines=theFile.readlines()
        theFile.close()
        
        #step one:prprocessing and timing error correction
        lines=preprocess(fileLines)
        #step two:filter
        ave1=0
        ave2=0
        ave3=0
        ave4=0
        ave5=0
        ave6=0
        samples=0
        sticky=0;
        #raw_input()
        el1=[]
        el2=[]
        el3=[]
        el4=[]
        el5=[]
        el6=[]
        for line in lines:
            splitup=line.split("\t")
            average=(float(splitup[0])+float(splitup[1])+float(splitup[2])+float(splitup[3])+float(splitup[4])+float(splitup[5]))/6
            el1.append(float(splitup[0])-average)
            el2.append(float(splitup[1])-average)
            el3.append(float(splitup[2])-average)
            el4.append(float(splitup[3])-average)
            el5.append(float(splitup[4])-average)
            el6.append(float(splitup[5])-average)
        el1=lfilter(thefilter,1.0,el1).tolist()
        el2=lfilter(thefilter,1.0,el2).tolist()
        el3=lfilter(thefilter,1.0,el3).tolist()
        el4=lfilter(thefilter,1.0,el4).tolist()
        el5=lfilter(thefilter,1.0,el5).tolist()
        el6=lfilter(thefilter,1.0,el6).tolist()
        #step 3:epoch and reject bad epochs
        epochHolder=[]
        linenum=0
        numtaken=0
        while len(el1) > 0:
           # print(str(len(el1)))
            epoch=[]
            keepRunning=True
            while len(epoch) <  100 and keepRunning:
                try:
                    line=lines[numtaken]
                    if  numtaken >=260:
                        epoch.append([el1.pop(0), el2.pop(0), el3.pop(0), el4.pop(0), el5.pop(0), el6.pop(0), int(line.split("\t")[6])])
                    else:
                        foo=([el1.pop(0), el2.pop(0), el3.pop(0), el4.pop(0), el5.pop(0), el6.pop(0), int(line.split("\t")[6])])
                    numtaken=numtaken+1
                except IndexError:
                    keepRunning=False
            keepEpoch=True
            for thing in epoch:
                startType=epoch[0][6]
                if (thing[6] != startType):
                    keepEpoch=False
            if keepEpoch or True:
                    epochHolder.append(epoch)
  
        #for epoch in epochHolder[5:]:
        print("*****")
        for epochnum in range(1,len(epochHolder)):
            epoch=epochHolder[epochnum];
            #raw_input()
            lastEpoch=epochHolder[epochnum-1];
            badEpoch=False
            for electrode in [0,1,2,3,4,5]:
                thistrode=[]
                for timepoint in lastEpoch:
                    thistrode.append(timepoint[electrode])
                ave=averageArray(thistrode)
                
                newtrode=[]
                for timepoint in epoch:
                    thistrode=timepoint[electrode]
                    if abs(thistrode-ave) > thresh:
                        badEpoch=True                
            #print(str(len(epoch[1])))
            if  not badEpoch:
                    closedset.append(epoch)
        for electrode in [0,1,2,3,4,5]:
                closedout=0
                closedlog=[]
                openout=0;
                conout=0
                
                for epoch in closedset:
                    ts=[]
                    for point in epoch:
                        ts.append(point[electrode])
                    ave=averageArray(ts)
                    newts=[]
                    
                    for point in ts:
                        newts.append(point-ave)
                    ts=newts
                    if "sessions" in mode:
                        closedout=closedout+qmean(ts)
                    else:
                        closedlog.append(qmean(ts))
                if "sessions" in mode:
                    closedout=closedout/len(closedset)
                    elecOut.append(closedout)
                else:
                    elecOut.append(closedlog)
                    

    except Exception:
        eg.msgbox("Error loading data file:"+filename)
    return elecOut
    
    
lastPacket={}
runDisplayThread=True
print("Brainkit 1.0 by Nathan Whitmore")
try:
    print("Checking for critical updates...")
    versionID=urllib2.urlopen("http://montageexplorer.appspot.com/brainkitversion").read()
    splitup=versionID.split("\n")
    if float(splitup[1]) > 1.0:
        print(splitup[2])
        eg.msgbox(splitup[2])
except Exception:
    print("Could not connect to server")
while True:
    choices=["(1) Create protocol manually","(2) Create protocol from experiment","(3) Run protocol","(4) Record data","(5) Run stimulator self tests"]
    userChoice=eg.choicebox("Welcome to BrainKit. Select an option to continue",title="BrainKit 1.0",choices=choices)
    if "1" in userChoice:
        createProtocol()
    if "2" in userChoice: #create protocol from experiment
        eFileName=eg.fileopenbox(title="Select the experiment file that you want to open")
        filepath=""
        splitup=eFileName.split("\\")
        for item in range(0,len(splitup)-1):
            filepath=filepath+splitup[item]+"\\"
        os.chdir(filepath) #set working directory so that we can load the data files
        eFile=open(eFileName,'r')
        efLines=eFile.readlines()
        exType=eg.buttonbox(title="Select experiment type",msg="What type of experiment is this?",choices=["Correlation experiment","Paired test experiment"])
        if ("Correlation" in exType): # Correlating an IV with neurophys data
            header=efLines[0]
            splitHead=header.split("\t")[1:]
            iv=eg.choicebox(title="Select behavioral variable",msg="Select which column designates the behavioral or cognitive variable of interest for this experiment",choices=splitHead)
            if iv:
                dv=[]
                ivnum=-1
                for item in range(0,len(splitHead)):
                    if iv in splitHead[item]:
                        ivnum=item
##                    #dv.append(item)
##                for item in range(1,len(splitHead)):
##                    dv.append(splitHead[item])

                setup=eg.multenterbox(title="Analysis settings",msg="Choose the settings you want for this analysis.",fields=["Critical p:","Use Bonferroni correction for multiple comparisons?(y/n)","Permutations per variable","Epoch size(seconds)","Artifact rejection threshold"],values=["0.05","n","10000","10","0.5"])
                allSession=[]
                for item in efLines[1:]:
                    print("Loading session "+str(item))
                    session=[]
                    splitup=item.split("\t")
                    #get the neurophys data
                    if True:
                        physdata=getPhysData(splitup[0],float(setup[3]),float(setup[4]),("sessions"))
                        print(str(physdata))
##                        for index in range(0,len(dv)):
##                            session.append(splitup[index])
                        session.append(splitup[ivnum+1])

                             
                        for index in range(0,len(physdata)):
                            session.append(physdata[index])
                        allSession.append(session)
                    elif "epoch" in setup[5]: #Mode to come, epoch-level analysis of data
                        physdata=getPhysData(splitup[0],float(setup[3]),float(setup[4]),("sessions"))
                        for epoch in physdata:
                            session=[splitup[ivnum+1]];
                            for index in range(0,len(epoch)):
                                session.append(epoch[index])
                            allSession.append(session)
                numItems=len(allSession[0])
##                print(str(allSession))
##                print(str(numItems))
##                print(str(allSession[0]))
##                print(str(dv))
##                raw_input()
                significant=[]
                pvals=[]
                rvals=[]
                
                for item in range(1,6):
                    print("Computing variable "+str(item))
                    thisVar=[]
                    condition=[]
                    for line in allSession:
                        thisVar.append(line[item])
                        condition.append(float(line[0]))
                    slope, intercept, r_value, p_value, std_err =stats.linregress(thisVar, condition)
                    significance= permCorrelation(thisVar,condition,int(setup[2]), r_value)
                    if ("y" in setup[1]):
                        critical=float(setup[0])/numItems
                    else:
                        critical=float(setup[0])
                    if (significance <= critical):
                        significant.append(item)
                        pvals.append(significance)
                        rvals.append(r_value)
                if len(significant) > 0:
                    choices=[]
                    headers=efLines[0].split("\t")
                    for itemnum in range(0,len(significant)):
                        item=int(significant[itemnum]-1)
                      
                        dataline=(headers[ivnum+1]).upper()+"x"+electrodeNames[item].upper()+" r:"+str(rvals[itemnum])+" p:"+str(pvals[itemnum])

                        choices.append(str(itemnum+1)+"."+dataline)
                    acceptable=False
                    select=[]
                    while not acceptable:
                        sigselect=eg.multchoicebox(msg="The following significant correlations were found. Select which ones you want to use to design the protocol",title="Select significant correlations",choices=choices)
                        if sigselect:
                                    acceptable=True
                                    for thing in sigselect:
                                        index=int(thing.split(".")[0])
                                        select.append(significant[index-1])
                    createProtocol(preselected_channels=select)
                                        
                        
                else:
                    eg.msgbox("No correlations were significant at the chosen threshold")
        else: #pre=post test
            header=efLines[0]
            m1ind=-1
            m2ind=-1
            splitHead=header.split("\t")
            m1=eg.choicebox(title="Select measurement 1",msg="Select which column contains data files corresponding to measurement 1",choices=splitHead)
            if m1:
                for item in range(0,len(splitHead)):
                    if m1 in splitHead[item]:
                        m1ind=item
                m2=eg.choicebox(title="Select measurement 2",msg="Select which column contains data files corresponding to measurement 2",choices=splitHead)
                if m2:
                    for item in range(0,len(splitHead)):
                        if m2 in splitHead[item]:
                            m2ind=item
                setup=eg.multenterbox(title="Analysis settings",msg="Choose the settings you want for this analysis.",fields=["Critical p:","Use Bonferroni correction for multiple comparisons?(y/n)","Permutations per variable","Epoch size(seconds)","Artifact rejection threshold"],values=["0.05","n","10000","10","0.5"])
                
                cond1=[]
                cond2=[]
                for item in efLines[1:]:
                    print("Loading session "+str(item))
                    session1=[]
                    session2=[]
                    splitup=item.split("\t")
                    #get the neurophys data
                    if True:
                        physdata1=getPhysData(splitup[m1ind],float(setup[3]),float(setup[4]),("sessions"))
                        print(str(physdata1))
                        for index in range(0,len(physdata1)):
                            session1.append(physdata1[index])
                        cond1.append(session1)
                        physdata2=getPhysData(splitup[m2ind],float(setup[3]),float(setup[4]),("sessions"))

                        
                        for index in range(0,len(physdata2)):
                            session2.append(physdata2[index])
                        cond2.append(session2)
                         
                    elif "epoch" in setup[5]: #to come lather: epoch-level analysis
                        physdata1=getPhysData(splitup[m1ind],float(setup[3]),float(setup[4]),(setup[5]))
                        physdata2=getPhysData(splitup[m2ind],float(setup[3]),float(setup[4]),(setup[5]))
                        for item in physdata1:
                            session1=[]
                            for index in range(0,len(item)):
                                session1.append(item[index])
                            cond1.append(session1)
                        for item in physdata2:
                            session2=[]
                            for index in range(0,len(item)):
                                session2.append(item[index])
                            cond2.append(session2)
                significant=[]
                pvals=[]
                meandiff=[]
                rvals=[]

                for item in range(1,6):
                    print("Computing variable "+str(item))
                    m1=[]
                    m2=[]
                    for line in range(0,len(cond1)):
                        m1.append(cond1[line][item])
                        m2.append(cond2[line][item])
                    print(str(m1))
                    print(str(m2))
                    tval,pval=stats.ttest_rel(m1,m2)
                    significance= permttest(m1,m2,int(setup[2]), tval)
                    if ("y" in setup[1]):
                        critical=float(setup[0])/numItems
                    else:
                        critical=float(setup[0])
                    if (significance <= critical):
                        significant.append(item)
                        pvals.append(significance)
                        rvals.append(tval)
            if len(significant) > 0:
                choices=[]
                headers=efLines[0].split("\t")
                for itemnum in range(0,len(significant)):
                    item=int(significant[itemnum]-1)
                  
                    dataline=(electrodeNames[item].upper()+" t:"+str(rvals[itemnum])+" p:"+str(pvals[itemnum]))

                    choices.append(str(itemnum+1)+"."+dataline)
                acceptable=False
                select=[]
                while not acceptable:
                    sigselect=eg.multchoicebox(msg="The following significant correlations were found. Select which ones you want to use to design the protocol",title="Select significant correlations",choices=choices)
                    if sigselect:
                                acceptable=True
                                for thing in sigselect:
                                    index=int(thing.split(".")[0])
                                    select.append(significant[index-1])
                createProtocol(preselected_channels=select)
                                    
                    
            else:
                eg.msgbox("No correlations were significant at the chosen threshold")


                
                
                    
                    
                    
                                        

    if "3" in userChoice: #run protocol
         totalCurrent=0
         intensityError=False
         errors=""
         fatalError=False
         eList=""
         fileName=""
         pFileName=eg.fileopenbox(title="Select the protocol that you want to run")
         if pFileName:
             filepath=""
             splitup=pFileName.split("\\")
             for item in range(0,len(splitup)-1):
                filepath=filepath+splitup[item]+"\\"
             os.chdir(filepath) #set working directory so that we can load the data files
             pFile=open(pFileName,'r')
             fileName=splitup[len(splitup)-1]
             pData=pFile.read()
             pFile.close()
             protosplit=pData.split("****")
             protodict={}
             for line in protosplit[0].split("\n"):
                 try:
                     argpair=line.split(":")
                     protodict[argpair[0]]=argpair[1]
                 except Exception:
                    1+1
             for line in protosplit[2].split("\n"):
                 try:
                     argpair=line.replace("\n","").replace("\r","").split(":")
                     protodict[argpair[0]]=argpair[1]
                     if argpair[0] in electrodeNames:
                         totalCurrent=totalCurrent+float(argpair[1])
                         try:
                             print(str(argpair[1]))
                             if abs(float(argpair[1])) > 5:
                                 fatalError=True
                                 errors=errors+"ERROR: A single regulated electrode cannot be set to sink or source more than 5 mA\n"
                             if abs(float(argpair[1])) > 2:
                                 errors=errors+"SAFETY WARNING: Current level exceeds typical max (2 mA). Excessive current can cause skin burns and may interefere with blinding or have unanticipated effects on the brain\n"
                             if abs(float(argpair[1])) <=  0.1: 
                                 errors=errors+"WARNING: Minimum current is 0.1 mA. Electrodes with less current specified will not be activated.\n"
                             eList=eList+line+"\n"
                         except Exception:
                            fatalError=True
                            errors=errors+"ERROR: Invalid current value for "+argpair[0]+"\n"
                 except Exception:
                    1+1
             #nowscan settings for errors
             try:
                 durDecode=float(protodict.get("duration","nf"))
                 if (durDecode > 25):
                     errors=errors+"SAFETY WARNING: Duration exceeds typical max (20 minutes)\n"

             except Exception:
                 fatalError=True
                 errors=errors+"ERROR: Duration not specified\n"
             try:
                 float(protodict.get("rampdur","nf"))
             except Exception:
                 fatalError=True
                 errors=errors+"ERROR: Ramping duration not specified\n"
             try:
                 float(protodict.get("frequency","nf"))
             except Exception:
                 fatalError=True
                 errors=errors+"ERROR: Stimulation frequency not specified\n"
             try:
                 float(protodict.get("sham","nf"))
             except Exception:
                 fatalError=True
                 errors=errors+"ERROR: Sham probability not specified\n"
             if totalCurrent > 0:
                errors=errors+"WARNING:Total current is not balanced. You will need to attach an electrode to the Arduino ground to absorb "+str(totalCurrent)+" mA of excess current\n"
             if totalCurrent < 0:
                errors=errors+"WARNING:Total current is not balanced. You will need to attach an electrode to the Arduino 5 volt rail to absorb "+str(abs(totalCurrent))+" mA of excess current\n"
             errorAbort=False
             if len(errors) > 0:
                if fatalError:
                    errorAbort=True
                    eg.msgbox(title="Critical protocol errors detected",msg="This protocol cannot be used because of errors. All errors and warnings are listed below.\n"+errors)
                continueRun=eg.buttonbox(title="Protocol issues detected", msg="At least one warning or safety issue was detected in this protocol. Do you want to continue?\n All issues are listed below.\n"+errors, choices=["Yes", "No"])
                if "No" in continueRun:
                    errorAbort=True
             if not errorAbort:
                print("Load protocl")
                outcomeSummary=protosplit[1].replace("NPHYS","Neurophysiological measurements").replace("/1"," before session").replace("/2"," after session").replace("/3"," before and after session")
                summary="DURATION:"+protodict.get("duration")+" minutes\nSHAM PROBABILITY:"+protodict.get("sham")+"%\nRAMPING DURATION:"+protodict.get("rampdur")+" seconds"+"\nFREQUENCY:"+protodict.get("frequency")+"\nPOWER LEVELS:\n"+eList+"OUTCOME MEASURES:\n"+outcomeSummary+"\n\nDo you want to run this protocol?"
                runproto=eg.ynbox(title="Protocol summary",msg=summary)
                if runproto:
                    presession=[]
                    postsession=[]
                    prename=""
                    postname=""
                    hasData=False
                    preData=[]
                    postData=[]
                    if randint(0,100) <= int(protodict.get("sham")):
                        sham=True
                    else:
                        sham=False
                    for item in protosplit[1].split("\n"):
                        if "/1" in item or "/3" in item and "NPHYS" not in item:
                            presession.append(item[:item.find("/")])
                    print(protosplit[1])
                    print(str(len(presession)))
                    if len(presession) > 0:
                        hasData=True
                        presession.append("Comments")
                        preData=eg.multenterbox("This protocol requires values for the following pre-session metrics","Outcome measures",presession)
                    if "NPHYS/1" in protosplit[1] or "NPHYS/3" in protosplit[1]:
                        hasdata=True
                        eg.msgbox("This protocol calls for neurophysiological data collection. Click OK to begin data collection.")
                        connectStim()
                        prename=fileName+"-presession-"+str(randint(0,9999))
                        recordData(prename)

                if connectStim():
                    print("Programming the stimulator...")
                    headset.startStim(200) #make sure we're in stimulation mode
                    #decide whether this trial is a sham and send it
                    #if randint(0,100) <= int(protodict.get("sham")):
                    if sham:
                        headset.startStim(550)
                    #send the stimulation duration
                    headset.startStim(float(protodict.get("duration"))+600)
                    #send the ramping duration
                    headset.startStim(float(protodict.get("rampdur"))+400)
                    #If this is AC mode, send the frequency
                    if float(protodict.get("frequency","0")) >0:
                        headset.startStim(1000+float(protodict.get("frequency","0")))
                    #now go through all the electrodes nd set their values using the offset table
                    for line in eList.split("\n"):
                        if len(line) > 1:
                            splitup=line.replace("\n","").split(":")
                            #print(splitup[0])
                            #print(str(float(offsets[splitup[0]])+float(splitup[1])))
                            headset.startStim(float(offsets[splitup[0]])+float(splitup[1]))
                    #Send start command
                        headset.startStim(800)
                    print("Starting stimulation, press c to toggle current display or space to end")
                    headset.flushData()
                    keepRunning=True
                    displayCurrent=False
                    while keepRunning:
                        if msvcrt.kbhit():
                            thechar=msvcrt.getch()
                            if " " in thechar:
                                keepRunning=False
                            if "c" in thechar:
                                if displayCurrent:
                                    displayCurrent=False
                                else:
                                    displayCurrent=True
                        theCurrent=headset.getData()
                        if "SHUTDOWN" in str(theCurrent):
                            print("Stimulator initiated shutdown.")
                            keepRunning=False
                        if displayCurrent:
                            print(str(theCurrent))
                        
                    print("Stimulator ramping down...")
                    headset.startStim(900)
                    headset.closeConnection()
                    print("Connection closed")
                    eg.msgbox("Press the reset button on the stimulator, then click OK")
                    print("Waiting for the stimulator to come back online...")
                    time.sleep(10)
                    
                    postsession=[]
                    for item in protosplit[1].split("\n"):
                        if "/2" in item or "/3" in item and "NPHYS" not in item:
                            postsession.append(item[:item.find("/")])
                    print(str(postsession))
                    if len(postsession) > 0:
                        hasData=True
                        postsession.append("Comments")
                        postData=eg.multenterbox("This protocol requires values for the following post-session metrics","Outcome measures",postsession)
                    if "NPHYS/2" in protosplit[1] or "NPHYS/3" in protosplit[1]:
                        hasdata=True
                        eg.msgbox("This protocol calls for neurophysiological data collection. Click OK to begin data collection.")
                        connectStim()
                        postname=fileName+"-postsession-"+str(randint(0,9999))
                        recordData(postname)
                    #now string things together to make the log file
                    header=""
                    data=""
                    if len(prename) >0:
                        header=header+"prestim-nphys-file\t"
                        data=data+prename+"\t"
                    if len(postname) > 0:
                        header=header+"poststim-nphys-file\t"
                        data=data+postname+"\t"
                    header=header+"sham\t"
                    if sham:
                        data=data+"1\t"
                    else:
                        data=data+"0\t"
                    for index in range(0,len(presession)):
                        header=header+"presession-"+presession[index]+"\t"
                        data=data+preData[index]+"\t"
                    for index in range(0,len(postsession)):
                        header=header+"postsession-"+postsession[index]+"\t"
                        data=data+postData[index]+"\t"
                    
                    alreadyWritten=False
                    dataSoFar=""
                    try:
                        expFile=open("log-"+fileName,'r')
                        dataSoFar=expFile.read()
                        if len(dataSoFar) > 1:
                            alreadyWritten=True
                        
                        else:
                            alreadyWritten=False
                        expFile.close()
                    except Exception:
                        alreadyWritten=False
                    print(str(alreadyWritten))
                    print(str(header))
                    outFile=open("log-"+fileName,'w')
                    if not alreadyWritten:
                        outFile.write(header+"\n")
                    else:
                        outFile.write(dataSoFar)
                    outFile.write(data+"\n")
                    outFile.flush()
                    outFile.close()
                else:
                    eg.msgbox("Could not connect stimulator.")
        
        
    if "4" in userChoice:
        accepted=False
        choice=""

        while not accepted:
            thePorts=headset.getPorts()
            if len(thePorts) < 1:
                eg.msgbox(title="No devices connected",msg="No devices were detected. Make sure the BrainKit stimulator is connected and powered on and try again")
                portSelect="Cancel"
            else:
                print(str(thePorts))
                portSelect=eg.buttonbox(title="Stimulator port", msg="Select the port to which the stimulator is connected. If you do not know the port, connected or unplug the stimultor and click refresh", choices=[thePorts, "Refresh"])
            if portSelect and "Refresh" not in portSelect:
                accepted=True
                choice=portSelect
        if "Cancel" not in portSelect:
                try:
                    print(str(choice))
                    print("Attempting to connect to stimulator...")
                    headset.getConnection(choice[0][0])
                    print("Connected...")
                    savedata=eg.filesavebox(title="Select where to save the data file")
                    if savedata:
                        recordData(savedata)
                except Exception:
                    eg.msgbox("Connection error")
    if "5" in userChoice:
        testSelect=eg.buttonbox(msg="Select the test that you want to run",title="Stimulator self test",choices=["Regulator test","Short/bridge test","Cancel"])
        if testSelect and "Cancel" not in testSelect:
            if "Regulator" in testSelect:
                regFail=False
                if connectStim():
                    eg.msgbox("Connect all 6 regulated outputs to each other, then click OK to continue")
                    print("Configuring the stimulator...")
                    
                    gocommand=[6,16,26,36,46,56]
                    for command in range(0,len(gocommand)):
                        headset.startStim(2000)
                        headset.startStim(610)
                        headset.startStim(800)
                        print("Testing electrode "+electrodeNames[command])
                        headset.flushData()
                        for ncommand in [4, 14, 24, 34, 44, 54]:
                            headset.startStim(ncommand)
                        headset.startStim(gocommand[command])
                        time.sleep(5) #give it time to equilibrate
                        headset.flushData()
                        maxData=0
                        values=[]
                        for i in range(0,15):
                            theData=headset.getData()
                            #print(str(theData))
                            try:
                                if len(theData) >5:
                                    thisData=theData[command]
                                    if (thisData == 0):
                                        regFail=True
                                        print("CAUTION:The stimulator may have reset due to an electrical fault")
                                    values.append(float(thisData))
                            except Exception: #some sort of decode failure
                                1+1
                        maxData=averageArray(values)
                        if (maxData >= 0.9 and maxData < 1.1):
                            print("Forward current test passed")
                        else:
                            print("***Forward current test failed! Mean current was "+str(maxData))
                            regFail=True
                    gocommand=[4,14,24,34,44,54]
                    maxData=0;
                    values=[]
                    for command in range(0,len(gocommand)):
                        
                        headset.startStim(2000)
                        headset.startStim(610)
                        headset.startStim(800)
                        print("Testing electrode "+electrodeNames[command])
                        headset.flushData()
                        for ncommand in [6, 16, 26, 36, 46, 56]:
                            headset.startStim(ncommand)
                        headset.startStim(gocommand[command])
                        maxData=0
                        values=[]
                        time.sleep(5) #give it time to equilibrate
                        headset.flushData()
                        for i in range(0,15):
                            theData=headset.getData()
                            print(str(theData))
                            try:
                                if len(theData) > 5:
                                    thisData=theData[command]
                                    if (thisData == 0):
                                        regFail=True
                                        print("CAUTION:The stimulator may have reset due to an electrical fault")
                                    values.append(float(thisData))
                            except Exception: #some sort of decode failure
                                1+1
                        maxData=abs(averageArray(values))
                        if (maxData >= 0.9 and maxData < 1.1):
                            print("Backward current test passed")
                        else:
                            print("***Backward current test failed! Mean current was "+str(maxData))
                            regFail=True
                    headset.closeConnection()
                    if regFail:
                        eg.msgbox("The regulator failed to generate the correct current on at least one electrode. Review the log to see details")
                    else:
                        eg.msgbox("Test complete. No issues detected.")
            if "Short" in testSelect:
                eg.msgbox("Disconnect the headset from your body, then click OK to continue.",title="Short/bridge test")
                gocommand=[9,19,29,39,49,59]
                gregFail=False
                if connectStim():
                    for command in range(0,len(gocommand)):
                        headset.startStim(2000)
                        headset.startStim(610)
                        headset.startStim(800)
                        print("Testing electrode "+electrodeNames[command])
                        headset.flushData()
                        regFail=False
                        
                        for ncommand in [4, 14, 24, 34, 44, 54]:
                            headset.startStim(ncommand)
                        headset.startStim(gocommand[command])
                        time.sleep(5) #give it time to equilibrate
                        headset.flushData()
                        maxData=0
                        values=[]
                        bridged=[]
                        for i in range(0,15):
                            theData=headset.getData()
                            try:
                                if len(theData) >5:
                                    for elecNum in range(0,5):
                                        if  float(theData[elecNum]) > 0.1:
                                            regFail=True
                                            gregFail=True
                                            #print(str(float(theData[elecNum])))
                                            if electrodeNames[elecNum] not in bridged:
                                                bridged.append(electrodeNames[elecNum])                  
                            except Exception: #some sort of decode failure
                                1+1
                        if regFail:
                            print("Electrode " +electrodeNames[command] +" may be shorted to electrodes:")
                            for item in bridged:
                                print(item)
                        else:
                            print("Electrode " +electrodeNames[command]+" does not appear to be shorted")
                    headset.closeConnection()
                    if gregFail:
                        eg.msgbox("One or more electrodes may be shorted. Check the console for more details")
                    else:
                        eg.msgbox("No shorted or bridged electrodes were detected.")
                
                    
        

        
