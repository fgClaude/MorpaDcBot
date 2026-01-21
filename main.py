import discord
from discord.ext import commands
import os
import subprocess
import tempfile
import time
import asyncio
import shutil
from get_handler import HttpGetter # import your handler

# Bot settings
TOKEN = "token"
PREFIX = "."

# Intent settings
intents = discord.Intents.default()
intents.message_content = True

# Bot creation
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Modules
getter = HttpGetter()

# FILE PATHS - EDIT THESE
DUMPER_PATH = "/storage/emulated/0/Documents/Morpa_Bot/dumper.lua"
WORK_DIR = "/storage/emulated/0/Documents/Morpa_Bot/dumps"

# Create work dir
if not os.path.exists(WORK_DIR):
    os.makedirs(WORK_DIR)

@bot.event
async def on_ready():
    print(f'bot is up as {bot.user}')
    print(f'dumper path: {DUMPER_PATH}')
    print(f'work dir: {WORK_DIR}')
    await bot.change_presence(activity=discord.Game(name=".help | Lua Dumper"))

def check_dumper():
    """check dumper file"""
    if not os.path.exists(DUMPER_PATH):
        return False, f"cant find dumper at: {DUMPER_PATH}"
    
    if not os.path.isfile(DUMPER_PATH):
        return False, f"dumper is not a file: {DUMPER_PATH}"
    
    try:
        with open(DUMPER_PATH, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if "larry" in first_line.lower() or "lua" in first_line.lower():
                return True, "dumper ready"
            else:
                return True, "dumper has weird content but ok"
    except:
        return True, "dumper file exists"

def run_lua_dumper(input_file, output_file):
    """run lua dumper script"""
    try:
        cmd = ["lua", DUMPER_PATH, input_file, output_file]
        print(f"running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORK_DIR
        )
        
        if result.returncode == 0:
            return True, "dump good"
        else:
            error_msg = result.stderr or result.stdout or "unknown error"
            return False, f"lua fail ({result.returncode}): {error_msg[:200]}"
            
    except subprocess.TimeoutExpired:
        return False, "timeout... took way too long"
    except FileNotFoundError:
        return False, "no lua found. do 'pkg install lua' bro"
    except Exception as e:
        return False, f"system rip: {str(e)}"

@bot.command(name='dump')
async def dump_command(ctx):
    """dumps lua stuff"""
    if not ctx.message.attachments:
        embed = discord.Embed(
            title="dump cmd",
            description="usage: .dump\n\nattach any file bro",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        return
    
    try:
        dumper_ok, dumper_msg = check_dumper()
        if not dumper_ok:
            await ctx.send(f"nah {dumper_msg}")
            return
        
        msg = await ctx.send("wait im downloadin the file...")
        attachment = ctx.message.attachments[0]
        
        unique_id = f"{ctx.author.id}_{int(time.time())}"
        # Orijinal uzantıyı korumak için:
        file_ext = os.path.splitext(attachment.filename)[1]
        input_file = os.path.join(WORK_DIR, f"input_{unique_id}{file_ext}")
        output_file = os.path.join(WORK_DIR, f"output_{unique_id}{file_ext}")
        
        file_data = await attachment.read()
        with open(input_file, 'wb') as f:
            f.write(file_data)
        
        await msg.edit(content="downloadin done... runnin dumper now...")
        success, result = run_lua_dumper(input_file, output_file)
        
        if not success:
            if os.path.exists(input_file): os.remove(input_file)
            await msg.edit(content=f"dump failed rip:\n```{result}```")
            return
        
        if os.path.exists(output_file):
            # Dosya metin ise içeriği oku, değilse direkt gönder
            try:
                with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                    dumped_content = f.read()
                
                if len(dumped_content) > 1900 or len(dumped_content) == 0:
                     await msg.edit(content="dump finished sending file now")
                     await ctx.send(file=discord.File(output_file, filename=f"DUMPED_{attachment.filename}"))
                else:
                     await msg.edit(content=f"dump finished here u go\n```\n{dumped_content}\n```")
            except:
                await msg.edit(content="dump finished sending file now")
                await ctx.send(file=discord.File(output_file, filename=f"DUMPED_{attachment.filename}"))
            
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(output_file): os.remove(output_file)
        else:
            await msg.edit(content="rip couldnt find output file")
            
    except Exception as e:
        await ctx.send(f"dang error:\n```{str(e)}```")

@bot.command(name='get')
async def get_command(ctx, *, text=None):
    """gets stuff from url using roblox headers"""
    if text is None:
        await ctx.send("bro give me a url to get")
        return
    
    msg = await ctx.send("wait im gettin content from link...")
    
    try:
        content, error = getter.get_from_text(text)
        
        if error:
            await msg.edit(content=f"nah {error}")
            return
        
        if len(content) > 1900:
            filename = f"response_{int(time.time())}.txt"
            temp_path = os.path.join(WORK_DIR, filename)
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            await msg.edit(content="got it... file too big so here u go")
            await ctx.send(file=discord.File(temp_path))
            os.remove(temp_path)
        else:
            await msg.edit(content=f"got it successfully\n```\n{content}\n```")
            
    except Exception as e:
        await msg.edit(content=f"rip something went wrong: {str(e)}")

@bot.command(name='setup')
async def setup_command(ctx):
    """check if setup is ok"""
    checks = []
    try:
        result = subprocess.run(['lua', '-v'], capture_output=True, text=True)
        checks.append(f"lua: {result.stdout.split()[1]}")
    except:
        checks.append("no lua installed (pkg install lua)")
    
    dumper_ok, dumper_msg = check_dumper()
    checks.append(f"dumper: {dumper_msg}")
    
    if os.path.exists(WORK_DIR):
        checks.append(f"work dir: {WORK_DIR}")
    else:
        checks.append(f"no work dir: {WORK_DIR}")
    
    embed = discord.Embed(
        title="setup check",
        description="\n".join(checks),
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.command(name='testdumper')
async def test_dumper_command(ctx):
    """test dumper with small script"""
    test_code = '-- test script\nlocal msg = "hello"\nprint(msg)\nreturn "done"'
    test_file = os.path.join(WORK_DIR, "test_input.lua")
    output_file = os.path.join(WORK_DIR, "test_output.lua")
    
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    success, result = run_lua_dumper(test_file, output_file)
    
    if success and os.path.exists(output_file):
        await ctx.send("test good dumper is workin")
        os.remove(test_file)
        os.remove(output_file)
    else:
        await ctx.send(f"test failed rip: {result}")

@bot.command(name='help')
async def help_command(ctx):
    """help msg"""
    embed = discord.Embed(
        title="lua dumper bot",
        description="dump or get any files",
        color=0x00ff00
    )
    embed.add_field(name=".dump", value="dumps attached file (any extension)", inline=False)
    embed.add_field(name=".get", value="gets content from a url", inline=False)
    embed.add_field(name=".setup", value="checks if setup ok", inline=True)
    embed.add_field(name=".testdumper", value="test the dumper", inline=True)
    embed.add_field(name=".help", value="shows this msg", inline=True)
    
    embed.set_footer(text=f"dumper: {os.path.basename(DUMPER_PATH)}")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("wrong cmd... check .help")
    else:
        await ctx.send(f"error bro: ```{str(error)[:200]}```")

if __name__ == "__main__":
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("error: edit the token first bro")
        exit(1)
    bot.run(TOKEN)
