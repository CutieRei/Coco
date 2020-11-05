import aiohttp
from discord.ext import commands
import datetime
import json
import discord

class Growtopia(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.url = 'https://growtopiagame.com'

    @commands.command(aliases=["rw"])
    async def render(self,ctx,world):
        """
        Shows an image of a rendered world
        """
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                async with sess.get(self.url+f'/worlds/{world.lower()}.png') as resp:
                    if not resp.status == 200:
                        await ctx.send("That world isn't rendered yet..")
                        return
                    embed = discord.Embed(title=f"render world of {world.upper()}",colour=self.bot.color)
                    embed.set_image(url=self.url+f'/worlds/{world.lower()}.png') 
                    await ctx.send(embed=embed)             
    
    @commands.command(aliases=["stat"])
    async def status(self,ctx):
        """
        Shows the server status of growtopia
        """
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                async with sess.get(self.url+"/detail") as resp:
                    data = await resp.json(content_type="text/html")
                    data['online_user'] = int(data["online_user"])
                    colour = discord.Colour
                    embed = discord.Embed(
                    title=f"Growtopia Status",
                    colour=colour.red() if data.get('online_user') < 10 else colour.green(),
                    timestamp=datetime.datetime.utcnow(),
                    description=f"Online User: **{str(data.get('online_user'))}**"+"\nStatus: "+("**Online**" if data.get('online_user') > 10 else "**Offline**")
                    )
                    embed.set_thumbnail(url='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRFfI3vRa4Uu7DK2QmgeUY-tCLKyc4eOLGl5cvQDkjjlXe6y-NjFZwmbt-v&s=10')
                    time = datetime.datetime.utcnow()-datetime.timedelta(hours=4)
                    hour, minute, second = str(time.hour),str(time.minute),str(time.second)
                    if len(hour) == 1:
                        hour = f"0{hour}"
                    if len(minute) == 1:
                        minute = f"0{minute}"
                    if len(second) == 1:
                        second = f"0{second}"
                    embed.set_footer(text=f"{hour}:{minute}:{second} Growtopia Time")
                    await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Growtopia(bot))
    print('(GROWTOPIA) Loaded cog')