
import discord
import os
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
import requests
import pyjokes
import json
import wikipedia
from dotenv import load_dotenv
from random import choice

#this is req for loading our bot token 
load_dotenv()
TOKEN=os.getenv('TOKEN')
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
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
# ffmpeg must be installed on machine / server hosting our code fofr testing its our pc 
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
# ytdl is youyube package to search for song and download it 
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


client = commands.Bot(command_prefix='?')
# list of status benath username of profile of server chaingin every 10 sec
status = ['i m Talkative!', 'Snoozed!', 'Eager to Chat!']
#method for getting quote
def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -- " + json_data[0]['a']
  return(quote)

@client.event
async def on_ready():
    change_status.start()
    print('Talkative Bot is UP!')

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}!  Ready to rock ? See `?help` command for details!')

@client.command(name='ping', help='This command returns the latency')
async def ping(ctx):
    await ctx.send(f'**Ping!** Latency: {round(client.latency * 1000)}ms')

@client.command(name='hello', help='This command returns a random welcome message')
async def hello(ctx):
    responses = ['how are you?', 'All well ?!', 'Start playing something' , 'Check what can i do with ?help','**Wasssuup!**']
    # await ctx.send(choice(responses))
    temp = choice(responses)
    await ctx.send(f" Hi , `{ctx.author.name}`, {temp}")

@client.command(name='die', help='This command returns a random last words')
async def die(ctx):
    responses = ['why have you brought my short life to an end', 'i could have done so much more', 'i have a family, kill them instead']
    await ctx.send(choice(responses))

@client.command(name='credit', help='This command returns the credits')
async def credits(ctx):
    await ctx.send('Made by  `AC`')
   
@client.command(name='inspireme', help='This command returns inspiring quote')
async def inspireme(ctx):
    quote = get_quote()
    await ctx.send(quote)

@client.command(name='joke', help='This command returns a joke')
async def joke(ctx):
    joke = pyjokes.get_joke()
    await ctx.send(joke)

@client.command(name='wiki', help='This command returns information from wikipedia of that keyword')
async def wiki(ctx,param):
    result = wikipedia.summary(param)
    await ctx.send(result)

@client.command(name='cryptoprice', help='This command returns prices of top 5 crypto currencies in USD')
async def cryptoprice(ctx):
    await ctx.send("**Below are prices of Top 5 Crypto Curriences in USD**")
    response = requests.get('https://api.coinstats.app/public/v1/coins?skip=0&limit=5&currency=USD')
    jsodata = json.loads(response.text)
    for i in range(5):
        formatted_float = "{:.2f}".format(jsodata['coins'][i]['price'])
        await ctx.send(jsodata['coins'][i]['id'] +' : '+ str(formatted_float) + '$')

@client.command(name='meme', help='This command shows a meme')
async def meme(ctx):
    content = requests.get("https://meme-api.herokuapp.com/gimme").text
    data = json.loads(content,)
    meme = discord.Embed(title=f"{data['title']}", Color = discord.Color.random()).set_image(url=f"{data['url']}")
    await ctx.reply(embed=meme)

@client.command(name='play', help='This command plays music')
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("Oops !! You Are not connected to Any Voice Channel Connect to it first ")
        return

    else:
        channel = ctx.message.author.voice.channel

    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('**Now playing:** {}'.format(player.title))

@client.command(name='stop', help='This command stops the music and makes the bot leave the voice channel')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()

@tasks.loop(seconds=10)
async def change_status():
    await client.change_presence(activity=discord.Game(choice(status)))

client.run(TOKEN)