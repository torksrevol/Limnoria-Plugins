# -*- coding: utf-8 -*-
###
# Copyright (c) 2011, Anthony Boot
# Copyright (C) 2015, wolfy1339
# All rights reserved.
#
# Licenced under GPLv2
# In brief, you may edit and distribute this as you want, provided the original
# and modified sources are always available, this license notice is retained
# and the original author is given full credit.
#
# There is no warrenty or guarentee, even if explicitly stated, that this
# script is bug and malware free. It is your responsibility to check this
# script and ensure its safety.
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircdb as ircdb

import re
import time
import json
import random
import socket
import supybot.ircmsgs as ircmsgs
import supybot.schedule as schedule


class General(callbacks.PluginRegexp):

    """Some general purpose plugins."""

    threaded = True

# Remove from this array to disable any regexps

    regexps = ["mooReply",
               "selfCorrect",
               "userCorrect",
               "saveLast",
               "greeter",
               "awayMsgKicker",
               "pasteSnarfer"]
    unaddressedRegexps = ["ytSnarfer"]

    ownerNick = 'wolfy1339'
    buffer = {}
    buffsize = 10
    alpha = []
    alpha += 'QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'
    annoyUser = []
    random.seed()
    random.seed(random.random())
    kickuser = {}

#####################
###   Commands....###
#####################

    def banmask(self, irc, msg, args, hostmask):
        """<nick|hostmask>

        Gets IP based hostmask for ban. """

        failed = False
        ipre = \
            re.compile(r"[0-9]{1,3}[.-][0-9]{1,3}[.-][0-9]{1,3}[.-][0-9]")
        bm = ipre.search(hostmask)
        try:
            bm = bm.group(0)
            bm = bm.replace('.', '?')
            bm = bm.replace('-', '?')
            irc.reply('*!*@*' + bm + '*')
        except:
            hostmask = hostmask.split('@')[1]
            count = 0
            while count < 10:
                hostmask = hostmask.replace(str(count), '?')
                count += 1
            irc.reply('*!*@%s' % hostmask, prefixNick=False)
            if self.consolechannel:
                irc.queueMsg(ircmsgs.privmsg(
                        self.consolechannel, 'BANMASK: *!*@%s returned for %s' %
                        (hostmask, msg.nick)))

    banmask = wrap(banmask, ['hostmask'])

    def me(self, irc, msg, args):
        """<no arguments>

        Returns your nick. """

        irc.reply(msg.nick)

    me = wrap(me, [])

    def rand(self, irc, msg, args, min, max, num):
        """[min] <max> [amount]

        Generates a random number from [min] to <max>, [amount] number of times."""

        random.seed()
        random.seed(random.random())

        if min > max and not num:
            num = max
            max = min
            min = 0
        elif min > max:
            (min, max) = (max, min)

        if not num:
            num = 1
        if not max:
            max = min
            min = 0

        try:
            min = int(min)
            max = int(max)
            num = int(num)
        except:
            irc.error('Non numeric value(s) given')
            return 0

        if num > 25:
            num = 25
        x = 0
        output = ''
        while x < num:
            output += str(int(random.randint(min, max))) + ' '
            x += 1
        irc.reply(output)

    rand = wrap(rand, ['int', optional('int'), optional('int')])

    def stewieQuote(self, irc, msg, args):
        data = \
            utils.web.getUrl(
                'http://smacie.com/randomizer/family_guy/stewie_griffin.html')
        quote = \
            data.split('<td valign="top"><big><big><big><font face="Comic Sans MS">')[
                1].split('</font></big></big></big></td>')[0]
        irc.reply(quote, prefixNick=False)

