# Setting up Mouser Bot

So you've decided to download and run Mouser Bot. Why thank you for taking an interest in my project!

## Packages and Configurations

In order to run Mouser Bot, you'll first need to install some requirements:

* python3.7+
* discord.py
* loguru
* discord-webhook
* requests
* linux

After packages have been installed, some configurations will need to be made.

Make a new directory in the root folder called `config`. Inside of it, make a new file called `core.json`. This will be our configuration file. If you're unfamiliar with JSON, don't worry. I've got a template you can copy+paste.

Put this inside of your `core.json` file (make sure to fill the blanks):

```json
{
	"token": "Your Discord bot token",
	"prefix": "mb ",
	"owner_id": "Your Discord account ID",
	"apikey": "Your Mouser Search API key",
```

If you want to have the Mouser Bot server email you when there's a problem, then copy+paste this code.

```json
	"email_when_error": true,
	"email_smtp_server": "Your SMTP server",
	"email_smtp_port": Your SMTP server port,
	"email_smtp_password": "Your SMTP server password",
	"email_from": "Your SMTP email",
	"email_to": "Your email that errors will go to"
}
```

If not, then skip the above portion and copy+paste the rest here.

```json
}
```

And you're done with packages and configurations! Time to run the program.

## Running the bot

There are two different programs that makes Mouser Bot run:

* The Discord bot: This interfaces with Discord and it's API and also interfaces with the database.
* The server: This interfaces with the Mouser Search API and the database.

Why two programs? Because I wrote the bot that way.

Now, in order to run the first program, run the `main.py` file or run this command:

`python3 main.py`

Now you've got the Discord bot working!

(Optional: If you want to run the bot in the background, use this command:)

`python3 main.py&`

Now, in order to run the second program, run the `start_server.py` file or run this command:

`python3 start_server.py`

Don't run the `server.py` file unless you know what you're doing.


And that's pretty much it for running the bot! Now start inviting the bot into servers and start adding parts.
