import discord
from discord import app_commands
from discord.ext import commands
import random
import urllib.parse
import asyncio
import yt_dlp

# ─── CONFIG ───────────────────────────────────────────────────────────────────
import os
TOKEN = os.environ.get('TOKEN')
# ──────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='..', intents=intents)

# ─── RESPUESTAS "EZ" ──────────────────────────────────────────────────────────
EZ_RESPONSES = [
    "TU MAMA es ez, malcriado.",
    "Ez? Preguntale a tu mama si le parece ez criarte.",
    "Tan ez como la vida de tu mama sin vos.",
    "Tu mama te pario y ESO fue lo mas dificil que hizo, gg.",
    "Ez lo dice el que no sabe lo que se esforzó tu mama en mandarte al colegio.",
    "Tu mama sudo mas planchando tu ropa que vos jugando, crack.",
    "Ez? Tu mama te haria llorar en 5 minutos, un poco de respeto.",
    "Decile 'ez' a tu mama a ver como te va.",
    "Tu mama diria que nada es ez, ella te conoce bien.",
    "Ez el que habla, pero tu mama se parte el lomo por vos todos los dias.",
    "Muy facil para alguien cuya mama todavia le lava la ropa.",
    "EZ no existe cuando tu mama esta en la ecuacion, mostro.",
]

# ─── READY ────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Slash commands registrados: {len(synced)}')
    except Exception as e:
        print(f'Error registrando comandos: {e}')

# ─── DETECTAR "EZ" ────────────────────────────────────────────────────────────
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    palabras = message.content.lower().split()
    if 'ez' in palabras:
        await message.reply(random.choice(EZ_RESPONSES))
    await bot.process_commands(message)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def mod_embed(color, titulo, campos):
    embed = discord.Embed(title=titulo, color=color)
    for nombre, valor, inline in campos:
        embed.add_field(name=nombre, value=valor, inline=inline)
    import datetime
    embed.timestamp = datetime.datetime.utcnow()
    return embed

# ─── BAN ──────────────────────────────────────────────────────────────────────
@bot.tree.command(name='ban', description='Banea a un usuario del servidor')
@app_commands.describe(usuario='Usuario a banear', razon='Razon del ban')
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, usuario: discord.Member, razon: str = 'Sin razon especificada'):
    if not usuario.is_bannable:
        return await interaction.response.send_message('No puedo banear a ese usuario. Puede tener un rol superior al mio.', ephemeral=True)
    await usuario.ban(reason=razon)
    embed = mod_embed(0xff0000, 'Usuario baneado', [
        ('Usuario', usuario.mention, True),
        ('Moderador', interaction.user.mention, True),
        ('Razon', razon, False),
    ])
    await interaction.response.send_message(embed=embed)

# ─── KICK ─────────────────────────────────────────────────────────────────────
@bot.tree.command(name='kick', description='Expulsa a un usuario del servidor')
@app_commands.describe(usuario='Usuario a expulsar', razon='Razon del kick')
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, usuario: discord.Member, razon: str = 'Sin razon especificada'):
    if not usuario.is_bannable:
        return await interaction.response.send_message('No puedo expulsar a ese usuario.', ephemeral=True)
    await usuario.kick(reason=razon)
    embed = mod_embed(0xff8800, 'Usuario expulsado', [
        ('Usuario', usuario.mention, True),
        ('Moderador', interaction.user.mention, True),
        ('Razon', razon, False),
    ])
    await interaction.response.send_message(embed=embed)

# ─── TIMEOUT ──────────────────────────────────────────────────────────────────
@bot.tree.command(name='timeout', description='Pone en timeout a un usuario')
@app_commands.describe(usuario='Usuario', minutos='Duracion en minutos', razon='Razon')
@app_commands.default_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, usuario: discord.Member, minutos: int, razon: str = 'Sin razon especificada'):
    import datetime
    if minutos < 1 or minutos > 40320:
        return await interaction.response.send_message('El tiempo debe ser entre 1 y 40320 minutos.', ephemeral=True)
    duracion = datetime.timedelta(minutes=minutos)
    await usuario.timeout(duracion, reason=razon)
    embed = mod_embed(0xffcc00, 'Timeout aplicado', [
        ('Usuario', usuario.mention, True),
        ('Duracion', f'{minutos} minutos', True),
        ('Moderador', interaction.user.mention, True),
        ('Razon', razon, False),
    ])
    await interaction.response.send_message(embed=embed)

