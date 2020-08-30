import discord, aiosqlite, datetime, inspect,uuid, random
from discord.ext import commands,tasks
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
            try:
                await ctx.author.edit(nick=f"「{name}」{ctx.author.name}")
            except:
                pass
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

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def add(self,ctx,amount:int,member: discord.Member):
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
            if msg.author.id == ctx.author.id:
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
        if member and ctx.author.guild_permissions.manage_channels:
            person = member
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

    @commands.command(aliases=["depo","dep"])
    @commands.guild_only()
    @commands.is_owner()
    async def deposit(self,ctx,amount:int,*,member: discord.Member):
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

    @commands.command(aliases=["draw"])
    @commands.is_owner()
    @commands.guild_only()
    async def withdraw(self,ctx,amount:int,member:discord.Member):
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

    @commands.command()
    async def search(self,ctx,*,name):
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members") as c:
                members = await c.fetchall()
                for id,growid,point,wls in members:
                    if growid.lower() == name.lower():
                        embed = discord.Embed(title=f"Founded {name}", description=f"Successfully founded members with name of {name}", timestamp=datetime.datetime.utcnow(),colour=ctx.author.colour)
                        embed.add_field(name="GrowID",value=growid)
                        embed.add_field(name="ID",value=id)
                        embed.add_field(name="Contribution",value=point)
                        member = ctx.guild.get_member(id)
                        embed.set_thumbnail(url=member.avatar_url_as(static_format='png'))
                        embed.set_footer(icon_url=member.avatar_url_as(static_format='png'),text=member)
                        await ctx.send(embed=embed)
                        return
            await ctx.send(f"Cannot find members with the name of {name}")

class Utils(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.loop.start()
    
    @commands.command()
    async def ping(self,ctx):
        """
        Shows the bot latency
        """
        ping = self.bot.latency*1000
        colour = None
        if ping > 300:
            colour = discord.Colour.red
        elif ping > 200:
            colour = discord.Colour.gold
        else:
            colour = discord.Colour.green
        embed = discord.Embed(
        title='Pong!',
        colour=colour,
        timestamp=datetime.datetime.utcnow(),
        description=f"My ping is {ping}ms"
        )
        embed.set_footer(icon_url=ctx.guild.me.avatar_url,text=random.choice(["I won!","Hey?","Why hello there","Sup!","Ping Pong, i win!","Hey there bud"]))
        await ctx.send(embed=embed)
    
    @commands.command()
    async def uptime(self,ctx):
        """
        Shows the bot uptime
        """
        second,minute,hour,day = int((datetime.datetime.utcnow()-self.bot.uptime).second),0,0,0
        if second > 60:
            minute += second//60
            second = second%60
        if minute > 60:
            hour += minute//60
            minute = minute%60
        if hour > 24:
            day += hour//24
            hour = hour%24
        embed = discord.Embed(
        title="Bot Uptime!",
        colour=ctx.author.colour,
        timestamp=datetime.datetime.utcnow()
        )
    
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
    
    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def dc(self,ctx):
        """
        disconnect the bot
        """
        self.loop.stop()
        await ctx.send("Disconnected!")
        await self.bot.logout()
    
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
            cmds = dict({})
            for name,cog in self.bot.cogs.items():
                cmds[name] = []
            cmds['No Modules'] = []
            for command in self.bot.commands:
                if not command.cog_name:
                    cmds['No Modules'].append(command.name)
                    continue
                cmds[command.cog_name].append(command.name)
            for cog,cmd in cmds.items():
                embed.add_field(name=cog,value=",".join(cmd),inline=False)
            
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
	async def on_ready(self):
	    self.bot.reload_extension("category")
	    print("[Bot] Ready!")
	
	@commands.Cog.listener()
	async def on_command_error(self,ctx,err):
		embed = discord.Embed(
		title=f"{err} Error",
		timestamp=datetime.datetime.utcnow(),
		colour=discord.Colour.from_rgb(255,70,0)
		)
		embed.set_footer(icon_url=ctx.author.avatar_url_as(static_format='png'),text="an error occurred")
		if getattr(ctx.command,'on_error',None):
			return
		if isinstance(err,commands.CommandNotFound):
			pass
		elif isinstance(err,commands.ConversionError):
			await ctx.send(dir(err))
		elif isinstance(err,commands.MissingRequiredArgument):
			embed.description = f'Missing argument **{err.param.name}**'
			await ctx.send(embed=embed)
		elif isinstance(err,commands.BadArgument):
			embed.description = ",".join(err.args[0])
			await ctx.send(embed=embed)
		elif isinstance(err,commands.PrivateMessageOnly):
			embed.description = 'You can only use this command on DM'
			await ctx.send(embed=embed)
		elif isinstance(err,commands.NoPrivateMessage):
			embed.description = "You can only use this command on Servers"
			await ctx.send(embed=embed)
		elif isinstance(err,commands.DisabledCommand):
			embed.description = 'This command is currently disabled'
		elif isinstance(err,commands.TooManyArguments):
			embed.description = 'You gave too many argument!'
			await ctx.send(embed=embed)
		elif isinstance(err,commands.CommandOnCooldown):
			minute,hour,second = 0,0,int(err.retry_after)
			if second > 60:
				minute += second // 60
				second = second%minute
			if minute > 60:
				hour += minute // 60
				minute = minute % hour
			embed.description = f"You need to wait **{hour}h {minute}m {second}s** to use the command again, command cooldown is **{err.cooldown.per}s** per **{err.cooldown.type.name.capitalize()}** for **{err.cooldown.rate}x**"
			await ctx.send(embed=embed)
		else:
			raise err

def setup(bot):
    if bot.ready_once:
        print("[Cogs] Reloading cogs")
    else:
        print("[Cogs] Loading cogs")
        bot.ready_once = True
    bot.add_cog(Guild(bot))
    bot.add_cog(Utils(bot))
    bot.add_cog(Event(bot))
    print("[Cogs] Loaded all cogs")