import discord, datetime
from discord.ext import commands
bot = commands.Bot(command_prefix=".",case_insensitive=True, activity=discord.Game(name="with the guild members"),help_command=None)
bot.load_extension('jishaku')
bot.owner_ids = [477789603403792404,716503311402008577]
bot.ready_once = False
bot.uptime = datetime.datetime.utcnow()
bot.load_extension("category")


@bot.command()
async def reload(ctx):
    bot.reload_extension("category")
    await ctx.send("Done!")


token = None
with open("token.txt") as file:
    token=file.read()
bot.run(token)