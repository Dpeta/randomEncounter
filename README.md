# Pesterchum Random Encounters Bot
Random encounters for Pesterchum, now with asyncio :3c

The Pesterchum client can only do random encounters if this bot or an equivalent bot is present on the connected IRC server.

Run with ``python3 randomEncounter.py`` or simply ``./randomEncounter``.

Run once to generate config/token file, hostname only needs to be included when using SSL.

## Protocol
- Responds to ``NOTICE !`` and CTCP request (``PRIVMSG \x01!\x01``) with ``NOTICE !=randomUser`` and ``NOTICE \x01!=randomUser\x01`` respectively, the notice is what Pesterchum uses to do random encounters. (Pesterchum user clicked "Random )
- Responds to ``NOTICE -`` and CTCP request (``PRIVMSG \x01-\x01``) with ``NOTICE -=k`` and ``NOTICE \x01-=k\x01`` respectively, the sender is excluded from further random encounters. (User turned off random encounters.)
- Responds to ``NOTICE +`` and CTCP request (``PRIVMSG \x01+\x01``) with ``NOTICE +=k`` and ``NOTICE \x01+=k\x01`` respectively, the sender is removed from the exclude list if present. (User turned on random encounters.)
- Responds to ``NOTICE ~`` and CTCP request (``PRIVMSG \x01~\x01``) with ``NOTICE ~=k`` and ``NOTICE \x01~=k\x01`` respectively, the sender is excluded from further random encounters. (User is AFK.)
- Responds to ``NOTICE +`` and CTCP request (``PRIVMSG \x01+\x01``) with ``NOTICE +=k`` and ``NOTICE \x01+=k\x01`` respectively, the sender is removed from the idle exclude list if present. (User is no longer AFK.)
- Responds to all incoming ``PRIVMSG`` with a random user.
- Responds to ``PRIVMSG #pesterchum GETMOOD randomEncounter`` with ``PRIVMSG #pesterchum MOOD >18``.
