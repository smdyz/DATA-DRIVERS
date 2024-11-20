#include <SPI.h>
#include <nRF24L01.h>
#include <RF24.h>

#define CE_PIN   9
#define CSN_PIN 10

const byte thisSlaveAddress[5] = {'R','x','A','A','A'};
RF24 radio(CE_PIN, CSN_PIN);

char packet[32 + 1] = "";       // Буфер для отдельного пакета
char completeMessage[450] = ""; // Буфер для полного сообщения
bool newData = false;

void setup() {
  Serial.begin(9600);
  radio.begin();
  radio.setDataRate(RF24_250KBPS);
  radio.openReadingPipe(1, thisSlaveAddress);
  radio.startListening();
  Serial.print("Hello, I am receiver");
}

void loop() {
  getData();
  
  // Печать полного сообщения, когда оно полностью получено
  if (newData) {
    Serial.print("Complete message received: ");
    Serial.println(completeMessage);
    newData = false;

    // Очистка буфера для следующего сообщения
    memset(completeMessage, 0, sizeof(completeMessage));
  }
}

void getData() {
  // Проверка наличия данных для чтения
  if (radio.available()) {
    radio.read(&packet, sizeof(packet) - 1); // Чтение пакета
    packet[32] = '\0';  // Завершаем строку

    Serial.print("Packet received: ");
    Serial.println(packet);

    // Добавляем пакет к полному сообщению
    strcat(completeMessage, packet);

    // Проверка на завершение сообщения (если в конце присутствует '}')
    if (strchr(packet, '}') != nullptr) {
      newData = true;
      Serial.println(completeMessage);
    }
  }
}
