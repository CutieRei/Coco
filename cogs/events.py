import discord
import datetime
from discord.ext import commands


class Events(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self,payload):
        if payload.message_id == 764018918527467520:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            await member.add_roles(guild.get_role(764015974357532684))

    @commands.Cog.listener()
    async def on_member_join(self,member):
        await member.send(f'Welcome to {member.guild.name} make sure to register using `.register <your growid>` if you are a guild member')

    @commands.Cog.listener()
    async def on_message(self,msg):
        if msg.content.lower() == self.bot.command_prefix+"bbc":
            await msg.channel.send("https://www.bbc.co.uk/")
        if msg.content in [f"<@{self.bot.user.id}>",f"<@!{self.bot.user.id}>"]:
            await msg.channel.send(f"My prefix is `{self.bot.command_prefix}`")
    
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
        elif isinstance(err,commands.NotOwner):
            embed.description = "You're not the bot owners, and you can't execute this command"
            await ctx.send(embed=embed)
        elif isinstance(err, commands.CheckFailure):
            return
        else:
            embed.description = "Unregistered error has occured!"
            await ctx.send(embed=embed)
            raise err

def setup(bot):
    bot.add_cog(Events(bot))
    print('(EVENTS) Loaded cog')