#! /usr/bin/env python3
# randomEnounter bot for Pesterchum using asyncio
import asyncio
import random
import time
import configparser
import os

class randomEncounterBot():
    def __init__(self):
        self.reader = None
        self.writer = None
        self.userlist = []
        self.userlistExclude = []
        self.userlistIdle = []
        self.userlistEncounterable = []
        self.updatingUserlist = False
        self.userlistDate = 0

    async def send(self, text, *params):
        # Works with command as str or as multiple seperate params
        for x in params:
            text += ' ' + x 
        print("Send: " + text)
        await self.writer.drain()
        self.writer.write(
            (text + '\n').encode()
            )
        
    async def getConfig(self):
        config = configparser.ConfigParser()
        if os.path.exists('config.ini'):
            config.read('config.ini')
        else:
            config['server'] = {'server': '127.0.0.1',
                                'hostname': 'irc.pesterchum.xyz',
                                'port': '6667',
                                'ssl': 'False'}
            config['tokens'] = {'nickserv_username': '',
                                'nickserv_password': '',
                                'vhost_login': '',
                                'vhost_password': ''}
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            print("Wrote default config file.")
        return config
 
    async def connect(self):
        config = await self.getConfig()
        if config['server'].getboolean('ssl') == True:
            self.reader, self.writer = await asyncio.open_connection(
                config['server']['server'],
                config['server'].getint('port'),
                ssl=config['server'].getboolean('ssl'),
                server_hostname=config['server']['hostname'])
        elif config['server'].getboolean('ssl') == False:
            self.reader, self.writer = await asyncio.open_connection(
                config['server']['server'],
                config['server'].getint('port'),
                ssl=config['server'].getboolean('ssl'))
        await self.send("NICK randomEncounter")
        await self.send("USER RE 0 * :PCRC")

    async def welcome(self):
        config = await self.getConfig()
        await self.send("MODE randomEncounter +B")
        await self.send("JOIN #pesterchum")
        await self.send("VHOST",
                        config['tokens']['vhost_login'],
                        config['tokens']['vhost_password'])
        await self.send("PRIVMSG nickserv identify",
                        config['tokens']['nickserv_username'],
                        config['tokens']['nickserv_password'])

    async def respond(self, data):
        text = data.decode()
        if text.startswith("PING"):
            self.writer.write(
                text.replace("PING", "PONG").encode()
                )
            return
        if text.startswith(':') & (len(text.split(' ')) > 2):
            prefix = text[1:].split(' ')[0]
            command = text.split(' ')[1]
            parameters = text.split(' ')[2:15]
            print(prefix, command, parameters)
            # RPL_WELCOME, run actions on welcome
            if command == "001":
                await self.welcome()
            # RPL_ENDOFWHO, WHO finished
            elif command == "315":
                self.updatingUserlist = False
            # RPL_WHOREPLY, add WHO reply to userlist
            elif command == "352":
                channel, user, host, server, nick = parameters[1:6]
                self.userlist.append(nick)
            # RPL_NAMREPLY, add NAMES reply to userlist
            elif command == "353":
                names_str = text.split(':')[2]    # List of names start after second delimiter
                names_list = names_str.split(' ') # 0x20 is the seperator between nicks
                # Add to userlist
                for x in names_list:
                    # Strip channel operator symbols
                    if (x[0] == '@') or (x[0] == '+'):
                        self.userlist.append(x[1:])
                    else:
                        self.userlist.append(x)
            # RPL_ENDOFNAMES, NAMES finished
            elif command == "366":
                self.updatingUserlist = False
            # PRIVMSG, always respond with random handle
            elif command == "PRIVMSG":
                receiver = parameters[0]
                nick = prefix[:prefix.find('!')]
                msg = text[text.find(parameters[1][1:]):] # All remaining parameters as str
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
                await self.userlistUpdate()
                if msg.startswith('\x01') == False:
                    # Normal PRIVMSG
                    await self.send("PRIVMSG", nick, random.choice(self.userlistEncounterable))
                elif msg.startswith('\x01'):
                    # CTCP
                    msg = msg.strip('\x01') # Strip so we can reuse notice code
                    # Return random user
                    if msg.startswith("!"):
                        await self.userlistUpdate()
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "!=" + random.choice(self.userlistEncounterable) + '\x01')
                    # Enable random encounters
                    elif msg.startswith("+"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "+=k" + '\x01')
                        if nick in self.userlistExclude:
                            self.userlistExclude.remove(nick)
                            await self.userlistUpdate()
                    # Disable random encounters
                    elif msg.startswith("-"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "-=k" + '\x01')
                        if nick not in self.userlistExclude:
                            self.userlistExclude.append(nick)
                            await self.userlistUpdate()
                    # Become idle
                    elif msg.startswith("~"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "~=k" + '\x01')
                        if nick not in self.userlistIdle:
                            self.userlistIdle.append(nick)
                            await self.userlistUpdate()
                    # Stop being idle
                    elif msg.startswith("*"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "*=k" + '\x01')
                        if nick in self.userlistIdle:
                            self.userlistIdle.remove(nick)
                            await self.userlistUpdate()
                    # ???
                    elif msg.startswith("?"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "?=y" + '\x01')
                    # The normal ones. . .
                    elif msg.startswith("VERSION"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "VERSION randomEncounter" + '\x01')
                    elif msg.startswith("SOURCE"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "SOURCE https://github.com/Dpeta/randomEncounter" + '\x01')
                    elif msg.startswith("PING"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + msg + '\x01')
                    elif msg.startswith("CLIENTINFO"):
                        await self.send("NOTICE",
                                        nick,
                                        '\x01' + "CLIENTINFO ! - + * ~ VERSION SOURCE PING CLIENTINFO" + '\x01')
                        
            # NOTICE
            elif command == "NOTICE":
                receiver = parameters[0]
                if receiver != "randomEncounter":
                    return
                nick = prefix[:prefix.find('!')]
                msg = text[text.find(parameters[1][1:]):] # All remaining parameters as str
                                                          # Delimiter ':' is stripped
                # Return random user
                if msg.startswith("!"):
                    await self.userlistUpdate()
                    await self.send("NOTICE",
                                    nick,
                                    "!=" + random.choice(self.userlistEncounterable))
                # Enable random encounters
                elif msg.startswith("+"):
                    await self.send("NOTICE",
                                    nick,
                                    "+=k")
                    if nick in self.userlistExclude:
                        self.userlistExclude.remove(nick)
                        await self.userlistUpdate()
                # Disable random encounters
                elif msg.startswith("-"):
                    await self.send("NOTICE",
                                    nick,
                                    "-=k")
                    if nick not in self.userlistExclude:
                        self.userlistExclude.append(nick)
                        await self.userlistUpdate()
                # Become idle
                elif msg.startswith("~"):
                    await self.send("NOTICE",
                                    nick,
                                    "~=k")
                    if nick not in self.userlistIdle:
                        self.userlistIdle.append(nick)
                        await self.userlistUpdate()
                # Stop being idle
                elif msg.startswith("*"):
                    await self.send("NOTICE",
                                    nick,
                                    "*=k")
                    if nick in self.userlistIdle:
                        self.userlistIdle.remove(nick)
                        await self.userlistUpdate()
                # ???
                elif msg.startswith("?"):
                    await self.send("NOTICE",
                                    nick,
                                    "?=y")
                    
    async def userlistUpdate(self):
        # Only update userlist if old
        if time.time() - self.userlistDate > 14.13:
            print("updating userlist. . .")
            self.updatingUserlist = True
            self.userlistDate = time.time()
            self.userlist = []
            await self.send("NAMES #pesterchum")
            # Wait for update to finish
        # Block until finished
        while self.updatingUserlist == True:
            await asyncio.sleep(0.413)
        # Encouterable users
        self.userlistEncounterable = self.userlist.copy()
        # Exclude users with RE turned off
        for x in self.userlistExclude:
            if x in self.userlistEncounterable:
                self.userlistEncounterable.remove(x)
        # Exclude idle users
        for x in self.userlistIdle:
            if x in self.userlistEncounterable:
                self.userlistEncounterable.remove(x)
            
    async def main(self):
        while True:
            await asyncio.create_task(self.connect())
            while self.writer.is_closing() == False:
                try:
                    data = await self.reader.readline()
                    if data != None:
                        asyncio.create_task(self.respond(data))
                except:
                    try:
                        await self.send("QUIT goo by cwuel wowl,,")
                    except:
                        pass
                    self.writer.close()
            print("4.13 seconds until reconnect. . .")
            await asyncio.sleep(4.13)

if __name__ == "__main__":
    bot = randomEncounterBot()
    asyncio.run(bot.main())
    print("Exiting. . .")
