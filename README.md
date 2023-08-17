# Xiaomi Smart WiFi Sockets and Power Strips

![GitHub actions](https://github.com/syssi/xiaomiplug/actions/workflows/ci.yaml/badge.svg)
![GitHub stars](https://img.shields.io/github/stars/syssi/xiaomiplug)
![GitHub forks](https://img.shields.io/github/forks/syssi/xiaomiplug)
![GitHub watchers](https://img.shields.io/github/watchers/syssi/xiaomiplug)
[!["Buy Me A Coffee"](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://www.buymeacoffee.com/syssi)

This is a custom component for Home Assistant to integrate the Xiaomi Smart WiFi Socket (called Plug), Xiaomi Smart Power Strip and Xiaomi Chuangmi Plug V1.

Please follow the instructions on [Retrieving the Access Token](https://www.home-assistant.io/integrations/xiaomi_miio/#xiaomi-cloud-tokens-extractor) to get the API token to use in the configuration.yaml file.

Credits: Thanks to [Rytilahti](https://github.com/rytilahti/python-miio) for all the work.

## Supported devices

| Name                        | Model                  | Model no. |
| --------------------------- | ---------------------- | --------- |
| Xiaomi Smart WiFi Socket    | chuangmi.plug.m1       | |
| Xiaomi Smart WiFi Socket    | chuangmi.plug.m3       | |
| Xiaomi Smart WiFi Socket    | chuangmi.plug.v2       | |
| Xiaomi Smart WiFi Socket    | chuangmi.plug.hmi205   | |
| Xiaomi Smart WiFi Socket    | chuangmi.plug.hmi206   | |
| Xiaomi Chuangmi Plug V1     | chuangmi.plug.v1       | |
| Xiaomi Chuangmi Plug V3     | chuangmi.plug.v3       | |
| Xiaomi Chuangmi Plug HMI208 | chuangmi.plug.hmi208   | |
| Xiaomi Smart Power Strip    | qmi.powerstrip.v1      | |
| Xiaomi Smart Power Strip    | qmi.plug.2a1c1         | |
| Xiaomi Smart Power Strip    | zimi.powerstrip.v2     | |
| Xiaomi Air Conditioning Companion V3 | lumi.acpartner.v3  | |
| Xiaomi Smart Plug TW        | qmi.plug.tw02  | |

## Features

### Xiaomi Smart WiFi Socket

Supported models: `chuangmi.plug.m1`, `chuangmi.plug.m3`, `chuangmi.plug.v2`, `chuangmi.plug.hmi205`, `chuangmi.plug.hmi206`

* Power (on, off)
* Attributes
  - Temperature

### Xiaomi Chuangmi Plug V1

Supported models: `chuangmi.plug.v1`, `chuangmi.plug.hmi208`

* Power (on, off)
* USB (on, off)
* Attributes
  - Temperature

### Xiaomi Chuangmi Plug V3

Supported models: `chuangmi.plug.v3`

* Power (on, off)
* USB (on, off)
* Wifi LED (on, off)
* Attributes
  - Temperature
  - Load power
  - Wifi LED

### Xiaomi Smart Power Strip

Supported models: `qmi.powerstrip.v1`, `zimi.powerstrip.v2`

* Power (on, off)
* Wifi LED (on, off)
* Power Price (0...999)
* Power Mode (green, normal) (Power Strip V1 only)
* Attributes
  - Temperature
  - Load power
  - Wifi LED
  - Mode (Power Strip V1 only)

### Xiaomi Air Conditioning Companion V3

Supported models: `lumi.acpartner.v3` (the socket of the acpartner.v1 and v2 isn't switchable!)

* Power (on, off)
* Attributes
  - Load power

### Xiaomi Smart Power Strip

Supported models: `qmi.plug.2a1c1`

* Power (on, off)
* Wifi LED (on, off)
* Power Mode (green, normal) (Power Strip V1 only)
* Attributes
  - Temperature
  - Load power
  - Wifi LED
  - Mode (Power Strip V1 only)

### Xiaomi Smart Plug TW

Supported models: `qmi.plug.tw02`

* Power (on, off)
* Attributes
  - Temperature
  - Load power

# Setup

Setup via HACS.

## Platform services

#### Service `xiaomi_plug.switch_set_wifi_led_on` (Power Strip and Chuangmi Plug V3)

Turn the wifi led on.

| Service data attribute    | Optional | Description                                             |
|---------------------------|----------|---------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific plug/powerstrip. Else targets all.  |

#### Service `xiaomi_plug.switch_set_wifi_led_off` (Power Strip and Chuangmi Plug V3)

Turn the wifi led off.

| Service data attribute    | Optional | Description                                             |
|---------------------------|----------|---------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific plug/powerstrip. Else targets all.  |

#### Service `xiaomi_plug.switch_set_power_price` (Power Strip only)

Set the power price.

| Service data attribute    | Optional | Description                                             |
|---------------------------|----------|---------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific plug/powerstrip. Else targets all.  |
| `price`                   |       no | Power price, between 0 and 999.                         |

#### Service `xiaomi_plug.switch_set_power_mode` (Power Strip V1 only)

Set the power mode.

| Service data attribute    | Optional | Description                                                   |
|---------------------------|----------|---------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.  |
| `mode`                    |       no | Power mode, valid values are 'normal' and 'green'             |
