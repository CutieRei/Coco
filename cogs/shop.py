from discord.ext import commands
import discord
import datetime
import json
import aiosqlite as sql
import uuid

class Shop(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @staticmethod
    def rand_color():
        return [random.randint(0,255) for i in range(0,3)]
    
    @commands.group(invoke_without_command=True)
    async def redeem(self,ctx):
        """
        Redeem group commands, show list of redeemable items you can get
        """
        user = None
        async with sql.connect('./db/data.sql') as db:
            async with db.execute("SELECT contribution FROM members WHERE id = ?",(ctx.author.id,)) as cursor:
                user = await cursor.fetchone()
                if not user:
                    await ctx.send("You're not registered")
                    return
        with open("./prize/prize.json","r") as file:
            items = json.load(file)
            embed = discord.Embed(title="Exchange",description="Exchange your points into item provided by the **GROWSTOCKS** guild leader",timestamp=datetime.datetime.utcnow(),colour=self.bot.color)
            embed.set_author(name="Shop",icon_url="https://cdn.discordapp.com/attachments/748776346385252422/760356650724491304/20200929_112547.jpg")
            item_list = []
            count = 1
            for item,price in items.items():
                item_list.append(f"**#{count}** | {item} for {price} Points")
                count += 1
            embed.add_field(name="Item list",value="\n".join(item_list))
            embed.set_footer(text=f"You have {user[0]} Points",icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @redeem.command()
    async def list(self,ctx):
        """
        Get the numbers of pending requests based of the author
        """
        async with sql.connect('./db/data.sql') as db:
            async with db.execute('SELECT * FROM redeem WHERE user = ? ORDER BY time ASC LIMIT 3',(ctx.author.id,)) as cursor:
                data = await cursor.fetchall()
                embed = discord.Embed(title="List of pending requests",description="Show list of pending requests",colour=self.bot.color)
                for bit in data:
                    print(bit)
                    time = datetime.datetime.utcnow()-(datetime.datetime.strptime(bit[3],'%Y-%m-%d %H:%M:%S.%f'))
                    d,h,m,s = int(time.days),0,0,int(time.seconds)
                    if s >= 60:
                        m += s//60
                        s = s%60
                    if m >= 60:
                        h += m//60
                        m = m%60
                    if d >= 1:
                        h = h%24
                    embed.add_field(name=bit[4],value=f"Requested **{d}d** **{h}h** **{m}m** **{s}s** ago")
                await ctx.send(embed=embed)

    @redeem.command()
    async def buy(self,ctx,index:int):
        """
        Exchange points for items, note that this will create a exchange requests and can be rejected
        """
        contri = None
        async with sql.connect('./db/data.sql') as db:
            async with db.execute('SELECT contribution FROM members WHERE id = ?',(ctx.author.id,)) as cursor:
                contri = await cursor.fetchone()
                if not contri:
                    await ctx.send("You're not registered")
                    return
                contri = contri[0]
        with open("./prize/prize.json",'r') as file:
            req_id = str(uuid.uuid4())
            items = json.load(file)
            if index > len(items):
                await ctx.send("That item doesn't exists")
                return
            price = items[list(items)[index-1]]
            if contri < price:
                await ctx.send("You don't have enough points")
                return
            contri -= price
            with open("./configs/config.json",'r') as file1:
                cfg = json.load(file1)
                recipient = self.bot.get_user(cfg.get("recipient"))
                embed = discord.Embed(title='Redeem Requests',description="Unapproved redeem requests",timestamp=datetime.datetime.utcnow(),colour=discord.Colour.light_grey())
                embed.set_footer(text=f'Requests by {ctx.author}',icon_url=ctx.author.avatar_url)
                embed.add_field(name='Requests ID',value=req_id,inline=False)
                embed.add_field(name="Item",value=list(items)[index-1])
                msg = await recipient.send(embed=embed)
                async with sql.connect('./db/data.sql') as db:
                    await db.execute("INSERT INTO redeem VALUES (?,?,?,?,?)",(msg.id,req_id,ctx.author.id,datetime.datetime.utcnow(),list(items)[index-1],))
                    await db.execute("UPDATE members SET contribution = ? WHERE id = ?",(contri,ctx.author.id,))
                    await db.commit()
                    await ctx.send(f'Your requests have been added {ctx.author.mention}, please wait for further notice')
    @commands.command()
    @commands.is_owner()
    async def accept(self,ctx,id):
        """
        Accept a requests with the given ID
        """
        recipient = None
        with open('./configs/config.json','r') as file:
            cfg = json.load(file)
            recipient = self.bot.get_user(cfg.get('recipient'))
        async with sql.connect('./db/data.sql') as db:
            async with db.execute('SELECT * FROM redeem WHERE id = ?',(id,)) as cursor:
                data = await cursor.fetchone()
                if not data:
                    await ctx.send('That requests doesn\'t exists')
                    return
                msg = await recipient.fetch_message(data[0])
                embed = msg.embeds[0]
                embed.colour = discord.Colour.green()
                embed.description = "Approved redeem requests"
                await msg.edit(embed=embed)
                await db.execute('DELETE FROM redeem WHERE message = ?',(msg.id,))
                user = self.bot.get_user(data[2])
                await db.commit()
                await ctx.send('Done!')
                await user.send(f"Your request for **{embed.fields[1].value}** is approved and is already delivered")

    @commands.command()
    @commands.is_owner()
    async def reject(self,ctx,id):
        """
        Reject a requests with the given ID
        """
        recipient = None
        with open('./configs/config.json','r') as file:
            cfg = json.load(file)
            recipient = self.bot.get_user(cfg.get('recipient'))
        async with sql.connect('./db/data.sql') as db:
            async with db.execute('SELECT * FROM redeem WHERE id = ?',(id,)) as cursor:
                data = await cursor.fetchone()
                if not data:
                    await ctx.send('That requests doesn\'t exists')
                    return
                msg = await recipient.fetch_message(data[0])
                embed = msg.embeds[0]
                embed.colour = discord.Colour.red()
                embed.description = "Rejected redeem requests"
                await msg.edit(embed=embed)
                await db.execute('DELETE FROM redeem WHERE message = ?',(msg.id,))
                user = self.bot.get_user(data[2])
                await db.commit()
                await ctx.send("Done!")
                await user.send(f"Your request for **{embed.fields[1].value}** is rejected")

    @commands.command()
    @commands.is_owner()
    async def get_id(self,ctx,message_id:int):
        async with sql.connect('./db/data.sql') as db:
            async with db.execute('SELECT id FROM redeem WHERE message = ?',(message_id,)) as cursor:
                id = await cursor.fetchone()
                if not id:
                    await ctx.send("Message is not a requests message")
                    return
                await ctx.send(id[0])
                await ctx.message.add_reaction("✅")

    @commands.group(invoke_without_command=True)
    async def config(self,ctx):
        await ctx.send('Missing Subcommands')

    @config.command()
    @commands.is_owner()
    async def recipient(self,ctx,new_id:int):
        with open('./configs/config.json','r+') as file:
            cfg = json.load(file)
            cfg['recipient'] = new_id
            file.seek(0)
            json.dump(cfg,file)
            await ctx.send('Updated recipient id!')

def setup(bot):
    bot.add_cog(Shop(bot))
    print('(SHOP) Loaded cog')