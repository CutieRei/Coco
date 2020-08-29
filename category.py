import discord, aiosqlite, datetime, inspect,uuid
from discord.ext import commands
sql = aiosqlite


class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = self.bot.get_channel(749082254482997298)
    
    @commands.command()
    @commands.guild_only()
    async def register(self,ctx,*,name):
        """
        register your GrowID
        """
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(ctx.author.id,)) as c:
                user = await c.fetchone()
                if user:
                    await ctx.send("You already registered")
                    return
            
            await db.execute("INSERT INTO members (id,growid) VALUES (?,?)",(ctx.author.id,name,))
            await db.commit()
            await ctx.author.edit(nick=f"「{name}」{ctx.author.name}")
            await self.log.send(embed=discord.Embed(description=f"{ctx.author} Registered as {name} at {datetime.datetime.utcnow()}", colour=ctx.author.colour))
            await ctx.send("Registered!")

    @commands.command()
    @commands.guild_only()
    async def info(self,ctx,member:discord.Member=None):
        """
        get info about member or yourself
        """
        user = ctx.author
        if member and ctx.author.guild_permissions.manage_channels:
            user = member
        
        data = None
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(user.id,)) as c:
                res = await c.fetchone()
                if res:
                    data = res
                else:
                    await ctx.send("I cant seem to find them..")
                    return
            embed = discord.Embed(
                title=f"Guild members info for {user.display_name}",
        description=f"Info for {user} in the guild",
            timestamp=datetime.datetime.utcnow(),
            colour=user.colour
            )
            embed.set_footer(icon_url=ctx.guild.me.avatar_url,text="v1")
            embed.set_thumbnail(url=user.avatar_url_as(static_format='png'))
            embed.add_field(name="Contribution",value=data[2],inline=False)
            embed.add_field(name="GrowID",value=data[1],inline=False)
            embed.add_field(name="ID",value=data[0],inline=False)
            await ctx.send(embed=embed)

    @commands.command(aliases=["depo","dep"])
    @commands.is_owner()
    @commands.guild_only()
    async def deposit(self,ctx,amount:int,member: discord.Member):
        """
        Deposit some points to a member
        """
        growid = None
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(member.id,)) as c:
                user = await c.fetchone()
                if not user:
                    await ctx.send("Cannot find member, mainly because they haven't registered their growid")
                    return
                growid = user[1]
                await db.execute("UPDATE members SET contribution = contribution + ? WHERE id = ?",(amount,member.id,))
                await db.commit()
                embed = discord.Embed(
                title=f"Successful deposited!",
                timestamp=datetime.datetime.utcnow(),
                colour=ctx.author.colour    
                )
                embed.add_field(name="Amount",value=amount)
                embed.add_field(name="GrowID",value=user[1])
                embed.set_footer(icon_url=ctx.guild.me.avatar_url,text="v1")
                embed.set_thumbnail(url=member.avatar_url_as(static_format='png'))
                await self.log.send(embed=discord.Embed(description=f"{ctx.author} Deposited {amount} to {member} with the growid of {growid}", colour=ctx.author.colour))
                await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def top(self,ctx):
        """
        Display top 10 members who contribute
        """
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members ORDER BY contribution DESC LIMIT 10") as c:
                users = await c.fetchall()
                embed = discord.Embed(
                title="Contribution Leaderboard",
                timestamp=datetime.datetime.utcnow(),
                colour=ctx.author.colour    
                )
                count = 1
                for id,name,contri,wls in users:
                    embed.add_field(name=str(count)+f". {self.bot.get_user(id)}",value=f"GrowID: **{name}**"+"\n"+f"Contribution: **{contri}**",inline=False)
                    count += 1
                embed.set_footer(icon_url=ctx.guild.me.avatar_url,text="v1")
                await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def reset(self,ctx):
        """
        Reset the contribution points
        """
        def check(msg):
            if msg.author.id == ctx.      author.id:
                return True
            return False
        msg1 = await ctx.send("Are you sure?")
        msg = await self.bot.wait_for("message",check=check)
        await msg1.delete()
        if msg.content.lower() == "yes":
            async with sql.connect("db/data.sql") as db:
                await db.execute("UPDATE members SET contribution = 0")
                await db.commit()
            await ctx.send("Contribution has been restarted!")
            await msg.delete()
        else:
            await ctx.send("Okay then")
            await msg.delete()
        await self.log.send(embed=discord.Embed(description=f"{ctx.author} Reseted the contribution points at {datetime.datetime.utcnow()}",colour=ctx.author.colour))

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def warn(self,ctx,member: discord.Member):
        """
        Warn members for invalid growid reason
        """
        embed = discord.Embed(
        title="Invalid GrowID",
        description=f"Hey {member}, your GrowID seems wrong, its not on our guild members we have removed your data from our database to reduce RAM usage, please do `?register <growid>` again with the valid growid this time!",
        timestamp=datetime.datetime.utcnow(),
        colour=discord.Colour.from_rgb(255,20,0)
        )
        embed.set_footer(icon_url=ctx.author.avatar_url_as(static_format='png'),text=ctx.author)
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(member.id,)) as c:
                if not await c.fetchone():
                    await ctx.send("That user haven't registered!")
                    return
            await db.execute("DELETE FROM members WHERE id = ?",(member.id,))    
            await db.commit()
        await member.edit(nick=None)
        await ctx.message.add_reaction("✅")
        await member.send(embed=embed)
    
    @commands.command(aliases=["bal"])
    @commands.guild_only()
    async def balance(self,ctx,member: discord.Member=None):
        person = ctx.author
        wls = 0
        growid = None
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(person.id,)) as c:
                wls = await c.fetchone()
                growid = wls[1]
                if not wls:
                    await ctx.send("I cannot find anything...")
                    return
        if member and ctx.author.guild_permissions.manage_channels:
            person = member
        embed = discord.Embed(
        title=f"{person.display_name} Balance",
        description=f"**{wls[3]} World Locks**",
        colour=person.colour,
        timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name='GrowID',value=growid)
        embed.set_thumbnail(url=person.avatar_url_as(static_format='png'))
        embed.set_footer(icon_url=ctx.author.avatar_url_as(static_format='png'),text=ctx.author)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def give(self,ctx,amount:int,*,member: discord.Member):
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(member.id,)) as c:
                user = await c.fetchone()
                if not user:
                    await ctx.send("Im sorry but, that member haven't registered")
                    return
                await db.execute("UPDATE members SET wls = wls + ? WHERE id = ?",(amount,member.id,))
                await db.commit()
                await self.log.send(embed=discord.Embed(description=f"{ctx.author} Gave {member} **{amount}Wls** to their balance",colour=ctx.author.colour))
                await ctx.send("Success!")

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def ungive(self,ctx,amount:int,member:discord.Member):
    	async with sql.connect('db/data.sql') as db:
    		async with db.execute("SELECT * FROM members WHERE id = ?",(member.id,)) as c:
    			user = await c.fetchone()
    			if amount > user[3]:
    				amount = user[3]
    			if user:
    				await db.execute("UPDATE members SET wls = wls - ? WHERE id = ?",(amount,member.id,))
    				await db.commit()
    				embed = discord.Embed(title="Success",description=f"Successfully removed **{amount}Wls** from {member}",timestamp=datetime.datetime.utcnow(),colour=ctx.author.colour)
    				embed.add_field(name='GrowID',value=user[1])
    				await ctx.send(embed=embed)
    				return
    			await ctx.send('I cannot find them.')

