# homeassistant-thermopi
Home Assistant component for ThermoPi

ThermoPi required using new api code -  See https://github.com/groupwhere/thermopi
Copy into your CONFIG_DIR/custom_components/climate/ directory.  You may need to create this dir.

Minimum config:
```
climate:
  - platform: thermopi
    name: Thermopi
    host: 192.168.0.33

```
Optional:
```
    port: 88
```

What works:
```
1. Display in web interface of target temp and operation mode.
```
More to come...

