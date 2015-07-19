#include <SPI.h>
#include "TimerOne.h"
#include <avr/wdt.h>
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

//output 1--8 and 9--A8 and A9
//output 2--4 and 6--A6 and A7
//output 3--10 and 12--A10 and A11
//output 4--A4 and A5
//output 5--A3 and A2
//output 6--A1 nd A0

//top leftt--output 6

//bottom left--output 5

//top right--output 4

//middle top right--output 3

//midlle bottom right --otuput 2
boolean resetReady=false;
boolean allowOvercurrent=false;
//bottom right--output 1
boolean rampingDisable=false;
float rampTime=10;
float P_FACTOR=5;
long SHAM_LENGTH=20000;
long lastRamp=0L;
long totaldur=0L;
float ramprate=0.1;
boolean stimMode=true;
boolean sham=false;
boolean enableRamping=false;
const int slaveSelectPin = 2;
void digitalPotWrite(int address, int value) {
  // take the SS pin low to select the chip:
  digitalWrite(slaveSelectPin,LOW);
  //  send in the address and value via SPI:
  SPI.transfer(address);
  SPI.transfer(value);
  // take the SS pin high to de-select the chip:
  digitalWrite(slaveSelectPin,HIGH);
}

#include <SPI.h>


// set pin 10 as the slave select for the digital pot:
boolean tacs=false;
boolean normalPhase=true;
float tacsFreq=1;
long tacsTimer=0;
int SAMPLES=100;
String serBuffer="";
int highSide[] = {
 A1, A3,A5,A7,A9,A11};
int lowSide[]={
 A0,A2,A4,A6,A8,A10 };
float power[]={
  0,0,0,0,0,0};
float realpower[]={
  0,0,0,0,0,0};
volatile float rset[]={
  127,127,127,127,127,127};
long startTime=0L;
float powReport[]={
  0,0,0,0,0,0};
  float rampingrates[]={
  0,0,0,0,0,0};
   boolean ramptarget[]={false,false,false,false,false,false};
void setup() {

  // set prescale to 16
  sbi(ADCSRA,ADPS2) ;
  cbi(ADCSRA,ADPS1) ;
  cbi(ADCSRA,ADPS0) ;
  pinMode (slaveSelectPin, OUTPUT);
  Serial.begin(115200);
  SPI.begin();
  for (int i=0; i< 6;i++) {
    pinMode(highSide[i],INPUT);
    pinMode(lowSide[i],INPUT);
  }

Timer1.initialize(50000*2);
wdt_enable(WDTO_2S);
}

void loop() {
  wdt_reset(); //reset the watchdog timer--if this crashes the device will auto-reset
  if (Serial.available() >0) {
    float command=Serial.parseFloat();
    Serial.println(command);
    if (command < 10) {
      power[0]=command-5;
    }
    if (command >= 10 && command < 20) {
      power[1]=command-15;
    }
    if (command >= 20 && command < 30) {
      power[2]=command-25;
    }
    if (command >= 30 && command < 40) {
      power[3]=command-35;
    }
    if (command >= 40 && command < 50) {
      power[4]=command-45;
    }
    if (command >= 50 && command < 60) {
      power[5]=command-55;
    }

    if (command > 199 && command < 201) {
      stimMode=true;
      allowOvercurrent=false;
    }
    if (command > 299 && command < 301) {
      stimMode=false;
    }
    if (command > 400 && command < 500) {
      rampTime=(command-400);
    }
    //sham stuff
    if (command > 500 && command < 600) {
      sham=true;
    }
    if (command > 600 && command < 700) {
      totaldur=((command-600)*60)*1000;
    }
    if (command > 799 && command < 801) {
      enableRamping=true;
      for (int i=0; i< 6; i++) {
        rampingrates[i]=(abs(power[i])/rampTime)/4;
      }
      startTime=millis();
      Timer1.attachInterrupt(timerIsr);
    }
    
     if (command > 899 && command < 901) {
       Serial.println(command); 
      for (int i=0; i< 6;i++) {
          power[i]=0;
          Serial.println(command);  //make sure computer acknowledges command
        }
        resetReady=true;
    }
    if (command > 1000 && command < 2000) { //tacs frequency set
    tacs=true;
    tacsFreq=(1000/(command-1000))/2;
    }
    if (command >1999 && command < 2001) { //ramping disable
    rampingDisable=true;
    allowOvercurrent=true;
    }

  }

    //        digitalPotWrite((byte)0,rset[0]);
    //        delay(10);
    //        digitalPotWrite((byte)1,rset[1]);
    //        delay(10);
    //         digitalPotWrite((byte)2,rset[2]);
    //        delay(10);
    //         digitalPotWrite((byte)3,rset[3]);
    //        delay(10);
    //         digitalPotWrite((byte)4,rset[4]);
    //        delay(10);
    //         digitalPotWrite((byte)5,rset[5]);
    //        delay(10);
    //         digitalPotWrite((byte)0,rset[0]);
    //        delay(10);
    //Serial.print(analogRead(highSide[0])-analogRead(lowSide[0]));
    if (resetReady) {//system powering down
    boolean doReset=true;
    for (int i=0; i< 6;i++) {
      if (abs(realpower[i]) > 0.1) {
        doReset=false;
      }
      else {
        pinMode(highSide[i],INPUT);
         pinMode(lowSide[i],INPUT);
      }
    }
      if (doReset) {
        Serial.end();
        asm volatile ("  jmp 0");  
      }
      }
    if (enableRamping) {
      if (millis()-startTime > totaldur||(sham && millis()-startTime > SHAM_LENGTH)) {
        for (int i=0; i< 6;i++) {
          power[i]=0;
        }
        if (millis()-startTime > totaldur) {
          for (int i=0; i< 6;i++) {
          Serial.println("SHUTDOWN");
          }
        }
      }
      if (millis() - lastRamp >=250) {
        for (int i=0; i< 6;i++) {
          
          Serial.print(powReport[i],DEC);

          Serial.print(",");
          ramprate=rampingrates[i];
          
          if (abs(power[i]-realpower[i])>0.005) {
          if ((realpower[i]) < (power[i])) {
            if (realpower[i] < power[i])
            realpower[i]=realpower[i]+ramprate;
          }
          else  if (realpower[i] > power[i]) {
            realpower[i]=realpower[i]-ramprate;
          }
          if (realpower[i] > 5) {
            realpower[i]=5;
          }
          if (realpower[i] < -5) {
            realpower[i]=-5;
          }
        }
        if (rampingDisable) {
        realpower[i]=power[i];
        }
        }
        Serial.println("");
        lastRamp=millis();
      }
    }
    if (stimMode) {
     // timerIsr();
    }
    else {
      Timer1.detachInterrupt();
      scanMode();
    }
  
}

