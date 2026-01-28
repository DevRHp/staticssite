#include <WiFi.h>
#include <HTTPClient.h>

// ==========================================
// 1. CONFIGURAÇÕES DE WI-FI
// ==========================================
const char* ssid = "Fretas_2GG";
const char* password = "123456789";

// ==========================================
// 2. CONFIGURAÇÕES DO SERVIDOR (WEB SERVICE)
// ==========================================
// IMPORTANTE: Troque pelo endereço DO SEU SERVIDOR (ex: https://seu-app.onrender.com)
// Se rodar localmente, use o IP do PC (ex: http://192.168.1.15:5000)
String server_url = "https://bakendgestaolim.onrender.com"; 

String nome_carrinho = "LIM01";

// ==========================================
// 3. HARDWARE
// ==========================================
const int PINO_TRAVA = 4;   // Relé / trava
const int PINO_LED   = 2;   // LED de aviso (mudança de status)

const int INTERVALO = 5000;

// ==========================================
// 4. CONTROLE DE MUDANÇA DE STATUS
// ==========================================
String ultimoStatus = "";
bool ledAtivo = false;
unsigned long tempoLed = 0;
const unsigned long DURACAO_LED = 10000; // 10 segundos

void setup() {
  Serial.begin(115200);

  pinMode(PINO_TRAVA, OUTPUT);
  pinMode(PINO_LED, OUTPUT);

  digitalWrite(PINO_TRAVA, LOW);
  digitalWrite(PINO_LED, LOW);

  // Conecta no Wi-Fi
  Serial.println();
  Serial.print("Conectando no Wi-Fi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {

  // ===============================
  // DESLIGA LED APÓS 10 SEGUNDOS
  // ===============================
  if (ledAtivo && millis() - tempoLed >= DURACAO_LED) {
    digitalWrite(PINO_LED, LOW);
    ledAtivo = false;
    Serial.println("💡 LED de aviso desligado");
  }

  if (WiFi.status() == WL_CONNECTED) {

    HTTPClient http;

    // Nova URL para o seu Backend Flask
    // Ex: https://meu-app.com/api/esp32/get_status?nome=LIM01
    String full_url = server_url + "/api/esp32/get_status?nome=" + nome_carrinho;

    // Se for HTTPS no Render, o ESP32 pode precisar do certificado ou usar setInsecure() se a lib suportar
    // Para HTTP simples (local), begin(full_url) basta.
    // Para simplificar, assumimos que o HTTPClient lida com redirects se necessário
    http.begin(full_url); 
    
    // O Render as vezes pede User-Agent
    http.addHeader("User-Agent", "ESP32");

    int httpCode = http.GET();

    if (httpCode > 0) {

      String payload = http.getString();

      Serial.print("URL: ");
      Serial.println(full_url);
      Serial.print("Status Code: ");
      Serial.println(httpCode);
      Serial.print("Resposta: ");
      Serial.println(payload);

      String statusAtual = "";

      // ===============================
      // LÓGICA ATUALIZADA (FLASK)
      // ===============================
      // O servidor retorna "STATUS:EM_USO" ou "STATUS:DISPONIVEL"
      
      if (payload.indexOf("STATUS:EM_USO") != -1) {
        Serial.println(">> AÇÃO: DESTRAVAR (EM USO)");
        digitalWrite(PINO_TRAVA, HIGH);
        statusAtual = "EM_USO";
      }
      else if (payload.indexOf("STATUS:DISPONIVEL") != -1) {
        Serial.println(">> AÇÃO: TRAVAR (DISPONIVEL)");
        digitalWrite(PINO_TRAVA, LOW);
        statusAtual = "DISPONIVEL";
      }
      else {
        Serial.println(">> ALERTA: Resposta desconhecida ou Erro");
        // Mantém estado anterior por segurança ou trava?
        // digitalWrite(PINO_TRAVA, LOW); 
      }

      // ===============================
      // DETECTA MUDANÇA DE STATUS
      // ===============================
      if (statusAtual != "" && statusAtual != ultimoStatus) {

        Serial.println("🔔 STATUS ALTERADO!");
        Serial.print("De: ");
        Serial.print(ultimoStatus);
        Serial.print(" → Para: ");
        Serial.println(statusAtual);

        // Acende LED de aviso por 10s
        digitalWrite(PINO_LED, HIGH);
        tempoLed = millis();
        ledAtivo = true;

        ultimoStatus = statusAtual;
      }

    } else {
      Serial.print("Erro HTTP: ");
      Serial.println(httpCode);
    }

    http.end();
  } else {
    Serial.println("Wi-Fi desconectado");
  }

  delay(INTERVALO);
}
