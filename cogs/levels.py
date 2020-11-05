import discord
from discord.ext import commands
import aiosqlite as sql
import datetime
import random

class Levels(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self,msg):
        if not msg.guild or msg.author.bot:
            return
        xp = random.randint(0,10)
        ctx = await self.bot.get_context(msg)
        if ctx.valid:
            return
        async with sql.connect("./db/data.sql") as db:
            async with db.execute("SELECT * FROM levels WHERE id = ?",(ctx.author.id,)) as cursor:
                data = await cursor.fetchone()
                if not data:
                    await db.execute("INSERT INTO levels VALUES (?,?,?)",(ctx.author.id,0,1,))
                    data = (ctx.author.id,0,0,)
                    await db.commit()
                new_data = [ctx.author.id,xp,0]
                new_data[1] += data[1]
                new_data[2] = int(data[2])
                if new_data[1] >= data[2]*125:
                    new_data[1] = 0
                    new_data[2] += 1
                    roles = [ctx.guild.get_role(i) for i in [761841612161941524,761841883038744586,761842249793142815]]
                    channel = self.bot.get_channel(749082254482997298)
                    if new_data[2] > data[2]:
                        if new_data[2] == 10:
                            await ctx.author.add_roles(roles[0])
                        elif new_data[2] == 20:
                            await ctx.author.add_roles(roles[1])
                        elif new_data[2] == 30:
                            await ctx.author.add_roles(roles[2])
                        await channel.send(f'GG {ctx.author.mention} leveled up to level **{new_data[2]}**')
                await db.execute('UPDATE levels SET exp = ?, level = ? WHERE id = ?',(new_data[1],new_data[2],ctx.author.id,))
                await db.commit()

    @commands.command()
    @commands.guild_only()
    async def level(self,ctx,*,user:discord.User=None):
        person = ctx.author
        if user:
            if ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_channels:
                person = user
        async with sql.connect('./db/data.sql') as db:
            async with db.execute('SELECT * FROM levels WHERE id = ?',(person.id,)) as cursor:
                data = await cursor.fetchone()
                if not data:
                    await db.execute('INSERT INTO levels VALUES (?,?,?)',(person.id,0,1,))
                    await db.commit()
                    data = [person.id,0,1]
                embed = discord.Embed(title=f"Level stats for {person}",timestamp=datetime.datetime.utcnow(),colour=self.bot.color)
                embed.add_field(name="Level",value=data[2])
                embed.add_field(name="Experience",value=data[1])
                embed.set_footer(icon_url=person.avatar_url,text='Get exp by chatting')
                await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def rank(self,ctx):
        async with sql.connect("./db/data.sql") as db:
            async with db.execute('SELECT * FROM levels ORDER BY level DESC, exp DESC') as cursor:
                data = await cursor.fetchall()
                embed = discord.Embed(title=f'Level ranks on {ctx.guild.name}',description='',colour=self.bot.color)
                for bit in data:
                    embed.description += f"\n{self.bot.get_user(bit[0]).mention} **{bit[1]}** exp, level **{bit[2]}**"
                await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Levels(bot))
    print('(LEVELS) Loaded cog')