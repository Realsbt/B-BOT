#ifndef WIFI_CMD_H
#define WIFI_CMD_H

#include <Arduino.h>

void WiFiCmd_Init(void);
void WiFiCmd_SetInputEnabled(bool enabled);
bool WiFiCmd_GetInputEnabled(void);

#endif
