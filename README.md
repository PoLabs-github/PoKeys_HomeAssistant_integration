# PoKeys_HomeAssistant_plugin

A HomeAssistant plugin for the PoKeys57E Ethernet I/O controller that contains all of the basic features required for most home automation projects. For detailed setup and use descriprion check out our blog site at https://blog.poscope.com

# Setup
## Hacs setup
- Go to Hacs>Integrations>Custom repositories
- Paste the link ```https://github.com/domen-jersek/PoKeys_HomeAssistant_plugin``` and select ```Integration```
- Restart HomeAssistant
- Go to Hacs>Integrations>Explore & download repositories, search for "pokeys" and click Download
## Manual setup
- Copy the custom_components folder into your HA config folder
- Restart HomeAssistant
- After restart you can now add your pokeys device to the file configuration.yaml
- An example of the pokeys configuration inside configuration.yaml:

```
#pokeys configuration example
pokeys:
  sensors_interval: 6 #[optional]how often sensors will update(in seconds)(default is 5)
  binary_sensors_interval: 2 #[optional]how often binary_sensors will update(in seconds)(default is 1)
  devices:
    - name: "PoKeys57E device 1"
      serial: 31557 #the serial number of your pokeys device
      buttons:
        - name: "pokeys_button_1" #the name of your button entity
          pin: 13 #the pin that will be efected
          delay: 4 #describes how long(seconds) the button will be turned on after press is called
        - name: "pokeys button 2"
          pin: 12
          delay: 2

      binary_sensors:
        - name: "pokeys binary sensor"
          pin: 8

    - name: "PoKeys57E device 2"
      serial: 31708
      sensors:
        - name: "pokeys easysensor temperature"
          id: 0 #sensor id/index

      switches:
        - name: "pokeys switch"
          pin: 12
        - name: "PoRelay"
          poextbus: 2.3 #the first digit is the device id the second digit is the relay on that device(device2 relay3)

#supported entities: switch, sensor(for pokeys EasySensor), binary_sensor
```

- After adding the pokeys configuration for your home automation project restart HomeAssistant and the entities you inputed will be added to HomeAssistant
