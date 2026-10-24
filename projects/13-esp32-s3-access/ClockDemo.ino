#include <Arduino.h>
#include <WiFi.h>
#include <esp_heap_caps.h>
#include <sys/time.h>
#include <time.h>

#include "Display_SPD2010.h"
#include "I2C_Driver.h"
#include "TCA9554PWR.h"
#include "wifi_secrets.h"

namespace {

constexpr uint16_t kWidth = 412;
constexpr uint16_t kHeight = 412;
constexpr uint16_t kBlack = 0x0000;
constexpr uint16_t kWhite = 0xFFFF;
constexpr uint16_t kCyan = 0x07FF;
constexpr uint8_t kThickness = 9;
constexpr uint16_t kDigitWidth = 62;
constexpr uint16_t kDigitHeight = 132;

uint16_t* framebuffer;
int lastDrawnSecond = -1;

void fillRect(uint16_t x, uint16_t y, uint16_t width, uint16_t height, uint16_t color)
{
  const uint16_t right = x + width < kWidth ? x + width : kWidth;
  const uint16_t bottom = y + height < kHeight ? y + height : kHeight;
  for (uint16_t row = y; row < bottom; ++row) {
    for (uint16_t column = x; column < right; ++column) {
      framebuffer[row * kWidth + column] = color;
    }
  }
}

void drawDigit(uint8_t digit, uint16_t x, uint16_t y, uint16_t color)
{
  static const uint8_t segments[] = {
    0x3F, 0x06, 0x5B, 0x4F, 0x66,
    0x6D, 0x7D, 0x07, 0x7F, 0x6F
  };
  const uint8_t mask = segments[digit];
  const uint16_t middle = y + kDigitHeight / 2;
  const uint16_t halfSegment = kDigitHeight / 2 - kThickness;

  if (mask & 0x01) fillRect(x + kThickness, y, kDigitWidth - 2 * kThickness, kThickness, color);
  if (mask & 0x02) fillRect(x + kDigitWidth - kThickness, y + kThickness, kThickness, halfSegment, color);
  if (mask & 0x04) fillRect(x + kDigitWidth - kThickness, middle, kThickness, halfSegment, color);
  if (mask & 0x08) fillRect(x + kThickness, y + kDigitHeight - kThickness, kDigitWidth - 2 * kThickness, kThickness, color);
  if (mask & 0x10) fillRect(x, middle, kThickness, halfSegment, color);
  if (mask & 0x20) fillRect(x, y + kThickness, kThickness, halfSegment, color);
  if (mask & 0x40) fillRect(x + kThickness, middle - kThickness / 2, kDigitWidth - 2 * kThickness, kThickness, color);
}

void drawClock(const tm& localTime)
{
  for (uint32_t i = 0; i < kWidth * kHeight; ++i) {
    framebuffer[i] = kBlack;
  }

  const uint16_t gap = 12;
  const uint16_t colonWidth = 16;
  const uint16_t clockWidth = 4 * kDigitWidth + 2 * gap + colonWidth;
  const uint16_t left = (kWidth - clockWidth) / 2;
  const uint16_t top = (kHeight - kDigitHeight) / 2;
  const uint16_t hour = localTime.tm_hour;
  const uint16_t minute = localTime.tm_min;

  drawDigit(hour / 10, left, top, kWhite);
  drawDigit(hour % 10, left + kDigitWidth + gap, top, kWhite);

  const uint16_t colonX = left + 2 * kDigitWidth + gap + (colonWidth - kThickness) / 2;
  fillRect(colonX, top + 40, kThickness, kThickness, kCyan);
  fillRect(colonX, top + 84, kThickness, kThickness, kCyan);

  const uint16_t minuteX = left + 2 * kDigitWidth + 2 * gap + colonWidth;
  drawDigit(minute / 10, minuteX, top, kWhite);
  drawDigit(minute % 10, minuteX + kDigitWidth + gap, top, kWhite);

  LCD_addWindow(0, 0, kWidth - 1, kHeight - 1, framebuffer);
  for (uint32_t i = 0; i < kWidth * kHeight; ++i) {
    framebuffer[i] = (framebuffer[i] << 8) | (framebuffer[i] >> 8);
  }
}

uint8_t monthNumber(const char* month)
{
  static const char* months[] = {
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
  };
  for (uint8_t i = 0; i < 12; ++i) {
    if (strncmp(month, months[i], 3) == 0) return i;
  }
  return 0;
}

void setBuildTime()
{
  char month[4] = {};
  int day = 0;
  int year = 0;
  int hour = 0;
  int minute = 0;
  int second = 0;
  sscanf(__DATE__, "%3s %d %d", month, &day, &year);
  sscanf(__TIME__, "%d:%d:%d", &hour, &minute, &second);

  tm buildTime = {};
  buildTime.tm_year = year - 1900;
  buildTime.tm_mon = monthNumber(month);
  buildTime.tm_mday = day;
  buildTime.tm_hour = hour;
  buildTime.tm_min = minute;
  buildTime.tm_sec = second;
  buildTime.tm_isdst = -1;

  timeval value = {};
  value.tv_sec = mktime(&buildTime);
  settimeofday(&value, nullptr);
}

void connectAndSyncTime()
{
  if (strlen(WIFI_SSID) == 0) {
    Serial.println("Wi-Fi not configured; clock is using the firmware build time.");
    return;
  }

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  const uint32_t connectStarted = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - connectStarted < 20000) {
    delay(250);
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi connection failed; clock is using the firmware build time.");
    return;
  }

  configTzTime(CLOCK_TIMEZONE, "pool.ntp.org", "time.google.com");
  const uint32_t syncStarted = millis();
  while (time(nullptr) < 1700000000 && millis() - syncStarted < 20000) {
    delay(250);
  }

  Serial.println(time(nullptr) >= 1700000000 ? "Clock synchronised with NTP." : "NTP time sync failed.");
}

}  // namespace

void setup()
{
  Serial.begin(115200);
  setenv("TZ", CLOCK_TIMEZONE, 1);
  tzset();
  setBuildTime();

  I2C_Init();
  TCA9554PWR_Init(0x00);
  Backlight_Init();
  LCD_Init();

  framebuffer = static_cast<uint16_t*>(
    heap_caps_malloc(kWidth * kHeight * sizeof(uint16_t), MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (framebuffer == nullptr) {
    Serial.println("Could not allocate the display framebuffer in PSRAM.");
    while (true) delay(1000);
  }

  tm localTime = {};
  time_t now = time(nullptr);
  localtime_r(&now, &localTime);
  drawClock(localTime);
  connectAndSyncTime();
}

void loop()
{
  tm localTime = {};
  time_t now = time(nullptr);
  localtime_r(&now, &localTime);

  if (localTime.tm_sec != lastDrawnSecond) {
    lastDrawnSecond = localTime.tm_sec;
    drawClock(localTime);
  }
  delay(10);
}
