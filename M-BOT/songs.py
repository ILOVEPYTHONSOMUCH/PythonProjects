
# โค้ดนี้ ไม่ใช่ของผมนะครับ ไป ก็อปมาดัดแปลง จาก https://gist.github.com/vbe0201/ade9b80f2d3b64643d854938d40a0a2d

import queue
import time
import discord
from discord.utils import get
import youtube_dl
import asyncio
from async_timeout import timeout
from functools import partial
import itertools
from youtube_dl import YoutubeDL
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"  ## song will end if no this line
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False, respone=True):
        loop = loop or asyncio.get_event_loop()
        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)
        if 'entries' in data:
            data = data['entries'][0]
        if respone:
          await ctx.send(f'```ini\n[เพิ่ม {data["title"]} ลงในเพลย์ลิสต์ แล้ว ไอสัส รอคิวด้วยมีมารยาทหน่อย ไอสัส]\n```')  # delete after can be added

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source, **ffmpeg_options), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data, requester=requester)


class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                del players[self._guild]
                return await self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'มีข้อผิดพลาดบางอย่าง กรุณาติดต่อ CoderMan\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source
            try:
              self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            except:
                try:
                    self._guild.voice_client.play(source,
                                                  after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                except:
                    try:
                        self._guild.voice_client.play(source,
                                                      after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
                    except:
                        self._guild.voice_client.play(source,
                                                      after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))

            self.np = await self._channel.send(f'**เล่นเพลง : ** `{source.title} ` อยู่ ไอเหี้ยที่ชื่อ  '
                                               f'`{source.requester}` สั่งมา !!!')
            await self.next.wait()
            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    async def destroy(self, guild):
        """Disconnect and cleanup the player."""
        await self._guild.voice_client.disconnect()
        return self.bot.loop.create_task(self._cog.cleanup(guild))


############
class songAPI:
    def __init__(self):
        self.players = {}

    async def play(self, ctx, search : str, loop):
        self.bot = ctx.bot
        self._guild = ctx.guild
        channel = ctx.author.voice
        if channel == None:
            await ctx.channel.send("** ไอสัส เข้าห้องก่อน ค่อยเชิญกูไป กูจะรู้ไหม ว่ามึงต้องการเล่นห้องไหน **")
            return
        channel = ctx.author.voice.channel
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client == None:
            await ctx.channel.send(f"กําลังเข้าไปเล่นเพลงที่ช่องเสียงที่ ชื่อ `{channel}` นะไอสัส ใช้กูจังเลย ไอเหี้ย !!!")
            await channel.connect()
            voice_client = get(self.bot.voice_clients, guild=ctx.guild)
        _player = self.get_player(ctx)
        try:
          z = int(loop)
          if z != 1 and z > 0:
              for i in range(loop):
                  source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False,respone=False)
                  await _player.queue.put(source)
          if z == 1:
              source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)
              await _player.queue.put(source)
        except ValueError:
            print("in")
            if loop == "playlist":
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False, respone=False)
                await _player.queue.put(source)
    players = {}

    def get_player(self, ctx):
        try:
            player = self.players[ctx.guild.id]
        except:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    async def stop(self, ctx):
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client == None:
            await ctx.channel.send("มึงตาบอดไหม เห็นไหมว่า กูยังไม่เข้าช่องเสียงเลย ไอโง่", delete_after=10)
            return

        if voice_client.channel != ctx.author.voice.channel:
            return
        ctx.channel.send(f"ไอเหี้ย `{ctx.author.name}` นี้สั่งให้กูหยุดเพลงถาวร")
        voice_client.stop()

    async def pause(self, ctx):
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client == None:
            await ctx.channel.send("มึงตาบอดไหม เห็นไหมว่า กูยังไม่เข้าช่องเสียงเลย ไอโง่", delete_after=10)
            return

        if voice_client.channel != ctx.author.voice.channel:
            return
        await ctx.channel.send(f"ไอเหี้ย `{ctx.author.name}` นี้สั่งให้กูหยุดเพลง")
        voice_client.pause()

    async def resume(self, ctx):
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client == None:
            await ctx.channel.send("มึงตาบอดไหม เห็นไหมว่า กูยังไม่เข้าช่องเสียงเลย ไอโง่", delete_after=10)
            return

        if voice_client.channel != ctx.author.voice.channel:
            return
        await ctx.channel.send(f"ไอเหี้ย `{ctx.author.name}` นี้สั่งให้กูเล่นเพลงต่อ")
        voice_client.resume()

    async def leave(self, ctx):
        del self.players[ctx.guild.id]
        await ctx.voice_client.disconnect()

    async def queueList(self, ctx):
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client == None or not voice_client.is_connected():
            await ctx.channel.send("กูยังไม่ได้เล่นเพลงแรกเลย จะขอดูทําพ่อง !!!", delete_after=10)
            return

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('มึงยังไม่เพิ่มเพลงให้กู เลยจะเอาที่ไหน มาให้มึงห้ะ ไอสัส')

        # 1 2 3
        upcoming = list(itertools.islice(player.queue._queue, 0, player.queue.qsize()))
        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'เพลงต่อไป - อีก {len(upcoming)} เพลง (อาจมีเพิ่มก็ได้)', description=fmt)
        await ctx.send(embed=embed)
    async def skip(self, ctx):
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)

        if voice_client == None or not voice_client.is_connected():
            await ctx.channel.send("กูยังไม่ได้เล่นเพลงแรกเลย ใจร่มๆ", delete_after=10)
            return

        if voice_client.is_paused():
            pass
        elif not voice_client.is_playing():
            return
        voice_client.stop()
        await ctx.send(f'**`{ctx.author}`**: สั่งให้กูข้ามเพลง นี้ ไปรุมกระทืบ มันได้เลย')
    async def clear(self,ctx):
        voice_client = get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client == None or not voice_client.is_connected():
            await ctx.channel.send("มึงตาบอดไหม เห็นไหมว่า กูยังไม่เข้าช่องเสียงเลย ไอโง่", delete_after=10)
            return
        player = self.get_player(ctx)
        if player.queue.empty():
            upcoming = list(itertools.islice(player.queue._queue, 0, player.queue.qsize()))
            fmt = "`ไม่มีเพลงต่อแล้ว แต่อย่าเพิ่มเถอะ กูเหนื่อย เป็นเหมือนกันไอเหี้ย`"
            embed = discord.Embed(title=f'เพลงต่อไป - อีก {len(upcoming)} เพลง (อาจมีเพิ่มก็ได้)', description=fmt)
            await ctx.send(embed=embed)
        q = player.queue
        size = q.qsize()
        await ctx.channel.send(f"**ลบเพลงออกจากเพลย์ลิสต์ไป {q.qsize()} **เพลง คนสั่งคือ `{ctx.author.name}`")
        while size != 0:
             q.get_nowait()
             q.task_done()
