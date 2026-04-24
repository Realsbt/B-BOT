#ifndef WIFI_CONFIG_H
#define WIFI_CONFIG_H

#if __has_include("wifi_config.local.h")
#include "wifi_config.local.h"
#endif

#ifndef WIFI_SSID
#define WIFI_SSID "CHANGE_ME"
#endif

#ifndef WIFI_PASS
#define WIFI_PASS "CHANGE_ME"
#endif

#ifndef WIFI_TCP_PORT
#define WIFI_TCP_PORT 23
#endif

#ifndef WIFI_WATCHDOG_MS
#define WIFI_WATCHDOG_MS 1500
#endif

#endif
