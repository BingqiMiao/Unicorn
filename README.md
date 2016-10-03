Unicorn
===========

### HardWare

`Computer` is Raspberry pi3 B

`GPS` is NEO-M8N

`Compass` is [msensor-HCM365](http://www.msensor.com.cn/52/i-2104.html)

`MCU` is STM32

`FC` is Pixhawk and ACE-ONE

`Vehicle` is HEX4,HEX6,Copter-450L,Copter-550,Copter-25B


### Installation

```bash
sudo pip install apscheduler,threadpool,pynmea2
```	

### Configuration

```gcc
./ultra_simple
```
Generate pipe -> Replay and Request


### Example

configure  *.xml

```python
sudo python config.py

sudo python MCU_module.py

sudo python compass_module.py

sudo python GPS_module.py

sudo python vehicle.py

sudo python lidar_module.py

sudo python sudo python cloud_module.py
```

Run
```python
sudo python main.py