void timerIsr() {
  if (normalPhase) { //set up unregulated connections
    pinMode(3,OUTPUT);
    digitalWrite(3,LOW); //3 is the cathode
    pinMode(13,OUTPUT);
    digitalWrite(13,HIGH); //13 is the anode
  }
  else {
    pinMode(3,OUTPUT);
    digitalWrite(3,HIGH); //3 is the anode
    pinMode(13,OUTPUT);
    digitalWrite(13,LOW); //13 is the cathode
  }
  float rdata[]={
    0,0,0,0,0,0  };
    if (tacs) {
      if (millis() > tacsTimer+tacsFreq) {
        normalPhase=!normalPhase;
        tacsTimer=millis();
      }
    }
  for (int x=0; x< SAMPLES; x++) {
    for (int i=5; i>=0;i--) {
      if ((normalPhase && realpower[i] > 0.1) || (!normalPhase && realpower[i] < -0.1)) {
        pinMode(lowSide[i],OUTPUT);
        pinMode(highSide[i],INPUT);
        digitalWrite(lowSide[i],HIGH);
        rdata[i]=rdata[i]+(analogRead(lowSide[i])-analogRead(highSide[i]));

      }
      else if ((normalPhase && realpower[i] < -0.1) || (!normalPhase && realpower[i] > 0.1)) {
        pinMode(lowSide[i],OUTPUT);
        pinMode(highSide[i],INPUT);
        digitalWrite(lowSide[i],LOW);
        rdata[i]=rdata[i]+(analogRead(highSide[i])-analogRead(lowSide[i]));

      }
      else {
        pinMode(highSide[i],INPUT);
        pinMode(lowSide[i],INPUT);
        rdata[i]=0;
      }

    }

  }
  for (int electrode=5; electrode >= 0;electrode--) {
    float voltage=((rdata[electrode]/(float)SAMPLES)/(float)1024)*5;
    float ma=(voltage/(float)100)*(float)1000;
    float diff=abs(abs(ma) - abs(realpower[electrode]));
    powReport[electrode]=ma;
    if (ma < 0.1 && abs(realpower[electrode] > 0.25 && !tacs && !allowOvercurrent) ) { //no connection, don't do anything {
      
    }
    else if (ma >  abs(realpower[electrode])+1 && !tacs && !allowOvercurrent) { //emergency shutdown
    rset[electrode]=0;
    }
    else {
  //  Serial.print(realpower[electrode],DEC);
 //   Serial.print(",");
   // Serial.print(totaldur);

    if (abs(ma) > abs(realpower[electrode])) {
      rset[electrode]=rset[electrode]-5;
      //rset[electrode]=rset[electrode]-3;
    }
    if (abs(ma) < abs(realpower[electrode])) {
      rset[electrode]=rset[electrode]+5;
      //rset[electrode]=rset[electrode]+3;
    }
    if (rset[electrode] < 0) {
      rset[electrode]=0;
    }
    if (rset[electrode] > 255) {
      rset[electrode]=255;
    }
  }
  }
  // Serial.println("");
  for (int setting=0;setting < 6;setting++) {
    // Serial.print(rset[setting-1]);
    //Serial.print(",");

   // digitalPotWrite((byte)setting,byte(round(rset[5])));
   digitalPotWrite((byte)setting,rset[setting]);
    //delay(10);
  }
}

void scanMode() {

  for (int port=0; port< 6; port++) {
    digitalPotWrite((byte)port+1,255);
    // pinMode(2,INPUT);
    float accumulated=0;
    int reading1=0;
    int reading2=0;
    pinMode(highSide[port],OUTPUT);

    for (int i=1; i<200; i++) {
      pinMode(highSide[port],OUTPUT);
      digitalWrite(highSide[port],LOW);
      accumulated=accumulated+(abs(reading2-reading1));
      //delay(1);
      reading1=analogRead(highSide[port]);
      pinMode(highSide[port],INPUT_PULLUP);
      //pinMode(receivePorts[port],INPUT_PULLUP);
      // delay(1);
      reading2=analogRead(highSide[port]);
      accumulated=accumulated+(abs(reading2-reading1));



    }
    pinMode(highSide[port],INPUT);
    pinMode(lowSide[port],INPUT);
    accumulated=accumulated/400;
    Serial.print(accumulated);
    Serial.print(",");

  }
  Serial.println("");

}

