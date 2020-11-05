import discord
import aiosqlite as sql
import datetime
import asyncio
import aiosqlite
import inspect
import random
from discord.ext import commands,tasks
import growtopia


class Utility(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.loop.start()
    
    async def check(self,ctx):
        if ctx.author.id in self.bot.owner_ids:
            return True
        return False

    @commands.command()
    async def emoji(self,ctx,emoji: discord.PartialEmoji):
        await ctx.send(emoji.url)
    
    @commands.command()
    async def ping(self,ctx):
        """
        Shows the bot latency
        """
        time1 = datetime.datetime.utcnow()
        msg = await ctx.send('Loading....')
        time2 = datetime.datetime.utcnow()
        ping = (time2-time1).total_seconds()*100
        colour = None
        if ping > 150:
            colour = discord.Colour.red()
        elif ping > 95:
            colour = discord.Colour.gold()
        else:
            colour = discord.Colour.green()
        embed = discord.Embed(
        title='Pong!',
        colour=colour,
        timestamp=datetime.datetime.utcnow(),
        description=f"My ping is {int(ping)}ms"
        )
        embed.set_footer(icon_url=ctx.me.avatar_url,text=random.choice(["I won!","Hey?","Why hello there","Sup!","Ping Pong, i win!","Hey there bud"]))
        await msg.edit(content=None,embed=embed)
    
    @commands.command()
    async def uptime(self,ctx):
        """
        Shows the bot lifetime
        """
        second,minute,hour,day = int((datetime.datetime.utcnow()-self.bot.uptime).seconds),0,0,int((datetime.datetime.utcnow()-self.bot.uptime).days)
        if second > 60:
            minute += second//60
            second = second%60
        if minute > 60:
            hour += minute//60
            minute = minute%60
        if day >= 1:
            hour = hour%24
        embed = discord.Embed(
        title="Bot Uptime!",
        colour=self.bot.colour,
        timestamp=datetime.datetime.utcnow(),
        description=f"{day}d {hour}h {minute}m {second}s"
        )
        await ctx.send(embed=embed)
    
    async def syntax(self,cmd):
        help = cmd.help or "No description"
        call = [cmd.name]
        for i in cmd.aliases:
            call.append(f"|{i}")
        call = f"{''.join(call)}"
        params = []
        for name,param in cmd.params.items():
            if name in ["self","ctx"]:
                continue
            if param.default != inspect._empty:
                params.append(f"[{name}]")
            else:
                params.append(f"<{name}>")
        return {"help":help,"alias":call,"params":params}
    
    @tasks.loop(hours=2)
    async def loop(self):
        with open('db/data_backup.sql','wb') as backup:
            with open("db/data.sql",'rb') as db:
                backup.write(db.read())

    @commands.group(invoke_without_command=True,case_insensitive=True)
    async def avatar(self,ctx):
        """
        Group command avatar
        """
        commands = ctx.command.commands
        desc = [f"{cmd}" for cmd in commands]
        embed=discord.Embed(title="Subcommands", description="\n".join(desc),colour=self.bot.color)
        await ctx.send(embed=embed)
    
    @avatar.command()
    async def show(self,ctx,*,member: discord.User=None):
        """
        Shows avatar of a member
        """
        if not member:
            member = ctx.author
        embed = discord.Embed(url=str(member.avatar_url),title="Avatar URL",colour=self.bot.color)
        embed.set_image(url=member.avatar_url_as(static_format='png',size=256))
        await ctx.send(embed=embed)
    
    @avatar.command()
    @commands.is_owner()
    async def save(self,ctx,*,member: discord.User=None):
        """
        Save avatar of a member in .png format
        """
        if not member:
            member = ctx.author
        avatar = member.avatar_url
        avatar_uri = f'{member.id}.{str(avatar).split(".")[-1].split("?")[0]}'
        if member.is_avatar_animated():
            avatar_uri = avatar_uri.split(".")
            avatar_uri[-1] = "gif"
            avatar_uri = ".".join(avatar_uri)
        else:
            avatar_uri = avatar_uri.split(".")
            avatar_uri[-1] = "png"
            avatar_uri = ".".join(avatar_uri)
        with open(f'avatars/{avatar_uri}',"wb") as file:
            await avatar.save(file)
        await ctx.send(f"Saved in ```/avatars/{avatar_uri}```")
    
    @commands.command()
    async def help(self,ctx,*,cmd=None):
        """
        Shows this!
        """
        if not cmd:
            embed = discord.Embed(
            title="Help commands list",
            description="show a list of commands",
            colour=self.bot.colour,
            timestamp=datetime.datetime.utcnow()
            )
            cmds = dict({})
            for name,cog in self.bot.cogs.items():
                if not [i for i in cog.walk_commands()]:
                    continue
                cmds[name] = []
            cmds['No Modules'] = []
            for command in self.bot.commands:
                if not command.cog_name:
                    cmds['No Modules'].append(command.name)
                    continue
                cmds[command.cog_name].append(command.name)
            for cog,cmd in cmds.items():
                embed.add_field(name=cog,value=",".join(cmd) or "No commands",inline=False)
            
            embed.set_footer(icon_url=self.bot.user.avatar_url_as(static_format='png'),text=f'Type {ctx.prefix}help [command] for more info about specific command')
            await ctx.send(embed=embed)
            return
        cmd = self.bot.get_command(cmd.lower())
        if cmd:
            command = await self.syntax(cmd)
            embed = discord.Embed(
            title=f"Help info for {cmd.name}",
            description=f"```{command['alias']} {' '.join(command['params'])}```",
            timestamp=datetime.datetime.utcnow(),
            colour=ctx.author.colour
            )
            embed.add_field(name="Description",value=command['help'],inline=False)
            subcommands = getattr(cmd,'commands',None)
            if subcommands:
                subco = []
                for subs in subcommands:
                    syntax = await self.syntax(subs)
                    subco.append(f"```{syntax['alias']} {' '.join(syntax['params'])}```")
                embed.add_field(name="Subcommands",value="\n".join(subco))
            await ctx.send(embed=embed)
        else:
            await ctx.send("Nope")

    @commands.command()
    @commands.guild_only()
    async def suggest(self,ctx):
        """
        For suggesting
        """
        def check(msg):
            return True if msg.author.id == ctx.author.id else False
        channel = self.bot.get_channel(739526508137152633)
        msg = await ctx.send('What is your suggestion title? (type "abort" to abort suggestion)')
        title = None
        try:
            title = await self.bot.wait_for('message',check=check,timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("I waited too long for response")
            return
        await msg.delete()
        if title.content.lower() == 'abort':
            await ctx.send("Suggestion has been aborted")
            await title.delete()
            return
        await title.delete()
        msg = await ctx.send('What is the suggestion itself?')
        description = None
        try:
            description= await self.bot.wait_for('message',check=check,timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("I waited too long for response")
            await msg.delete()
            return
        await msg.delete()
        await description.delete()
        embed = discord.Embed(
            title=f'Suggestion by {ctx.author}',
            colour=self.bot.color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name='Title',value=title.content)
        embed.add_field(name="Description",value=description.content)
        embed.set_footer(icon_url=ctx.author.avatar_url_as(static_format='png'),text=ctx.author)
        suggest = await channel.send(embed=embed)
        await suggest.add_reaction('\U0000274e')
        await suggest.add_reaction('\U00002705')
        await ctx.send("Suggestion posted!")

def setup(bot):
    bot.add_cog(Utility(bot))
    print('(UTILITY) Loaded cog')