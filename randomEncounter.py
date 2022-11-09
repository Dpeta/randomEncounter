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
CLIENTINFO = "CLIENTINFO ! - + * ~ VERSION SOURCE PING CLIENTINFO"
PREFIXES = ["~", "&", "@", "%", "+"]  # channel membership prefixes

if not os.path.isdir("errorlogs"):
    os.makedirs("errorlogs")


class RandomEncounterBot:
    """Class for an instance of the 'randomEncounter' bot"""

    def __init__(self):
        self.end = False
        self.reader = None
        self.writer = None
        self.userlist = []
        self.userlist_exclude = []
        self.userlist_idle = []
        self.userlist_encounterable = []
        self.updating_userlist = False
        self.userlist_date = 0

    async def send(self, text, *params):
        """Works with command as str or as multiple seperate params"""
        for param in params:
            text += " " + param
        print("Send: " + text)
        await self.writer.drain()
        self.writer.write((text + "\n").encode())

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

    async def welcome(self):
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
        await self.send("METADATA * set color 255,0,0")  # Red

    async def safe_respond(self, data):
        """Alternative way to call respond(), catches and logs exception."""
        try:
            await self.respond(data)
        except Exception as respond_except:
            print("Error,", respond_except)
            # Try to write to logfile
            try:
                local_time = time.localtime()
                local_time_str = time.strftime("%Y-%m-%d %H-%M", local_time)
                with open(
                    os.path.join("errorlogs", f"RE_errorlog {local_time_str}.log"),
                    "a",
                    encoding="utf-8",
                ) as file:
                    traceback.print_tb(respond_except.__traceback__, file=file)
                    file.close()
            except Exception as write_except:
                print("Failed to write errorlog,", write_except)

    async def respond(self, data):
        """Responses for server reply code / commands."""
        text = data.decode()
        if text.startswith("PING"):
            self.writer.write(text.replace("PING", "PONG").encode())
            return
        if text.startswith(":") & (len(text.split(" ")) > 2):
            prefix = text[1:].split(" ")[0]
            command = text.split(" ")[1]
            parameters = text.split(" ")[2:15]
            print(prefix, command, parameters)
            # RPL_WELCOME, run actions on welcome
            if command == "001":
                await self.welcome()
            # RPL_ENDOFWHO, WHO finished
            elif command == "315":
                self.updating_userlist = False
            # RPL_WHOREPLY, add WHO reply to userlist
            elif command == "352":
                # channel, user, host, server, nick = parameters[1:6]
                nick = parameters[5]
                self.userlist.append(nick)
            # RPL_NAMREPLY, add NAMES reply to userlist
            elif command == "353":
                names_str = text.split(":")[2]  # List of names start
                # after second delimiter
                names_list = names_str.split(" ")  # 0x20 is the seperator
                # between nicks
                # Add to userlist
                for name in names_list:
                    # Strip channel operator symbols
                    if (name[0] == "@") or (name[0] == "+"):
                        self.userlist.append(name[1:])
                    else:
                        self.userlist.append(name)
            # RPL_ENDOFNAMES, NAMES finished
            elif command == "366":
                self.updating_userlist = False
            # PRIVMSG, reply with random handle unless quit
            elif command == "PRIVMSG":
                receiver = parameters[0]
                nick = prefix[: prefix.find("!")]
                msg = text[
                    text.find(parameters[1][1:]) :
                ]  # All remaining parameters as str
                # Delimiter ':' is stripped
                # We can give mood :3
                if receiver == "#pesterchum":
                    if msg.startswith("GETMOOD") & ("randomEncounter" in msg):
                        await self.send("PRIVMSG #pesterchum MOOD >18")
                # If it's not addressed to us it's irrelevant
                if receiver != "randomEncounter":
                    return
                # Don't wanna lock people into dialogue :"3
                if msg.startswith("PESTERCHUM") or msg.startswith("COLOR"):
                    return
                await self.userlist_update()

                # Handle possible commands
                # Any PRIVMSG
                await self.userlist_update()
                outnick = random.choice(self.userlist_encounterable)
                for char in PREFIXES:
                    if outnick[0] == char:
                        outnick = outnick[1:]
                await self.send("PRIVMSG", nick, outnick)

            # NOTICE
            elif command == "NOTICE":
                receiver = parameters[0]
                if receiver != "randomEncounter":
                    return
                nick = prefix[: prefix.find("!")]
                msg = text[
                    text.find(parameters[1][1:]) :
                ]  # All remaining parameters as str
                # Delimiter ':' is stripped
                # Return random user
                if msg.startswith("!"):
                    await self.userlist_update()
                    outnick = random.choice(self.userlist_encounterable)
                    for char in PREFIXES:
                        if outnick[0] == char:
                            outnick = outnick[1:]
                    await self.send("NOTICE", nick, "!=" + outnick)
                # Enable random encounters
                elif msg.startswith("+"):
                    await self.send("NOTICE", nick, "+=k")
                    if nick in self.userlist_exclude:
                        self.userlist_exclude.remove(nick)
                        await self.userlist_update()
                # Disable random encounters
                elif msg.startswith("-"):
                    await self.send("NOTICE", nick, "-=k")
                    if nick not in self.userlist_exclude:
                        self.userlist_exclude.append(nick)
                        await self.userlist_update()
                # Become idle
                elif msg.startswith("~"):
                    await self.send("NOTICE", nick, "~=k")
                    if nick not in self.userlist_idle:
                        self.userlist_idle.append(nick)
                        await self.userlist_update()
                # Stop being idle
                elif msg.startswith("*"):
                    await self.send("NOTICE", nick, "*=k")
                    if nick in self.userlist_idle:
                        self.userlist_idle.remove(nick)
                        await self.userlist_update()
                # ???
                elif msg.startswith("?"):
                    await self.send("NOTICE", nick, "?=y")

    async def userlist_update(self):
        """Updates userlist by requesting #pesterchum userlist"""
        # Only update userlist if old
        if time.time() - self.userlist_date > 14.13:
            print("updating userlist. . .")
            self.updating_userlist = True
            self.userlist_date = time.time()
            self.userlist = []
            await self.send("NAMES #pesterchum")
            # Wait for update to finish
        # Block until finished
        while self.updating_userlist:
            await asyncio.sleep(0.413)
        # Encouterable users
        self.userlist_encounterable = self.userlist.copy()
        # Exclude users with RE turned off
        for dont_encounter in self.userlist_exclude:
            if dont_encounter in self.userlist_encounterable:
                self.userlist_encounterable.remove(dont_encounter)
        # Exclude idle users
        for idle_user in self.userlist_idle:
            if idle_user in self.userlist_encounterable:
                self.userlist_encounterable.remove(idle_user)
        print(f"USERS TOTAL: {len(self.userlist)}")
        print(f"USERS VIABLE: {len(self.userlist_encounterable)}")

    async def main(self):
        """Main function/loop, creates a new task when the server sends data."""
        while not self.end:
            # Try to connect
            try:
                await self.connect()
            except Exception as connection_exception:
                print("Failed to connect,", connection_exception)
            # Sub event loop while connected
            if self.writer and self.reader:  # Not none
                while not self.writer.is_closing() and not self.reader.at_eof():
                    try:
                        data = await self.reader.readline()
                        if data is not None:
                            asyncio.create_task(self.safe_respond(data))
                    except Exception:
                        try:
                            await self.send("QUIT goo by cwuel wowl,,")
                        except Exception as quit_exception:
                            print("Failed to send QUIT,", quit_exception)
                        self.writer.close()
            if not self.end:
                print("4.13 seconds until reconnect. . .")
                await asyncio.sleep(4.13)


if __name__ == "__main__":
    bot = RandomEncounterBot()
    asyncio.run(bot.main())
    print("Exiting. . .")
