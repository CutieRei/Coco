import discord
import aiosqlite as sql
import datetime
from discord.ext import commands
import growtopia


class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def change(self,ctx,user:discord.User,*,name):
        async with sql.connect('./db/data.sql') as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(user.id,)) as cursor:
                data = await cursor.fetchone()
                growuser = growtopia.Growuser(data,ctx.author,db)
                if growuser.growid.lower() == name.lower():
                	await ctx.send("New name can't be old name")
                	return
                old_name = growuser.growid
                await growuser.set_name(name=name)
                await ctx.send(f'Successfully changed name from **{old_name}** to **{growuser.growid}** for **{user}**')


    @commands.command()
    async def infolist(self,ctx):
        async with sql.connect('./db/data.sql') as db:
            async with db.execute('SELECT id,growid,rank FROM members ORDER BY rank ASC') as cursor:
                lis = await cursor.fetchall()
                ranks = ["leader","co-leaders","elders","members"] 
                for i in lis:
                    if i[-1].lower() == "leader":
                        coco = lis.pop(lis.index(i))
                        lis.insert(0, coco)
                lis = [f"{self.bot.get_user(i[0])} - {i[1]}[{i[2]}]" for i in lis]
                embed = discord.Embed(title="List of data from members", description="\n".join(lis),colour=self.bot.colour, timestamp=datetime.datetime.utcnow())
                embed.set_footer(text=str(len(lis))+" Members total")
                await ctx.send(embed=embed)
    
    @property
    def log(self):
        return self.bot.get_channel(749082254482997298)
    
    @commands.command()
    async def members(self,ctx):
        async with sql.connect('./db/data.sql') as db:
            async with db.execute('SELECT * FROM members') as c:
                members = await c.fetchall()
                embed = discord.Embed(title='Member list',colour=self.bot.color, timestamp=datetime.datetime.utcnow(), description="\n".join([f"**{count+1}.** Name:** {self.bot.get_user(members[count][0])}** GrowID: **{members[count][1]}**" for count in range(0,len(members)-1)]))
                await ctx.send(embed=embed)
    
    @commands.command()
    @commands.is_owner()
    async def remove(self,ctx,user: discord.User):
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(user.id,)) as c:
                res = await c.fetchone()
                if not res:
                    await ctx.send("I cannot find them")
                    return
                await db.execute("DELETE FROM members WHERE id = ?",(user.id,))
                await db.commit()
                await ctx.send("Done!")
    
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def deduct(self,ctx,points:int,member: discord.Member):
        """
        Remove points from member
        """
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(member.id,)) as c:
                user = await c.fetchone()
                if not user:
                    await ctx.send("That member isn't registered")
                    return
                if points > user[2]:
                    points = user[2]
                await db.execute("UPDATE members SET contribution = contribution - ? WHERE id = ?",(points,member.id,))
                await db.commit()
                embed = discord.Embed(
                title="Successfully deducted",
                description=f"Successfully deducted **{points}** from {member}({user[1]})",
                timestamp=datetime.datetime.utcnow(),
                colour=self.bot.color
                )
                embed.set_thumbnail(url=member.avatar_url_as(static_format='png'))
                embed.set_footer(icon_url=ctx.author.avatar_url_as(static_format='png'),text="v1")
                await ctx.send(embed=embed)
                
    
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
            await self.log.send(embed=discord.Embed(description=f"{ctx.author} Registered as {name} at {datetime.datetime.utcnow()}", colour=ctx.author.colour))
            await ctx.send("Registered!")
            role = ctx.guild.get_role(739374593029963786)
            await ctx.author.add_roles(role)

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
            colour=self.bot.colour
            )
            embed.set_footer(icon_url=ctx.guild.me.avatar_url,text="v1")
            embed.set_thumbnail(url=user.avatar_url_as(static_format='png'))
            embed.add_field(name="Points",value=data[2],inline=False)
            embed.add_field(name="GrowID",value=data[1],inline=False)
            embed.add_field(name="ID",value=data[0],inline=False)
            embed.add_field(name="Rank",value=data[4] or 'No rank')
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
                title=f"Successfully added!",
                timestamp=datetime.datetime.utcnow(),
                colour=self.bot.colour    
                )
                embed.add_field(name="Points",value=amount)
                embed.add_field(name="GrowID",value=user[1])
                embed.set_footer(icon_url=ctx.guild.me.avatar_url,text="v1")
                embed.set_thumbnail(url=member.avatar_url_as(static_format='png'))
                await self.log.send(embed=discord.Embed(description=f"{ctx.author} Added {amount} to {member} with the growid of {growid}", colour=self.bot.colour))
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
                title="Leaderboard",
                timestamp=datetime.datetime.utcnow(),
                colour=self.bot.colour    
                )
                count = 1
                for id,name,contri,wls,rank in users:
                    embed.add_field(name=str(count)+f". {self.bot.get_user(id)}",value=f"GrowID: **{name}**"+"\n"+f"Points: **{contri}**",inline=False)
                    count += 1
                embed.set_footer(icon_url=ctx.guild.me.avatar_url,text="v1")
                await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    @commands.guild_only()
    async def reset(self,ctx):
        """
        Reset the points
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
            await ctx.send("Points has been restarted!")
            await msg.delete()
        else:
            await ctx.send("Okay then")
            await msg.delete()
        await self.log.send(embed=discord.Embed(description=f"{ctx.author} Reseted the points at {datetime.datetime.utcnow()}",colour=self.bot.colour))

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
        """
        Check member balance
        """
        person = ctx.author
        wls = 0
        growid = None
        if member and ctx.author.guild_permissions.manage_channels:
            person = member
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(person.id,)) as c:
                wls = await c.fetchone()
                if not wls:
                    await ctx.send("I cannot find anything...")
                    return
                growid = wls[1]
        if member and ctx.author.guild_permissions.manage_channels:
            person = member
        embed = discord.Embed(
        title=f"{person.display_name} Balance",
        description=f"**{wls[3]} World Locks**",
        colour=self.bot.colour,
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
        """
        Add money to a member
        """
        async with sql.connect("db/data.sql") as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(member.id,)) as c:
                user = await c.fetchone()
                if not user:
                    await ctx.send("Im sorry but, that member haven't registered")
                    return
                await db.execute("UPDATE members SET wls = wls + ? WHERE id = ?",(amount,member.id,))
                await db.commit()
                await self.log.send(embed=discord.Embed(description=f"{ctx.author} Gave {member} **{amount}Wls** to their balance",colour=self.bot.colour))
                await ctx.send("Success!")

    @commands.command(aliases=["draw"])
    @commands.is_owner()
    @commands.guild_only()
    async def withdraw(self,ctx,amount:int,member:discord.Member):
        """
        Remove currency on member balance
        """
        async with sql.connect('db/data.sql') as db:
            async with db.execute("SELECT * FROM members WHERE id = ?",(member.id,)) as c:
                user = await c.fetchone()
                if amount > user[3]:
                    amount = user[3]
                if user:
                    await db.execute("UPDATE members SET wls = wls - ? WHERE id = ?",(amount,member.id,))
                    await db.commit()
                    embed = discord.Embed(title="Success",description=f"Successfully removed **{amount}Wls** from {member}",timestamp=datetime.datetime.utcnow(),colour=self.bot.colour)
                    embed.add_field(name='GrowID',value=user[1])
                    await ctx.send(embed=embed)
                    return
                await ctx.send('I cannot find them.')

    @commands.command()
    async def search(self,ctx,*,name):
        async with sql.connect("db/data.sql") as db:
            """
            Search member by growid
            """
            async with db.execute("SELECT * FROM members") as c:
                members = await c.fetchall()
                for id,growid,point,wls,rank in members:
                    if growid.lower() == name.lower():
                        embed = discord.Embed(title=f"Founded {name}", description=f"Successfully founded members with name of {name}", timestamp=datetime.datetime.utcnow(),colour=self.bot.colour)
                        embed.add_field(name="Name",value=self.bot.get_user(id))
                        embed.add_field(name="ID",value=id)
                        embed.add_field(name="Points",value=point)
                        member = ctx.guild.get_member(id)
                        embed.set_thumbnail(url=member.avatar_url_as(static_format='png'))
                        embed.set_footer(icon_url=member.avatar_url_as(static_format='png'),text=member)
                        await ctx.send(embed=embed)
                        return
            await ctx.send(f"Cannot find members with the name of {name}")

    @commands.command()
    @commands.is_owner()
    async def promote(self,ctx,rank_name,*,name):
        """
        Promote a member(use this instead of manual name changes)
        """
        async with sql.connect('db/data.sql') as db:
            async with db.execute("SELECT * FROM members") as c:
                members = await c.fetchall()
                member = None
                for id,growid,point,wls,rank in members:
                    if name.lower() == growid.lower():
                        member = (id,growid,point,wls,rank)
                if not member:
                    await ctx.send("I cant find that member, perhaps you make a typo")
                    return

                embed = discord.Embed(
                    title=f"Promoted!",
                    description=f"Successfully promoted {member[1]} to {rank_name}",
                    timestamp=datetime.datetime.utcnow(),
                    colour=self.bot.colour
                )
                embed.set_thumbnail(url=self.bot.get_user(member[0]).avatar_url_as(static_format='png'))
                await ctx.send(embed=embed)
                await db.execute('UPDATE members SET rank = ? WHERE id = ?',(rank_name,member[0],))
                await db.commit()

def setup(bot):
    bot.add_cog(Guild(bot))
    print('(GUILD) Loaded cog')