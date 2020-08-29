import discord,aiosqlite, datetime
from discord.ext import commands,tasks
sql = aiosqlite
bot = commands.Bot(command_prefix=".",case_insensitive=True, activity=discord.Game(name="with the guild members"),help_command=None)
bot.load_extension('jishaku')
bot.owner_ids = [477789603403792404,716503311402008577]
bot.load_extension("category")


@bot.command()
async def reload(ctx):
    bot.reload_extension("category")
    await ctx.send("Done!")

@tasks.loop(hours=2)
async def loop():
    loop.stop()
    with open('db/data_backup.sql','wb') as backup:
        with open("db/data.sql",'rb') as db:
            backup.write(db.read())

loop.start()
token = None
with open("token.txt") as file:
    token=file.read()
bot.run(token)