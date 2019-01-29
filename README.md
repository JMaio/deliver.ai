# deliver.ai
System Design Project 2018/19 - Group 19

# Setup
## Raspberry Pi
Our Pi is `abomasnow` and can be accessed from within the Informatics network via  
```
ssh student@abomasnow -XC
```
From SDP Wiki: the password is `password`  
(`-XC` allows for X forwarding over SSH, basically it shows windows from the Pi on your own machine)

~`jigglypuff` doesn't seem to like something about the setup, and has mostly been unreachable when testing.~
> It looks as though one of our micro-usb cables is faulty! I'll try to verify and get it replaced soon.  
> Joao 22/01/19

`jigglypuff` can only be _reliably_ powered by a 5V 2A+ source, otherwise it will fail to start up. Successful boot is indicated by the red LED and the green LED blinking at some point. If only the red LED shows, it may have failed to start.

`jigglypuff` was failing to boot so it's been exchanged for `abomasnow`

