import discord, asyncio, os
from discord.ext import commands
from discord.ui import View, Modal, TextInput
from datetime import datetime

TOKEN = os.getenv("TOKEN")

MAZERET_KANAL = 1505330270398578857
ONAY_KANAL = 1505330270696505465
LOG_KANAL = 1505330270696505467
YETKILI_ROL = 1505330268204961816
MAZERET_ROL = 1505330268129722506

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

aktif = []

class MazaretModal(Modal, title="Mazaret"):

    tur = TextInput(label="Tür")
    bas = TextInput(label="Başlangıç (gün.ay.yıl saat)")
    bit = TextInput(label="Bitiş (gün.ay.yıl saat)")
    aciklama = TextInput(label="Açıklama", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction):

        kanal = bot.get_channel(ONAY_KANAL)

        embed = discord.Embed(title="Yeni Başvuru", color=discord.Color.orange())
        embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=False)
        embed.add_field(name="Tür", value=self.tur.value)
        embed.add_field(name="Başlangıç", value=self.bas.value)
        embed.add_field(name="Bitiş", value=self.bit.value)
        embed.add_field(name="Açıklama", value=self.aciklama.value, inline=False)

        await kanal.send(embed=embed, view=OnayView(interaction.user, self.tur.value, self.bit.value))

        await interaction.response.send_message("Gönderildi", ephemeral=True)


class BasvuruView(View):

    @discord.ui.button(
        label="📝 Mazaret Oluştur",
        style=discord.ButtonStyle.green
    )
    async def btn(self, interaction, button):

        embed = discord.Embed(
            title="📋 Mazaret Başvurusu",
            description="Başvuru yapmak için aşağıdaki butona tıkla",
            color=discord.Color.green()
        )

        embed.set_image(url="https://media.discordapp.net/attachments/1023953372467966023/1507325447183274154/ChatGPT_Image_22_May_2026_13_12_39.png?ex=6a117db7&is=6a102c37&hm=609b7c3d8ae933f003298d4a8894e9dc0db77fe54602b41d0f0043e6dfa6cfd0&=&format=webp&quality=lossless&width=1163&height=930")

        await interaction.response.send_message(
            embed=embed,
            view=ButtonOnlyView(),
            ephemeral=True
        )

class OnayView(View):

    def __init__(self, user, tur, bitis):
        super().__init__(timeout=None)
        self.user = user
        self.tur = tur
        self.bitis = bitis

    def yetkili(self, interaction):
        return discord.utils.get(interaction.user.roles, id=YETKILI_ROL)

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success)
    async def onay(self, interaction, button):

        if not self.yetkili(interaction):
            return await interaction.response.send_message("Yetki yok", ephemeral=True)

        role = interaction.guild.get_role(MAZERET_ROL)
        await self.user.add_roles(role)

        aktif.append({
    "user": self.user.id,
    "guild": interaction.guild.id,
    "role": MAZERET_ROL,
    "bitis": datetime.strptime(self.bitis, "%d.%m.%Y %H:%M")
})

log = bot.get_channel(LOG_KANAL)

embed = discord.Embed(title="Onaylandı", color=discord.Color.green())
embed.add_field(name="Kullanıcı", value=self.user.mention)
embed.add_field(name="Tür", value=self.tur)
embed.add_field(name="Onaylayan", value=interaction.user.mention)

await log.send(embed=embed)

try:
    await self.user.send("✅ Mazaretin ONAYLANDI.")
except:
    pass

await interaction.response.send_message("Onaylandı")

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger)
    async def red(self, interaction, button):

        if not self.yetkili(interaction):
            return await interaction.response.send_message("Yetki yok", ephemeral=True)

        log = bot.get_channel(LOG_KANAL)

        embed = discord.Embed(title="Reddedildi", color=discord.Color.red())
        embed.add_field(name="Kullanıcı", value=self.user.mention)
        embed.add_field(name="Tür", value=self.tur)
        embed.add_field(name="Reddeden", value=interaction.user.mention)

        await log.send(embed=embed)

        await interaction.response.send_message("Reddedildi")


async def kontrol():
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = datetime.now()
        for i in aktif[:]:
            if now >= i["bitis"]:
                guild = bot.get_guild(i["guild"])
                user = guild.get_member(i["user"])
                role = guild.get_role(i["role"])
                if user and role:
                    await user.remove_roles(role)
                aktif.remove(i)
        await asyncio.sleep(60)


@bot.command()
async def kur(ctx):
    kanal = bot.get_channel(MAZERET_KANAL)
    embed = discord.Embed(title="Mazaret Sistemi", description="Başvuru yap", color=discord.Color.blue())
    await kanal.send(embed=embed, view=BasvuruView())
    await ctx.send("Kuruldu")


@bot.event
async def on_ready():
    print("Bot aktif")
    bot.loop.create_task(kontrol())


bot.run(TOKEN)