import discord
from discord.ext import commands
import random

# Privileged Gateway Intents
intents = discord.Intents().all()

# Set prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

async def on_ready(ctx):
    print(f'We have logged in as {bot.user}, enjoy!')

@bot.command()
async def test(ctx, *args):
    arguments = ' '.join(args)
    await ctx.send(arguments)

# Basic converter
@bot.command()
async def add(ctx, arg1: int, arg2: int):
    await ctx.send(f'{arg1} + {arg2} = {arg1+arg2}')

# Function annotation
def to_upper(argument):
    return argument.upper()

@bot.command()
async def up(ctx, *, content: to_upper):
    await ctx.send(content)

# Custom converter
class Slapper(commands.Converter):
    async def convert(self, ctx, argument):
        to_slap = random.choice(ctx.guild.members)
        return f'{ctx.author} slapped {to_slap} because *{argument}*'
    
@bot.command()
async def slap(ctx, *, reason: Slapper):
    await ctx.send(reason)

# Discord converter
@bot.command()
async def joined(ctx, *, member: discord.Member):
    await ctx.send(f'{member} joined on {member.joined_at}')

class MemberRoles(commands.MemberConverter):
    async def convert(self, ctx, argument):
        member = await super().convert(ctx, argument)
        return [role.name for role in member.roles[1:]]  # Remove everyone role
    
@bot.command()
async def roles(ctx, *, member: MemberRoles):
    await ctx.send(f'The role of {member} is ' + ', '.join(member))

bot.run('bot_token')