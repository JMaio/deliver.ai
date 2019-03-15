<h1 align="center">deliver.ai</h1>

<p align="center">System Design Project 2018/19 - Group 19</p>
<p align="center">
  <img src="https://circleci.com/gh/JMaio/deliver.ai.svg?style=svg&circle-token=011ef6be1434239ca561203d45e70003fb37f596">
</p>

# Setup

## EV3 Usage 

We first initialise a `Map` which always has a `HOME` at (0,0). We then initialise and `Office` giving it a name and coordinates (e.g. `o = Office("barbara", (1,1))`).
We can then add (and afterwards delete) an office from our map. A robot is initialised with a map and a starting position (e.g. `bot = DeliverAIBot(my_map, my_map.home)`) after which it can be called to any other office on the map using the `goTo` function.

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

