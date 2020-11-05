import discord
from discord.ext import commands
import datetime

class Profit(commands.Cog):
	def __init__(self,bot):
		self.bot = bot

	@commands.group(invoke_without_command=True)
	async def profit(self,ctx):
		return

	@profit.command()
	async def add(self,ctx,*,text):
		embed = discord.Embed(title=f"Profit Method!", description=text,color=self.bot.color, timestamp=datetime.datetime.utcnow())
		embed.set_author(icon_url=ctx.author.avatar_url,name=ctx.author)
		channel = self.bot.get_channel(770521664961511424)
		await channel.send(embed=embed)
		await ctx.send("Added!")

def setup(bot):
    bot.add_cog(Profit(bot))
    print('(PROFIT) Loaded cog')