# ─── UNTIMEOUT ────────────────────────────────────────────────────────────────
@bot.tree.command(name='untimeout', description='Quita el timeout a un usuario')
@app_commands.describe(usuario='Usuario')
@app_commands.default_permissions(moderate_members=True)
async def untimeout(interaction: discord.Interaction, usuario: discord.Member):
    await usuario.timeout(None)
    await interaction.response.send_message(f'Se quito el timeout a **{usuario.display_name}**.')

# ─── WARN ─────────────────────────────────────────────────────────────────────
@bot.tree.command(name='warn', description='Advierte a un usuario via DM')
@app_commands.describe(usuario='Usuario', razon='Razon')
@app_commands.default_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, usuario: discord.Member, razon: str):
    try:
        await usuario.send(f'Has recibido una advertencia en **{interaction.guild.name}**.\nRazon: {razon}')
    except Exception:
        pass
    embed = mod_embed(0xffaa00, 'Advertencia emitida', [
        ('Usuario', usuario.mention, True),
        ('Moderador', interaction.user.mention, True),
        ('Razon', razon, False),
    ])
    await interaction.response.send_message(embed=embed)

# ─── CLEAR ────────────────────────────────────────────────────────────────────
@bot.tree.command(name='clear', description='Elimina mensajes del canal')
@app_commands.describe(cantidad='Cantidad de mensajes (1-100)')
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, cantidad: int):
    if cantidad < 1 or cantidad > 100:
        return await interaction.response.send_message('La cantidad debe ser entre 1 y 100.', ephemeral=True)
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=cantidad)
    await interaction.followup.send(f'Se eliminaron {len(deleted)} mensajes.', ephemeral=True)

# ─── SLOWMODE ─────────────────────────────────────────────────────────────────
@bot.tree.command(name='slowmode', description='Activa o desactiva el slowmode')
@app_commands.describe(segundos='0 para desactivar, maximo 21600')
@app_commands.default_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, segundos: int):
    if segundos < 0 or segundos > 21600:
        return await interaction.response.send_message('El valor debe ser entre 0 y 21600.', ephemeral=True)
    await interaction.channel.edit(slowmode_delay=segundos)
    msg = 'Slowmode desactivado.' if segundos == 0 else f'Slowmode activado: {segundos} segundos entre mensajes.'
    await interaction.response.send_message(msg)

# ─── LOCK ─────────────────────────────────────────────────────────────────────
@bot.tree.command(name='lock', description='Bloquea el canal para que nadie pueda escribir')
@app_commands.default_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message('Canal bloqueado. Nadie puede escribir.')

# ─── UNLOCK ───────────────────────────────────────────────────────────────────
@bot.tree.command(name='unlock', description='Desbloquea el canal')
@app_commands.default_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=None)
    await interaction.response.send_message('Canal desbloqueado.')

# ─── UNBAN ────────────────────────────────────────────────────────────────────
@bot.tree.command(name='unban', description='Desbanea a un usuario por su ID')
@app_commands.describe(userid='ID del usuario a desbanear')
@app_commands.default_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, userid: str):
    try:
        user = await bot.fetch_user(int(userid))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f'Usuario **{user}** desbaneado correctamente.')
    except Exception:
        await interaction.response.send_message('No se pudo desbanear. Verifica que el ID sea correcto.', ephemeral=True)

