# OpenQABot
This repository contains a minimal example how the REST API of OpenQA(http://openqa.aksw.org/) can be used as a telegram bot using the telegram-bot wrapper(https://github.com/python-telegram-bot/python-telegram-bot)

# Dependencies
Use `pip` to install the dependencies:

`sudo pip install SPARQLWrapper requests python-telegram-bot emoji --upgrade`

# Try it
If you have a telegram account you can just chat with the bot at (https://telegram.me/OpenQABot)

# Examples
You have to write `/start` to start the conversation with the bot and then you can try to ask questions like:

`Give me the capital of Germany`

`List the children of Margaret Thatcher`

# Usage
If you want to make your own bot, you need to register a bot and get an API Token from (https://telegram.me/botfather) if you did not already do this.

Run the `openQABot.py` file and provide the API Token as argument:

`python openQABot.py <TOKEN>`

# Known Issues
The queries can sometimes take a while
