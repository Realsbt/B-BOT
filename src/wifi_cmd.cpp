#include "wifi_cmd.h"

#ifdef ENABLE_WIFI_CMD

#include <WiFi.h>
#include <ESPmDNS.h>
#include "serial.h"
#include "wifi_config.h"

#ifndef WIFI_MDNS_HOST
#define WIFI_MDNS_HOST "wheeleg"
#endif

#define WIFI_CONNECT_TIMEOUT_MS 15000
#define WIFI_RECONNECT_INTERVAL_MS 5000
// TCP-level watchdog: if no line received within WIFI_WATCHDOG_MS,
// the PC script is considered dead — force close + full stop.
// DRIVE-level watchdog (500ms) runs separately inside serial.cpp.

static WiFiServer sServer(WIFI_TCP_PORT);
static WiFiClient sClient;
static volatile bool sWifiInputEnabled = true;
static uint32_t sLastTcpLineMs = 0;
static bool sHadTcpClient = false;
static bool sServerStarted = false;

static void fullStopOnDisconnect(const char *reason) {
    // DRIVE bypasses the queue, so QUEUE_STOP alone cannot stop a moving robot.
    // Zero both the direct teleop channel (DRIVE) and YAWRATE, then stop the queue.
    Serial.printf("WiFi command disconnect (%s): emitting full stop\n", reason);
    Serial_InjectCommandLine("DRIVE,0,0");
    Serial_InjectCommandLine("YAWRATE,0");
    Serial_InjectCommandLine("QUEUE_STOP");
}

static bool tryConnectWiFi(void) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.printf("WiFi command connecting to %s", WIFI_SSID);
    uint32_t start = millis();
    while (WiFi.status() != WL_CONNECTED) {
        if (millis() - start > WIFI_CONNECT_TIMEOUT_MS) {
            Serial.println("\nWiFi command connect timeout, will retry later");
            return false;
        }
        vTaskDelay(pdMS_TO_TICKS(500));
        Serial.print(".");
    }
    Serial.printf("\nWiFi command ready: %s:%d\n",
                  WiFi.localIP().toString().c_str(),
                  WIFI_TCP_PORT);
    if (MDNS.begin(WIFI_MDNS_HOST)) {
        MDNS.addService("wheeleg", "tcp", WIFI_TCP_PORT);
        Serial.printf("mDNS: %s.local:%d\n", WIFI_MDNS_HOST, WIFI_TCP_PORT);
    } else {
        Serial.println("mDNS start failed");
    }
    return true;
}

static void handleLine(char *line) {
    if (!sWifiInputEnabled) {
        Serial.println("WiFi command ignored: input disabled");
        return;
    }

    sLastTcpLineMs = millis();
    Serial.printf("WiFi命令: %s\n", line);
    Serial_InjectCommandLine(line);
}

static void WiFiCmdTask(void *arg) {
    char rxBuffer[256] = {0};
    size_t bufIndex = 0;
    uint32_t lastConnectAttempt = 0;

    while (1) {
        // --- WiFi link state ---
        if (WiFi.status() != WL_CONNECTED) {
            if (sServerStarted) {
                // lost WiFi while serving: stop the robot defensively
                if (sHadTcpClient) {
                    fullStopOnDisconnect("wifi_lost");
                    sHadTcpClient = false;
                    sLastTcpLineMs = 0;
                }
                sServer.stop();
                sServerStarted = false;
                MDNS.end();
            }
            if (millis() - lastConnectAttempt >= WIFI_RECONNECT_INTERVAL_MS ||
                lastConnectAttempt == 0) {
                lastConnectAttempt = millis();
                tryConnectWiFi();
            } else {
                vTaskDelay(pdMS_TO_TICKS(200));
            }
            continue;
        }

        if (!sServerStarted) {
            sServer.begin();
            sServer.setNoDelay(true);
            sServerStarted = true;
            Serial.printf("WiFi TCP server listening on :%d\n", WIFI_TCP_PORT);
        }

        // --- client accept / drop ---
        if (!sClient || !sClient.connected()) {
            if (sHadTcpClient) {
                fullStopOnDisconnect("client_drop");
            }
            if (sClient) {
                sClient.stop();
            }
            sHadTcpClient = false;
            sLastTcpLineMs = 0;
            sClient = sServer.available();
            if (sClient) {
                sClient.setNoDelay(true);
                sClient.setTimeout(1);
                sHadTcpClient = true;
                sLastTcpLineMs = millis();
                bufIndex = 0;
                rxBuffer[0] = '\0';
                Serial.printf("WiFi command client connected: %s\n",
                              sClient.remoteIP().toString().c_str());
            }
        }

        // --- read lines ---
        while (sClient && sClient.connected() && sClient.available() > 0) {
            char c = (char)sClient.read();
            if (c == '\n' || bufIndex >= sizeof(rxBuffer) - 1) {
                rxBuffer[bufIndex] = '\0';
                if (bufIndex > 0 && rxBuffer[bufIndex - 1] == '\r') {
                    rxBuffer[bufIndex - 1] = '\0';
                }
                bufIndex = 0;
                handleLine(rxBuffer);
            } else {
                rxBuffer[bufIndex++] = c;
            }
        }

        // --- TCP-level idle watchdog: force close a stale client ---
        if (sHadTcpClient && sLastTcpLineMs != 0 &&
            millis() - sLastTcpLineMs > WIFI_WATCHDOG_MS) {
            Serial.println("WiFi command client idle: force close");
            fullStopOnDisconnect("idle_timeout");
            sClient.stop();
            sHadTcpClient = false;
            sLastTcpLineMs = 0;
        }

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

void WiFiCmd_Init(void) {
    xTaskCreatePinnedToCore(WiFiCmdTask, "WiFiCmdTask", 4096, NULL, 1, NULL, 1);
}

void WiFiCmd_SetInputEnabled(bool enabled) {
    sWifiInputEnabled = enabled;
    Serial.printf("WiFi command input %s\n", enabled ? "enabled" : "disabled");
}

bool WiFiCmd_GetInputEnabled(void) {
    return sWifiInputEnabled;
}

#else

void WiFiCmd_Init(void) {}
void WiFiCmd_SetInputEnabled(bool enabled) { (void)enabled; }
bool WiFiCmd_GetInputEnabled(void) { return false; }

#endif
