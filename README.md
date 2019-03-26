# Botler

[![Build](https://drone.kputrajaya.com/api/badges/kiloev/botler/status.svg)](https://drone.kputrajaya.com/kiloev/botler)

Telegram bot on AWS Lambda that connects to various APIs.

## Built with

* [Serverless](https://serverless.com/)
* [Serverless Python Requirements](https://github.com/UnitedIncome/serverless-python-requirements)
* [RoboBrowser](https://github.com/jmcarp/robobrowser)
* [AWS Lambda](https://aws.amazon.com/lambda/)
* [Python 3.7](https://www.python.org/)
* [Drone](https://drone.io/)

## Bot commands

* `/bca` - Get latest [BCA](https://ibank.klikbca.com/) statements by crawling.
* `/crypto` - Get crypto prices from [Indodax](https://indodax.com/).
* `/ip` - Get server's public IP address from [Ipify](https://www.ipify.org/).
* `/mc` - Get Minecraft server status via [Minecraft Server Status](https://api.mcsrvstat.us/).