class Utils(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
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
    
    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def dc(self,ctx):
        """
        disconnect the bot
        """
        await ctx.send("Disconnected!")
        await self.bot.logout()

    @commands.Cog.listener()
    async def on_ready(self):
        print("!--Bot ready--!")
    
    @commands.command()
    async def help(self,ctx,cmd=None):
        """
        Shows this!
        """
        if not cmd:
            embed = discord.Embed(
            title="Help commands list",
            description="show a list of commands",
            colour=ctx.author.colour,
            timestamp=datetime.datetime.utcnow()
            )
            for name,cog in self.bot.cogs.items():
                if name == "Jishaku" or not [i for i in cog.walk_commands()]:
                    continue
                cmd = []
                for i in cog.walk_commands():
                    cmd.append(str(i))
                embed.add_field(name=name,value=" , ".join(cmd),inline=False)
            embed.set_footer(icon_url=ctx.guild.me.avatar_url_as(static_format='png'),text=f'Type {ctx.prefix}help [command] for more info about specific command')
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
            embed.add_field(name="Description",value=command['help'])
            await ctx.send(embed=embed)
        else:
            await ctx.send("Nope")

    @commands.command()
    @commands.guild_only()
    async def suggest(self,ctx):
    	def check(msg):
    		return True if msg.author.id == ctx.author.id else False
    	channel = self.bot.get_channel(739526508137152633)
    	msg = await ctx.send('What is your suggestion title? (type "abort" to abort suggestion)')
    	title = await self.bot.wait_for('message',check=check)
    	await msg.delete()
    	if title.content.lower() == 'abort':
    		await ctx.send("Suggestion has been aborted")
    		await title.delete()
    		return
    	await title.delete()
    	msg = await ctx.send('What is the suggestion itself?')
    	description= await self.bot.wait_for('message',check=check)
    	await msg.delete()
    	await description.delete()
    	embed = discord.Embed(
    		title=f'Suggestion by {ctx.author}',
    		colour=discord.Colour.from_rgb(30,200,255),
    		timestamp=datetime.datetime.utcnow()
    	)
    	embed.add_field(name='Title',value=title.content)
    	embed.add_field(name="Description",value=description.content)
    	embed.set_footer(icon_url=ctx.author.avatar_url_as(static_format='png'),text=ctx.author)
    	suggest = await channel.send(embed=embed)
    	await suggest.add_reaction('\U0000274e')
    	await suggest.add_reaction('\U00002705')
    	await ctx.send("Suggestion posted!")

class Event(commands.Cog):
	def __init__(self,bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_command_error(self,ctx,err):
		if getattr(ctx.command,'on_error',None):
			return
		if isinstance(err,commands.CommandNotFound):
			pass
		elif isinstance(err,commands.ConversionError):
			await ctx.send(dir(err))
		elif isinstance(err,commands.MissingRequiredArgument):
			await ctx.send(f'Missing argument **{err.param.name}**')
		elif isinstance(err,commands.BadArgument):
			await ctx.send(err.args[0])
		elif isinstance(err,commands.PrivateMessageOnly):
			await ctx.send('You can only use this command on DM')
		elif isinstance(err,commands.NoPrivateMessage):
			await ctx.send("You can only use this command on Servers")
		elif isinstance(err,commands.DisabledCommand):
			await ctx.send('This command is currently disabled')
		elif isinstance(err,commands.TooManyArguments):
			await ctx.send('You gave too many argument!')
		elif isinstance(err,commands.CommandOnCooldown):
			minute,hour,second = 0,0,int(err.retry_after)
			if second > 60:
				minute += second // 60
				second = second%minute
			if minute > 60:
				hour += minute // 60
				minute = minute % hour
			await ctx.send(f"You need to wait **{hour}h {minute}m {second}s** to use the command again, command cooldown is **{err.cooldown.per}s** per **{err.cooldown.type.name.capitalize()}** for **{err.cooldown.rate}x**")
		else:
			raise err

def setup(bot):
    bot.add_cog(Guild(bot))
    bot.add_cog(Utils(bot))
    bot.add_cog(Event(bot))
    print("--Loaded all cogs--")