#    stewie = wrap(stewieQuote)

    def geoip(self, irc, msg, args, ohostmask):
        """<IPv4 Address>

        Find where an ip address is in the world"""

        try:
            tmphostmask = irc.state.nickToHostmask(ohostmask)
            if tmphostmask:
                ohostmask = tmphostmask
        except:
            pass
        ohostmask = ohostmask.split("@")[-1]
        ipre = \
            re.compile(r"[0-9]{1,3}[.-][0-9]{1,3}[.-][0-9]{1,3}[.-][0-9]{1,3}")
        hostmask = ipre.search(ohostmask)

        if '/' in ohostmask and not hostmask:
            irc.reply('Unable to locate IP - user cloak detected')
            return None

        if hostmask:
            try:
                hostmask = hostmask.group(0)
                hostmask = hostmask.replace('-', '.')
            except:
                hostmask = hostmask
        else:
            hostmask = ohostmask

        if '.' not in hostmask:
            if ':' in hostmask:
                irc.reply('Unable to locate IP - IPv6 not supported')
            else:
                irc.reply('Unable to locate IP - unknown nick')
            return None

        self.log.info('GeoIP: %s', hostmask)

        if "gateway" in hostmask:
            hostmask = hostmask.split("ip.")[1]

        data = utils.web.getUrl(
            "http://infosniper.net/?ip_address=%s" %
            hostmask)
        data = data.split(
            '<!-- ################################################################################## -->')[5]
        data = re.split('<[^<>]+>|\\n| |	|   |  ', data)

        x = 0
        info = []
        while x < len(data):
            if data[x] is '' or len(data[x]) < 2 and ' ' in data[x]:
                pass
            else:
                info += [data[x]]
            x += 1

        country = info[20].strip()
        city = info[5].strip()
        try:
            tz = info[27].strip()
        except:
            tz = 'n/a'
        try:
            to = info[30].strip()
        except:
            to = 'unknown'
        if "-" not in to:
            to = '+%s' % to
        lat = info[13].strip()
        lon = info[21].strip()
        provider = info[11].strip()

        if city.lower() == 'n/a' and tz.lower() == 'n/a':
            irc.reply('Unable to locate IP - not found')
            return None

        if lat.lower() != 'n/a' and lon.lower() != 'n/a':
            tinyurl = utils.web.getUrl(
                'http://tinyurl.com/api-create.php?url=http://maps.google.com/maps?q=%s,%s' %
                (lat, lon))
            tinyurlLink = ' (%s)' % tinyurl
        else:
            tinyurlLink = ''

        irc.reply(
            '%s is near %s in %s%s. The timezone is %s and is UTC/GMT%s. The provider is %s' %
            (hostmask, city, country, tinyurlLink, tz, to, provider))

    geoip = wrap(geoip, ['text'])

    def bug(self, irc, msg, args, cmd, txt):
        """<plugin> [details of bug]

        Use this command when the bot has a bug. It places a note in the logs and sends the owner a message."""

        self.log.error(
            '****Error in {0} reported by {1}: {2}****'.format(cmd, msg.nick, txt))
        irc.queueMsg(
            ircmsgs.privmsg(
                'Memoserv',
                'SEND {0} Bug found in {1} by {2} ({3})'.format(
                    self.ownerNick, cmd, msg.nick, txt)))
        irc.replySuccess('Bug reported.')

    bug = wrap(bug, ['something', additional('text')])

    def kicked(self, irc, msg, args, nick):
        """[user]

        Shows how many times [user] has been kicked and by who.
        If [user] isn't provided, it returns infomation based on the caller."""

        if nick is None:
            ref = msg.nick.lower()
            nick = msg.nick
        else:
            ref = nick.lower()

        with open('KCOUNT', 'r') as f:
            kickdata = json.load(f)

        try:
            kickdata = kickdata[ref]
            reply = '{0} has been kicked {1} times, '.format(nick,
                                                             kickdata['total'])
            for each in kickdata:
                if each in 'total':
                    continue
                reply = '{0} {1} by {2},'.format(reply, kickdata[each],
                                                 each)
            irc.reply(reply[:-1].replace('o', '\xF0'))
        except:
            irc.reply('{0} hasn"t been kicked it seems.'.format(nick))

    kicked = wrap(kicked, [optional("nick")])

    def annoy(self, irc, msg, args, channel, nick, mins):
        """[channel] <nick> [mins]

        Repeats everything the user says via a NOTICE for 2 minutes if [mins] is not specified.
        Blame Doxin for this."""

        if not mins or mins == 0:
            mins = 2

        expires = time.time() + mins * 60

        try:

            def f():
                try:
                    self.annoyUser.pop(self.annoyUser.index(nick.lower()))
                    self.log.info(
                        'ANNOY: No longer annoying {0}'.format(nick))
                except:
                    self.log.info('ANNOY: Expired for {0}'.format(nick))

            schedule.addEvent(f, expires)
        except:
            irc.error('I borked.')
            return 0

        self.log.info(
            'ANNOY: Annoying {0} for {1} minutes'.format(nick, mins))
        self.annoyUser += [nick.lower()]

    annoy = wrap(annoy, ['op', 'nickInChannel', optional('float')])

    def unannoy(self, irc, msg, args, channel, nick):
        """[channel] <nick>

        Stops annoying someone."""

        try:
            self.annoyUser.pop(self.annoyUser.index(nick.lower()))
            self.log.info('ANNOY: No longer annoying {0}'.format(nick))
        except:
            irc.error('That user isn\'t being annoyed.')
            return 0

    unannoy = wrap(unannoy, ['op', 'nick'])

    def justme(self, irc, msg, args, url):
        """<url>

        Checks if a website is up or down (using isup.me)"""

        try:
            url = url.split('//')[1]
        except:
            pass
        socket.setdefaulttimeout(60)
        try:
            data = utils.web.getUrl("http://isup.me/{0}".format(url))
        except:
            irc.reply("isup.me seems down.")
            return
        if "is up." in data:
            irc.reply("It's just you.")
        elif "looks down" in data:
            irc.reply("It's down.")
        elif ("If you can see this page and still think we're down, it's just you"
                in data):
            irc.reply("It's just you.")
        else:
            irc.error("Check URL and try again")

    justme = wrap(justme, ["something"])

    def multikick(self, irc, msg, args, channel, nick, num, message):
        """<nick> <num> [message]

        Kicks <nick> every time [s]he talks up to <num> (max 10) times with [message].
        Use #n to insert number of remaining kicks."""

        if not channel:
            channel = "#powder"
        try:
            num = int(num)
        except:
            irc.error("Non-numeric value given.")
            return 0
        if num > 10:
            num = 10
        nick = nick.lower()
        try:
            self.kickuser[channel]
        except:
            self.kickuser[channel] = {}
        self.kickuser[channel][nick] = {}
        self.kickuser[channel][nick]["num"] = num
        if not message or message == "":
            message = "#n kick(s) remaining."
        self.kickuser[channel][nick]["msg"] = message

        irc.reply(
                "Kicking anyone with {0} in their nick {1} times.".format(
                    nick, num), private=True)

    multikick = wrap(multikick, [
            "op", ("haveOp", "Kick a user"), "something", "something", optional("text")])