# ─── USERINFO ─────────────────────────────────────────────────────────────────
@bot.tree.command(name='userinfo', description='Muestra informacion de un usuario')
@app_commands.describe(usuario='Usuario (opcional, por defecto vos mismo)')
@app_commands.default_permissions(moderate_members=True)
async def userinfo(interaction: discord.Interaction, usuario: discord.Member = None):
    target = usuario or interaction.user
    roles = [r.name for r in target.roles if r.name != '@everyone']
    embed = discord.Embed(title=f'Informacion de {target}', color=0x5865f2)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name='ID', value=target.id, inline=True)
    embed.add_field(name='Apodo', value=target.nick or 'Ninguno', inline=True)
    embed.add_field(name='Cuenta creada', value=discord.utils.format_dt(target.created_at, style='R'), inline=True)
    embed.add_field(name='Se unio al servidor', value=discord.utils.format_dt(target.joined_at, style='R'), inline=True)
    embed.add_field(name='Bot', value='Si' if target.bot else 'No', inline=True)
    embed.add_field(name='Roles', value=', '.join(roles) if roles else 'Ninguno', inline=False)
    import datetime
    embed.timestamp = datetime.datetime.utcnow()
    await interaction.response.send_message(embed=embed)

# ─── IMAGEN ───────────────────────────────────────────────────────────────────
@bot.tree.command(name='imagen', description='Genera una imagen con IA')
@app_commands.describe(prompt='Descripcion de la imagen a generar')
async def imagen(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    seed = random.randint(1, 99999)
    encoded = urllib.parse.quote(prompt)
    url = f'https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}'
    import datetime
    embed = discord.Embed(title='Imagen generada con IA', description=f'Prompt: {prompt}', color=0x5865f2)
    embed.set_image(url=url)
    embed.set_footer(text=f'Pedido por {interaction.user}')
    embed.timestamp = datetime.datetime.utcnow()
    await interaction.followup.send(embed=embed)

# ─── PING ────────────────────────────────────────────────────────────────────
@bot.command(name='ping')
async def ping(ctx):
    latencia = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latencia: {latencia}ms')

# ─── SAY ─────────────────────────────────────────────────────────────────────
@bot.command(name='say')
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, mensaje: str):
    await ctx.message.delete()
    await ctx.send(mensaje)


# ─── MUSICA ───────────────────────────────────────────────────────────────────
queues = {}

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if not queue:
        return
    url, title = queue.pop(0)
    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
    ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    await ctx.send(f'Reproduciendo: **{title}**')

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, busqueda: str):
    if not ctx.author.voice:
        return await ctx.send('Tenes que estar en un canal de voz.')
    canal = ctx.author.voice.channel
    if ctx.voice_client is None:
        await canal.connect()
    elif ctx.voice_client.channel != canal:
        await ctx.voice_client.move_to(canal)

    await ctx.send(f'Buscando: **{busqueda}**...')

    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        try:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(f'ytsearch:{busqueda}', download=False))
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info.get('title', 'Desconocido')
        except Exception as e:
            return await ctx.send(f'No se pudo encontrar la cancion: {e}')

    queue = get_queue(ctx.guild.id)
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        queue.append((url, title))
        await ctx.send(f'Agregado a la cola: **{title}**')
    else:
        queue.append((url, title))
        await play_next(ctx)

@bot.command(name='skip', aliases=['s'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send('Cancion saltada.')
    else:
        await ctx.send('No hay nada reproduciendose.')

@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send('Pausado.')
    else:
        await ctx.send('No hay nada reproduciendose.')

@bot.command(name='resume', aliases=['r'])
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send('Reanudado.')
    else:
        await ctx.send('No hay nada pausado.')

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        get_queue(ctx.guild.id).clear()
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send('Musica detenida y bot desconectado.')
    else:
        await ctx.send('El bot no esta en un canal de voz.')

@bot.command(name='cola', aliases=['queue', 'q'])
async def cola(ctx):
    queue = get_queue(ctx.guild.id)
    if not queue:
        return await ctx.send('La cola esta vacia.')
    lista = '\n'.join([f'{i+1}. {title}' for i, (_, title) in enumerate(queue)])
    await ctx.send(f'Cola de reproduccion:\n{lista}')

# ─── RUN ──────────────────────────────────────────────────────────────────────
bot.run(TOKEN)
