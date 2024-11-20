#include <AltSoftSerial.h>
#include <SoftwareSerial.h>
#include <TinyGPS++.h>
#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>
#define CE_PIN  6
#define CSN_PIN 10
static const uint32_t GPSBaud = 9600;
SoftwareSerial BT(2, 3); // Bluetooth RX, TX
TinyGPSPlus gps;
AltSoftSerial ss;  // GPS на RX=8, TX=9
String data = "nothing";
bool f = false;
String latitude = "";
String longitude = "";
const byte slaveAddress[5] = {'R','x','A','A','A'};
RF24 radio(CE_PIN, CSN_PIN);
char dataToSend[450] = "";
char txNum = '0';
unsigned long currentMillis;
unsigned long prevMillis;
unsigned long txIntervalMillis = 500;
void setup() {
  // начальная настройка
  Serial.begin(9600);       
  BT.begin(9600);
  ss.begin(GPSBaud);
  Serial.println("Hello");
  BT.println("hello");
  radio.begin();
  radio.setDataRate( RF24_2MBPS );
  radio.setRetries(3,5);
  radio.openWritingPipe(slaveAddress);
}
void loop() {
  while (ss.available() > 0) {
    gps.encode(ss.read());
  }
  if (gps.location.isValid()) {
    latitude = String(gps.location.lat(), 6);
    longitude = String(gps.location.lng(), 6);
  } else {
    latitude = "N/A";
    longitude = "N/A";
  }
  if (Serial.available()) {
    char CH = Serial.read();
    Serial.println(CH);
    BT.println(CH);
  }
  if (BT.available()) {
    char CH1 = BT.read();
    Serial.print("From Bluetooth: ");
    Serial.println(CH1);
    if (CH1 == '{') {
      f = true;
      data = "{";
    }
    else if (CH1 == '}') {
      f = false;
      data += ", Coordinates: (" + latitude + "," + longitude + ")}";
      Serial.println(data);
    }
    else if (f) {
      data += CH1;
    }
  }
  data.toCharArray(dataToSend, sizeof(dataToSend));
  currentMillis = millis();
  if(not(f)){
    if (currentMillis - prevMillis >= txIntervalMillis) {
        send();
        prevMillis = millis();
        Serial.print("\n");
      }
  }
}
void send() {
    Serial.print("Data Sent: ");
    int maxPacketSize = 32;
    int messageLength = strlen(dataToSend);
    for (int i = 0; i < messageLength; i += maxPacketSize) {
        char packet[33] = "";
        packet[-1] = '\0';
        for (int g = i; g < i + 32; g++) {
            packet[g - i] =  dataToSend[g];
        }
        bool rslt = radio.write(&packet, sizeof(packet));
        int n = 0;
        while (rslt != true){
          rslt = radio.write(&packet, sizeof(packet));
          if (n > 50){break;}
          n++;
        }
        Serial.print(packet);
        if (rslt) {
            Serial.println(" Acknowledge received");
        } else {
            Serial.println(" Tx failed");
        }
    }
}
