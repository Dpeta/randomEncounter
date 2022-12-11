#! /usr/bin/env python3
"""randomEnounter bot for Pesterchum using asyncio.
Retrieves random users for clients and keeps track of
which clients have random enounters disabled."""
import os
import time
import random
import asyncio
import traceback
import configparser

SOURCE = "https://github.com/Dpeta/randomEncounter"
VERSION = "randomEncounter"
CLIENTINFO = "VERSION SOURCE PING CLIENTINFO"
PREFIXES = ["~", "&", "@", "%", "+"]  # channel membership prefixes
ACCEPTABLE_EXCEPTIONS = (OSError, TimeoutError, EOFError, asyncio.LimitOverrunError)

if not os.path.isdir("errorlogs"):
    os.makedirs("errorlogs")


class Users:
    """Class to keep track of users and their states"""

    def __init__(self):
        self.userlist = []
        self.exclude = []  # Users with RE turned off
        self.idle = []  # Idle users

    async def add(self, *users):
        """Adds users if they joined or someone changed their nick to a new handle"""
        for user in users:
            if user[0] in PREFIXES:
                user = user[1:]
            if user not in self.userlist:
                self.userlist.append(user)
        print(f"self.userlist: {self.userlist}")

    async def remove(self, *users):
        """Adds users if they quit/parted or someone changed their nick to a new handle"""
        for user in users:
            if user[0] in PREFIXES:
                user = user[1:]
            if user in self.userlist:
                self.userlist.remove(user)
        print(f"self.userlist: {self.userlist}")

    async def set_idle(self, user, idle):
        """Set if a user is or is not idle,
        params are user (str) and idle state (bool)"""
        if idle:
            if user not in self.idle:
                # Add idle user
                self.idle.append(user)
        else:
            if user in self.idle:
                # Remove idle user
                self.idle.remove(user)
        print(f"self.idle: {self.idle}")

    async def set_random_encounter(self, user, encounter):
        """Set if a user has random encounters enabled,
        params are user (str) and encounter state (bool)"""
        if encounter:
            if user in self.exclude:
                # Remove user from exclude list
                self.exclude.remove(user)
        else:
            if user not in self.exclude:
                # Add user to exclude list
                self.exclude.append(user)
        print(f"self.exclude: {self.exclude}")

    async def get_random(self):
        """Return a random user from the userlist,
        exclude idlers and users with RE disabled."""
        # Encouterable users
        encounter = self.userlist.copy()
        dont_encounter = self.exclude + self.idle
        # Exclude idle users and users with RE turned off
        for user in dont_encounter:
            if user in encounter:
                encounter.remove(user)
        print(f"dont_encounter: {dont_encounter}")
        print(f"encounter: {encounter}")
        if encounter:
            return random.choice(encounter)
        return "mistakeswereMade"

    async def sanity_check(self):
        """Make sure that users not in the userlist aren't
        still listed in the idle/exclude lists."""
        try:
            for user in self.exclude.copy():
                if user not in self.userlist:
                    self.exclude.remove(user)
            for user in self.idle.copy():
                if user not in self.userlist:
                    self.idle.remove(user)
        except ValueError as oh_no:
            print(oh_no)


