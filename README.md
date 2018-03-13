# homeassistant-thermopi
Home Assistant component for ThermoPi

ThermoPi required using new api code (not yet published) -  See https://github.com/groupwhere/thermopi
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

Once again, the code for the required API has not yet been published.

More to come...

