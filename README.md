# Botler

[![Build Status](http://drone.kputrajaya.com/api/badges/kiloev/botler/status.svg)](http://drone.kputrajaya.com/kiloev/botler)

Telegram bot on AWS Lambda that connects to APIs.

Due to its simplicity, can be used as base for making other serverless Telegram bots.

## Bot commands

* `/bca` - Get latest [BCA](https://ibank.klikbca.com/) statements by crawling.
* `/crypto` - Get crypto prices from [Indodax](https://indodax.com/).
* `/ip` - Get server's public IP address from [Ipify](https://www.ipify.org/).
* `/mc` - Get Minecraft server status via [Minecraft Server Status](https://api.mcsrvstat.us/).

## Built with

* [Serverless](https://serverless.com/)
* [Serverless Python Requirements](https://github.com/UnitedIncome/serverless-python-requirements)
* [RoboBrowser](https://github.com/jmcarp/robobrowser)
* [AWS Lambda](https://aws.amazon.com/lambda/)
* [Python 3.7](https://www.python.org/)
* [Drone](https://drone.io/)

## Related tutorials

* [Serverless Telegram bot on AWS Lambda](https://hackernoon.com/serverless-telegram-bot-on-aws-lambda-851204d4236c)
* [Serverless Python Packaging](https://serverless.com/blog/serverless-python-packaging/)
