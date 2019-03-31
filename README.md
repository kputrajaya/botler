# Botler

[![Build](https://drone.kputrajaya.com/api/badges/kiloev/botler/status.svg)](https://drone.kputrajaya.com/kiloev/botler)

Telegram bot on AWS Lambda that connects to various APIs.

## Built With

* [Python](https://www.python.org/)
* [RoboBrowser](https://github.com/jmcarp/robobrowser)
* [Serverless](https://serverless.com/)
* [AWS Lambda](https://aws.amazon.com/lambda/)
* [Drone](https://drone.io/)

## Bot Commands

* `/bca` - Get latest [BCA](https://ibank.klikbca.com/) statements by crawling.
* `/crypto` - Get crypto prices from [Indodax](https://indodax.com/).
* `/ip` - Get server's public IP address from [Ipify](https://www.ipify.org/).
* `/mc` - Get Minecraft server status via [Minecraft Server Status](https://api.mcsrvstat.us/).