#####################
###....RegExps....###
#####################

    def _color(self, c, fg=None, bg=None):
        if c == " ":
            return c
        if fg is None:
            fg = str(random.randint(2, 15)).zfill(2)
        else:
            fg = str(fg).zfill(2)
        if bg is None and c != ",":
            return "\x03%s%s" % (fg, c)
        else:
            if bg is None:
                # or \x03%s,16%s or \x03%s,00 or \x03%s\x03 ?
                return "\x03%s%s%s" % (fg, "\u200b", c)
            else:
                bg = str(bg).zfill(2)
                return "\x03%s,%s%s" % (fg, bg, c)

    def mooReply(self, irc, msg, match):
        r"""^((./door |!|.+:\s+)?moo+)+[\s.]*$"""

        self.log.info("moo detected")
        if random.random() < 0.05:
            if random.random() < 0.5:
                text = "mooMOOmooMOOmoomooMOO"
            else:
                text = "POTATOES"
            colors = utils.iter.cycle([4, 7, 8, 3, 2, 12, 6])
            L = [self._color(c, fg=colors.next()) for c in
                 str(ircutils.stripColor(text), "utf-8")]

            if self.registryValue('enableMooReply', msg.args[0]):
                irc.reply(
                    "".join(L).encode("utf-8") + "\x03",
                    prefixNick=False)
            else:
                return

    mooReply = urlSnarfer(mooReply)

    def greeter(self, irc, msg, match):
        r"""^(hello|hi|sup|hey|o?[bh]ai|wa+[sz]+(a+|u+)p?|Bye+|cya+|later[sz]?)([,. ]+(stewi?e?(griffin(sub)?)?|bot|all|there|SGS)\b|der$)"""

        if "," in match.group(0):
            hail = match.group(0).split(",")[0]
        elif "." in match.group(0):
            hail = match.group(0).split(".")[0]
        else:
            hail = match.group(0).split(" ")[0]
        self.log.info("Responding to %s with %s" % (msg.nick, hail))

        if self.registryValue('enableGreeter', msg.args[0]):
            irc.reply("%s, %s" % (hail, msg.nick), prefixNick=False)
        else:
            return

    greeter = urlSnarfer(greeter)

    def awayMsgKicker(self, irc, msg, match):
        r"""(is now (set as )?away [-:(] Reason|is no longer away [:-] Gone for|is away:)"""

        if self.registryValue('enableAwayMsgKicker', msg.args[0]):
            self.log.info("KICKING %s for away announce" % msg.nick)
            ir.queuemsg(
                ircmsgs.kick(
                    msg.args[0],
                    msg.nick,
                    "Autokick: Spam (Away/Back Announce)"))
        else:
            return

    awayMsgKicker = urlSnarfer(awayMsgKicker)

    def _ytinfo(self, irc, url, nickPrefix):
        code = False
        if not code:
            match = re.search(r"youtube[.]com/.*v[/=]([0-9A-z\-_]{11})", url)
            if match:
                code = match.group(1)
        if not code:
            match = re.search(r"youtu.be/([0-9A-z\-_]{11})", url)
            if match:
                code = match.group(1)
        if not code:
            match = re.match(r"^([0-9A-z\-_]{11})$", url)
            if match:
                code = match.group(1)

        if not code:
            irc.error("Could not find youtube link")
            return

        if url.find("v=") != -1 or url.find("&") != -1:
            if url.find("v=") != -1:
                url = url.split("v=")[1]
            if url.find("&") != -1:
                url = url.split("&")[0]
        else:
            url = url[-11:]

        self.log.info("ytSnarfer - Video ID: %s" % url)

        url = "http://www.youtube.com/watch?v=" + url

        data = utils.web.getUrl(url)
        data = data.split("<title>")[1].split("</title>")[0]
        ending = "- YouTube"
        if data.endswith(ending):
            data = data[:-len(ending)]
        data = data.strip()

        data = data.replace(
            "&quot;",
            "\"").replace(
            "&#39;",
            "'").replace(
            "&amp;",
            "&")
        irc.reply("Youtube video is '%s'" % data, prefixNick=nickPrefix)

    def youtube(self, irc, msg, args, url):
        """<url>

        Returns info on a youtube video"""

        self._ytinfo(irc, url, True)

    youtube = wrap(youtube, ["text"])

    def ytSnarfer(self, irc, msg, match):
        r""".*(youtube[.]com/.+v=[0-9A-z\-_]{11}).*"""

        if self.registryValue('youtubeSnarfer', msg.args[0]):
            if "Tribot200" in irc.state.channels[msg.args[0]].users:
                return
            self._ytinfo(irc, match.group(1), False)
        else:
            return

    ytSnarfer = urlSnarfer(ytSnarfer)

    def capsKick(self, irc, msg, match):
        r""".+"""

        data = match.group(0)
        data = data.strip("\x01ACTION").strip("\x01").strip(
            "\x02").strip("\x07").strip("\x0f")

        knownCapsNicks = ["UBERNESS", "ADL"]
        for each in knownCapsNicks:
            data = data.strip(each)
        data = list(data)

        # Simon: Increased from 5 to 15, was making quite a few people unhappy
        if len(data) < 15:
            return 0

        length = 0
        caps = 0
        for each in data:
            if each in self.alpha:
                length += 1
                if each in each.upper():
                    caps += 1

        self.log.warning(
            "{0} {1} {2}".format(
                length, caps, int(
                    float(caps) / length * 100)))

        if int(float(caps) / length * 100) > 60:
            self.log.info(
                "Kicking {0} from {1} for caps rage.".format(
                    msg.nick, msg.args[0]))
            if self.consolechannel:
                irc.queueMsg(
                    ircmsgs.privmsg(
                        self.consolechannel,
                        "KICK: %s for excessive caps. (automatic)" %
                        msg.nick))

            with open("KCOUNT", "r") as f:
                kd = json.load(f)

            with open("KCOUNT", "w") as f:
                try:
                    kd[msg.nick.lower()] += 1
                except:
                    kd[msg.nick.lower()] = 1
                f.write(json.dumps(kd, sort_keys=True, indent=4))

            reason = "{0} - Kicked {1} time".format(
                "Excessive Caps", kd[msg.nick.lower()])
            if kd[msg.nick.lower()] > 1:
                reason = "{0}s".format(reason)

            del kd
            irc.queueMsg(ircmsgs.kick(msg.args[0], msg.nick, reason))

    capsKick = urlSnarfer(capsKick)

    def pasteSnarfer(self, irc, msg, match):
        r"""http://pastebin[.]com/[A-Za-z0-9]{8}"""

        url = match.group(0)
        self.log.info("Pastebin Found - {0}".format(url))
        page = utils.web.getUrl(url).replace(" ", " ")

        paste = {}
        paste["name"] = page.split("<h1>")[1].split("</h1>")[0]

        page = page.split("<div class=\"paste_box_line2\">")[
            1].split("</div>")[0].strip().split("|")

        try:
            paste["by"] = page[0].split("<span")[0].split("\">")[
                1].split("</a>")[0].strip()
        except:
            paste["by"] = page[0].split(":")[1].split("on <")[0].strip()
        paste["date"] = page[0].split("<span title")[1].split(">")[
            1].split("<")[0].strip()
        paste["syntax"] = page[1].split(">")[1].split("<")[0].strip()
        paste["size"] = (page[2].split(":")[1])[1:-1].strip()
        paste["expires"] = (page[4].split(":")[1])[1:].strip()

        if 'None' in paste["syntax"]:
            paste["syntax"] = "Plain Text"

        if not self.registryValue("pasteSnarfer", msg.args[0]):
            return
        else:
            irc.reply(
                'Pastebin is {0} by {1} posted on {2} and is written in {3}. The paste is {4} and expires {5}'.format(
                    paste['name'], paste['by'], paste['date'], paste['syntax'], paste['size'], paste['expires']),
                prefixNick=False)

    pasteSnarfer = urlSnarfer(pasteSnarfer)

    def selfCorrect(self, irc, msg, match):
        r"""^s[/].*[/].*$"""

        match = match.group(0)
        data = match.split('/')

        newData = []
        x = 0
        while x < len(data):
            if (len(data[x]) and data[x][-1] == '\\' and
                    x + 1 < len(data)):
                newData += ['{0}/{1}'.format((data[x])[:-1], data[x + 1])]
                x += 2
            else:
                newData += [data[x]]
                x += 1

        data = newData

        channel = msg.args[0]

        try:
            self.buffer[channel]
        except:
            self.buffer[channel] = []

        for each in self.buffer[channel]:
            if msg.nick in each[0]:
                output = each[1]
                x = 1
                while x + 1 < len(data):
                    output = output.replace(data[x], data[x + 1])
                    output = output[0:min(len(output), 4096)]
                    x += 2

                self.log.info('Changing {0} to {1}'.format(each[1], output))
                irc.reply('<{0}> {1}'.format(
                        each[0], output), prefixNick=False)
                return 0

        irc.error('Not found in buffer')

    selfCorrect = urlSnarfer(selfCorrect)

    def userCorrect(self, irc, msg, match):
        r"""^u[/].*[/].*[/].*$"""

        if (msg.args[0] != '##powder-bots' and
                msg.args[0] != '##jacksonmj-test'):
            irc.noReply()
            return
        if not ircdb.checkCapability(
                msg.prefix,
                ircdb.makeChannelCapability(msg.args[0], 'op')):
            irc.noReply()
            return
        match = match.group(0)
        data = match.split('/')
        user = data[1]

        newData = []
        x = 0
        while x < len(data):
            if (len(data[x]) and data[x][-1] == '\\' and
                    x + 1 < len(data)):
                newData += ['{0}/{1}'.format((data[x])[:-1], data[x + 1])]
                x += 2
            else:
                newData += [data[x]]
                x += 1

        data = newData

        channel = msg.args[0]

        try:
            self.buffer[channel]
        except:
            self.buffer[channel] = []

        for each in self.buffer[channel]:
            print (
                user.lower(),
                each[0].lower(),
                user.lower() is each[0].lower())
            if user.lower() in each[0].lower():
                output = each[1]
                x = 2
                while x + 1 < len(data):
                    output = output.replace(data[x], data[x + 1])
                    output = output[0:min(len(output), 4096)]
                    x += 2

                if self.registryValue('enableUserCorrect', msg.args[0]):
                    self.log.info(
                        'Changing {0} to {1}'.format(
                            each[1], output))
                    irc.reply('<{0}> {1}'.format(
                            each[0], output),
                        prefixNick=False)
                else:
                    return

                return 0

        irc.error("Not found in buffer")

    userCorrect = urlSnarfer(userCorrect)

    def saveLast(self, irc, msg, match):
        r""".+"""

        channel = msg.args[0]

        try:
            self.buffer[channel]
        except:
            self.buffer[channel] = []

