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


# =========================
# MODAL
# =========================
class MazaretModal(Modal, title="Mazaret"):

    tur = TextInput(label="Mazeret Türü", placeholder="Sağlık / Aile / Şehir Dışı", required=True)
    bas = TextInput(label="Başlangıç", placeholder="22.05.2026 15:00", required=True)
    bit = TextInput(label="Bitiş", placeholder="23.05.2026 15:00", required=True)
    aciklama = TextInput(label="Açıklama", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction):

        try:
            bas_dt = datetime.strptime(self.bas.value, "%d.%m.%Y %H:%M")
            bit_dt = datetime.strptime(self.bit.value, "%d.%m.%Y %H:%M")
        except:
            return await interaction.response.send_message(
                "❌ Tarih formatı yanlış (22.05.2026 15:00)",
                ephemeral=True
            )

        kanal = bot.get_channel(ONAY_KANAL)

        embed = discord.Embed(title="Yeni Başvuru", color=discord.Color.orange())
        embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=False)
        embed.add_field(name="Tür", value=self.tur.value)
        embed.add_field(name="Başlangıç", value=self.bas.value)
        embed.add_field(name="Bitiş", value=self.bit.value)
        embed.add_field(name="Açıklama", value=self.aciklama.value, inline=False)

        view = OnayView(interaction.user, self.tur.value, bit_dt)

        msg = await kanal.send(embed=embed, view=view)
        view.message = msg

        await interaction.response.send_message("Gönderildi", ephemeral=True)


# =========================
# BAŞVURU BUTONU
# =========================
class ButtonOnlyView(View):

    @discord.ui.button(label="📝 Mazaret Oluştur", style=discord.ButtonStyle.green)
    async def btn(self, interaction, button):

        embed = discord.Embed(
            title="📋 Mazaret Başvurusu",
            description="Butona basarak başvuru yapabilirsin",
            color=discord.Color.green()
        )

        embed.set_image(url="https://media.discordapp.net/attachments/1023953372467966023/1507325447183274154/ChatGPT_Image_22_May_2026_13_12_39.png?ex=6a117db7&is=6a102c37&hm=609b7c3d8ae933f003298d4a8894e9dc0db77fe54602b41d0f0043e6dfa6cfd0&=&format=webp&quality=lossless&width=1163&height=930")

        await interaction.response.send_modal(MazaretModal())


# =========================
# ONAY SİSTEMİ
# =========================
class OnayView(View):

    def __init__(self, user, tur, bitis):
        super().__init__(timeout=None)
        self.user = user
        self.tur = tur
        self.bitis = bitis
        self.locked = False
        self.message = None

    def yetkili(self, interaction):
        return any(role.id == YETKILI_ROL for role in interaction.user.roles)

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success)
    async def onay(self, interaction, button):

        if self.locked:
            return await interaction.response.send_message("Zaten sonuçlandı", ephemeral=True)

        if not self.yetkili(interaction):
            return await interaction.response.send_message("Yetki yok", ephemeral=True)

        self.locked = True

        role = interaction.guild.get_role(MAZERET_ROL)
        await self.user.add_roles(role)

        # 🔥 KRİTİK FIX: timestamp
        aktif.append({
            "user": self.user.id,
            "guild": interaction.guild.id,
            "role": MAZERET_ROL,
            "bitis": self.bitis.timestamp()
        })

        log = bot.get_channel(LOG_KANAL)

        embed = discord.Embed(title="Onaylandı", color=discord.Color.green())
        embed.add_field(name="Kullanıcı", value=self.user.mention)
        embed.add_field(name="Tür", value=self.tur)
        embed.add_field(name="Onaylayan", value=interaction.user.mention)

        await log.send(embed=embed)

        try:
            await self.user.send("✅ Mazaret ONAYLANDI")
        except:
            pass

        for item in self.children:
            item.disabled = True

        if self.message:
            await self.message.edit(view=self)

        await interaction.response.send_message("Onaylandı", ephemeral=True)

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger)
    async def red(self, interaction, button):

        if self.locked:
            return await interaction.response.send_message("Zaten sonuçlandı", ephemeral=True)

        if not self.yetkili(interaction):
            return await interaction.response.send_message("Yetki yok", ephemeral=True)

        self.locked = True

        log = bot.get_channel(LOG_KANAL)

        embed = discord.Embed(title="Reddedildi", color=discord.Color.red())
        embed.add_field(name="Kullanıcı", value=self.user.mention)
        embed.add_field(name="Tür", value=self.tur)
        embed.add_field(name="Reddeden", value=interaction.user.mention)

        await log.send(embed=embed)

        try:
            await self.user.send("❌ Mazaret REDDEDİLDİ")
        except:
            pass

        for item in self.children:
            item.disabled = True

        if self.message:
            await self.message.edit(view=self)

        await interaction.response.send_message("Reddedildi", ephemeral=True)


# =========================
# SÜRE SİSTEMİ (FIXLİ + DEBUG)
# =========================
async def kontrol():
    await bot.wait_until_ready()
    print("⏰ Süre sistemi aktif")

    while not bot.is_closed():
        now = datetime.now().timestamp()

        for i in aktif[:]:

            if now >= i["bitis"]:

                guild = bot.get_guild(i["guild"])
                if not guild:
                    continue

                try:
                    user = await guild.fetch_member(i["user"])
                    role = guild.get_role(i["role"])

                    if user and role:
                        await user.remove_roles(role)
                        print(f"✔ Rol silindi: {user}")

                except Exception as e:
                    print("❌ Hata:", e)

                aktif.remove(i)

        await asyncio.sleep(10)


# =========================
# KUR KOMUTU
# =========================
@bot.command()
async def kur(ctx):

    kanal = bot.get_channel(MAZERET_KANAL)

    embed = discord.Embed(
        title="Mazaret Sistemi",
        description="Başvuru yapmak için butona bas",
        color=discord.Color.blue()
    )

    await kanal.send(embed=embed, view=ButtonOnlyView())

    await ctx.send("Kuruldu")


# =========================
# BOT START
# =========================
@bot.event
async def on_ready():
    print(f"{bot.user} aktif")
    bot.loop.create_task(kontrol())


bot.run(TOKEN)