class RandomEncounterBot:
    """Class for an instance of the 'randomEncounter' bot"""

    def __init__(self):
        self.end = False
        self.reader = None
        self.writer = None
        self.users = Users()

    async def send(self, text, *params):
        """Works with command as str or as multiple seperate params"""
        for param in params:
            text += " " + param
        print("Send: " + text)
        await self.writer.drain()
        self.writer.write((text + "\r\n").encode())

    async def get_config(self):
        """Gets bot configuration from 'config.ini'"""
        config = configparser.ConfigParser()
        if os.path.exists("config.ini"):
            config.read("config.ini")
        else:
            config["server"] = {
                "server": "127.0.0.1",
                "hostname": "irc.pesterchum.xyz",
                "port": "6667",
                "ssl": "False",
            }
            config["tokens"] = {
                "nickserv_username": "",
                "nickserv_password": "",
                "vhost_login": "",
                "vhost_password": "",
            }
            with open("config.ini", "w", encoding="utf-8") as configfile:
                config.write(configfile)
            print("Wrote default config file.")
        return config

    async def connect(self):
        """Connect to the server."""
        config = await self.get_config()
        if config["server"].getboolean("ssl"):
            self.reader, self.writer = await asyncio.open_connection(
                config["server"]["server"],
                config["server"].getint("port"),
                ssl=config["server"].getboolean("ssl"),
                server_hostname=config["server"]["hostname"],
            )
        else:
            self.reader, self.writer = await asyncio.open_connection(
                config["server"]["server"],
                config["server"].getint("port"),
                ssl=config["server"].getboolean("ssl"),
            )
        await self.send("NICK randomEncounter")
        await self.send("USER RE 0 * :PCRC")

    async def welcome(self, _):
        """Actions to take when the server has send a welcome/001 reply,
        meaning the client is connected and nick/user registration is completed."""
        config = await self.get_config()
        await self.send("MODE randomEncounter +B")
        await self.send("JOIN #pesterchum")
        await self.send(
            "VHOST", config["tokens"]["vhost_login"], config["tokens"]["vhost_password"]
        )
        await self.send(
            "PRIVMSG nickserv identify",
            config["tokens"]["nickserv_username"],
            config["tokens"]["nickserv_password"],
        )
        # Set mood/color
        await self.send("METADATA * set mood 18")  #  'PROTECTIVE' mood
        await self.send("METADATA * set color #ff0000")  # Red

    async def nam_reply(self, text):
        """RPL_NAMREPLY, add NAMES reply to userlist"""
        # List of names start
        names_str = text.split(":")[2]
        # after second delimiter
        names_list = names_str.split(" ")  # 0x20 is the seperator
        # Add to userlist
        for name in names_list:
            # Strip channel operator symbols
            if name[0] in PREFIXES:
                await self.users.add(name[1:])
            else:
                await self.users.add(name)

    async def privmsg(self, text):
        """Handles incoming PRIVMSG"""
        parameters = text.split(" ")[2:15]
        receiver = parameters[0]
        prefix = text[1:].split(" ")[0]
        nick = prefix[: prefix.find("!")]

        # All remaining parameters as str, the delimiter ':' is stripped.
        msg = text[text.find(parameters[1][1:]) :]

        # We can give mood :3
        if receiver == "#pesterchum":
            if "randomEncounter" in msg and msg.startswith("GETMOOD"):
                await self.send("PRIVMSG #pesterchum MOOD >18")

        # Return if not addressed to us or if it's just Pesterchum syntax weirdness.
        if (
            receiver != "randomEncounter"
            or msg.startswith("PESTERCHUM")
            or msg.startswith("COLOR")
        ):
            return

        if msg[0] != "\x01":
            # Reply with a random user
            outnick = await self.users.get_random()
            await self.send("PRIVMSG", nick, outnick)
        else:
            # CTCP
            msg = msg.strip("\x01")
            match msg:
                case "VERSION":
                    await self.send(f"NOTICE {nick} \x01VERSION {VERSION}\x01")
                case "SOURCE":
                    await self.send(f"NOTICE {nick} \x01SOURCE {SOURCE}\x01")
                case "PING":
                    await self.send(f"NOTICE {nick} \x01{msg}\x01")
                case "CLIENTINFO":
                    await self.send(f"NOTICE {nick} \x01CLIENTINFO {CLIENTINFO}\x01")

    async def notice(self, text):
        """Handles incoming NOTICE"""
        parameters = text.split(" ")[2:15]
        receiver = parameters[0]
        prefix = text[1:].split(" ")[0]
        nick = prefix[: prefix.find("!")]

        if receiver != "randomEncounter":
            return

        # All remaining parameters as str, the delimiter ':' is stripped.
        msg = text[text.find(parameters[1][1:]) :]

        match msg[0]:
            # Return random user
            case "!":
                outnick = await self.users.get_random()
                await self.send("NOTICE", nick, "!=" + outnick)
            # Enable random encounters
            case "+":
                await self.send("NOTICE", nick, "+=k")
                await self.users.set_random_encounter(nick, True)
            # Disable random encounters
            case "-":
                await self.send("NOTICE", nick, "-=k")
                await self.users.set_random_encounter(nick, False)
            # Become idle
            case "~":
                await self.send("NOTICE", nick, "~=k")
                await self.users.set_idle(nick, True)
            # Stop being idle
            case "*":
                await self.send("NOTICE", nick, "*=k")
                await self.users.set_idle(nick, False)
            # ???
            case "?":
                await self.send("NOTICE", nick, "?=y")

    async def ping(self, text):
        """Handle incoming pings"""
        await self.send("PONG" + text[4:])

    async def nick(self, text):
        """Handle users changing their nicks,
        nick got changed from old_nick to new_nick"""
        prefix = text[1:].split(" ")[0]
        old_nick = prefix[: prefix.find("!")]
        parameters = text.split(" ")[2:15]
        new_nick = parameters[0]
        if new_nick[0] == ":":
            new_nick = new_nick[1:]

        await self.users.set_idle(prefix, False)
        await self.users.set_random_encounter(prefix, False)
        await self.users.remove(old_nick)
        await self.users.add(new_nick)

    async def quit(self, text):
        """Handle other user's QUITs"""
        prefix = text[1:].split(" ")[0]
        nick = prefix[: prefix.find("!")]
        await self.users.remove(nick)

    async def part(self, text):
        """Handle other user's PARTs"""
        prefix = text[1:].split(" ")[0]
        nick = prefix[: prefix.find("!")]
        await self.users.remove(nick)

    async def join(self, text):
        """Handle other user's JOINs"""
        prefix = text[1:].split(" ")[0]
        nick = prefix[: prefix.find("!")]
        if nick[0] == ":":
            nick = nick[1:]
        await self.users.add(nick)

    async def get_names(self):
        """Routinely retrieve the userlist from scratch."""
        while True:
            await asyncio.sleep(1200)  # 20min
            print("Routine NAMES reset.")
            self.users.userlist = []
            try:
                await self.send("NAMES #pesterchum")
            except AttributeError as fail_names:
                print(f"Failed to send NAMES, disconnected? {fail_names}")

            # Run sanity check with a delay
            await asyncio.sleep(600)  # 10min
            self.users.sanity_check()

    async def decode_data(self, data):
        """Returns decoded string, returns one space if it fails."""
        try:
            return data.decode()
        except ValueError:
            return " "

    async def get_command(self, text):
        """Return IRC command from line of text, returns empty string if it fails."""
        text_split = text.split(" ")
        length = len(text_split)
        if text.startswith(":") and length >= 1:
            return text_split[1].upper()
        if length >= 0:
            return text_split[0].upper()
        return ""

    async def main(self):
        """Main function/loop, creates a new task when the server sends data."""
        command_handlers = {
            "001": self.welcome,
            "353": self.nam_reply,
            # "366": self.end_of_names,
            "PING": self.ping,
            "PRIVMSG": self.privmsg,
            "NOTICE": self.notice,
            "NICK": self.nick,
            "QUIT": self.quit,
            "PART": self.part,
            "JOIN": self.join,
        }
        # Create task for routinely updating names from scratch
        asyncio.create_task(self.get_names())

        # Repeats on disconnect
        while not self.end:
            # Try to connect
            try:
                await self.connect()
            except ACCEPTABLE_EXCEPTIONS as connection_exception:
                print("Failed to connect,", connection_exception)

            # Sub event loop while connected
            if self.writer and self.reader:  # Not none
                while not self.writer.is_closing() and not self.reader.at_eof():
                    try:
                        data = await self.reader.readline()
                        if data:
                            text = await self.decode_data(data)
                            command = await self.get_command(text)
                            # Pass task to the command's associated function if it exists.
                            if command in command_handlers:
                                asyncio.create_task(
                                    command_handlers[command](text.strip())
                                )
                    except ACCEPTABLE_EXCEPTIONS as core_exception:
                        print("Error,", core_exception)
                        # Write to logfile
                        local_time = time.localtime()
                        local_time_str = time.strftime("%Y-%m-%d %H-%M", local_time)
                        with open(
                            f"errorlogs/RE_errorlog {local_time_str}.log",
                            "a",
                            encoding="utf-8",
                        ) as file:
                            traceback.print_tb(core_exception.__traceback__, file=file)
                        self.writer.close()
                    except KeyboardInterrupt:
                        await self.send("QUIT goo by cwuel wowl,,")
                        self.end = True
            if not self.end:
                print("4.13 seconds until reconnect. . .")
                await asyncio.sleep(4.13)


if __name__ == "__main__":
    bot = RandomEncounterBot()
    asyncio.run(bot.main())
    print("Exiting. . .")