# Stuff for multikick

        if channel in self.kickuser:
            for each in self.kickuser[channel]:
                if (each in msg.nick.lower() and
                        not self.kickuser[channel][each]['num'] <= 0):
                    irc.queueMsg(ircmsgs.ban(msg.args[0], msg.nick))
                    irc.queueMsg(ircmsgs.kick(
                            msg.args[0], msg.nick, '{}'.format(
                                self.kickuser[channel][each]['msg'].replace(
                                    '#n', str(
                                        self.kickuser[channel][each]['num'])))))
                    self.kickuser[channel][each]['num'] -= 1

                    def un():
                        irc.queueMsg(ircmsgs.unban(msg.args[0], msg.nick))

                    schedule.addEvent(
                        un,
                        time.time() +
                        random.randint(
                            10,
                            60))  # 30,120

# END

        line = match.group(0).replace("\x01ACTION", "*").strip("\x01")

        if msg.nick.lower() in self.annoyUser:

            def fu():
                irc.queueMsg(ircmsgs.IrcMsg(
                        "NOTICE {0} :\x02\x03{},{1}{2}".format(
                            msg.nick, random.randint(
                                0, 15), random.randint(
                                0, 15), line)))

            schedule.addEvent(fu, time.time() + random.randint(2, 60))

        if re.match(r"^u[/].*[/].*[/].*$", match.group(0)) \
                or re.match(r"^s[/].*[/].*$", match.group(0)):
            return 1

        self.buffer[channel].insert(0, [msg.nick, line])
        if len(self.buffer[channel]) > self.buffsize:
            self.buffer[channel].pop(self.buffsize)
        return 1

    saveLast = urlSnarfer(saveLast)

    def pop(self, irc, msg, args, text):
        """

        Go pop, moo or Bang"""

        # text = unicode(text, "utf-8")

        r = random.random()
        if r < 0.05:
            irc.reply('goes BANG!', action=True)
        elif r < 0.1:
            irc.reply('goes moo!', action=True)
        else:
            if text is not None:
                if text.lower() == 'cherry':
                    text = msg.nick
                irc.reply('pops {}'.format(text), action=True)
            else:
                irc.reply('goes pop!', action=True)

        # irc.queueMsg(ircmsgs.action(channel, text.encode("utf-8")))

    pop = wrap(pop, [optional("text")])

Class = General

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
