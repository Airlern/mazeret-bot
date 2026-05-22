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

    tur = TextInput(
        label="Mazeret Türü",
        placeholder="Sağlık / Aile / Şehir Dışı",
        required=True
    )

    bas = TextInput(
        label="Başlangıç Tarih & Saat",
        placeholder="22.05.2026 15:00",
        required=True
    )

    bit = TextInput(
        label="Bitiş Tarih & Saat",
        placeholder="23.05.2026 15:00",
        required=True
    )

    aciklama = TextInput(
        label="Açıklama",
        placeholder="Örn: Hastaneye gitmem gerekiyor",
        style=discord.TextStyle.paragraph,
        required=True
    )

    async def on_submit(self, interaction):

        kanal = bot.get_channel(ONAY_KANAL)

        embed = discord.Embed(title="Yeni Başvuru", color=discord.Color.orange())
        embed.add_field(name="Kullanıcı", value=interaction.user.mention, inline=False)
        embed.add_field(name="Tür", value=self.tur.value)
        embed.add_field(name="Başlangıç", value=self.bas.value)
        embed.add_field(name="Bitiş", value=self.bit.value)
        embed.add_field(name="Açıklama", value=self.aciklama.value, inline=False)

        view = OnayView(interaction.user, self.tur.value, self.bit.value)

        msg = await kanal.send(embed=embed, view=view)
        view.message = msg

        await interaction.response.send_message("Gönderildi", ephemeral=True)


# =========================
# BAŞVURU BUTONU
# =========================
class ButtonOnlyView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📝 Mazaret Oluştur",
        style=discord.ButtonStyle.green
    )
    async def btn(self, interaction, button):

        try:
            modal = MazaretModal()
            await interaction.response.send_modal(modal)
        except:
            await interaction.followup.send("Modal açılamadı, tekrar dene.", ephemeral=True)


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
        return discord.utils.get(interaction.user.roles, id=YETKILI_ROL)

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success)
    async def onay(self, interaction, button):

        if self.locked:
            return await interaction.response.send_message("Zaten sonuçlandı", ephemeral=True)

        if not self.yetkili(interaction):
            return await interaction.response.send_message("Yetki yok", ephemeral=True)

        self.locked = True

        role = interaction.guild.get_role(MAZERET_ROL)
        await self.user.add_roles(role)

        try:
            bitis_dt = datetime.strptime(self.bitis, "%d.%m.%Y %H:%M")
        except:
            return await interaction.response.send_message("Tarih hatalı", ephemeral=True)

        aktif.append({
            "user": self.user.id,
            "guild": interaction.guild.id,
            "role": MAZERET_ROL,
            "bitis": bitis_dt
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
# OTOMATİK ROL SİLME
# =========================
async def kontrol():
    await bot.wait_until_ready()
    while not bot.is_closed():

        now = datetime.now()

        for i in aktif[:]:
            try:
                if now >= i["bitis"]:

                    guild = bot.get_guild(i["guild"])
                    if not guild:
                        continue

                    user = await guild.fetch_member(i["user"])
                    role = guild.get_role(i["role"])

                    if role and role in user.roles:
                        await user.remove_roles(role)

                    aktif.remove(i)

            except Exception as e:
                print("ROL SİLME HATA:", e)

        await asyncio.sleep(30)


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
# BOT BAŞLANGIÇ
# =========================
@bot.event
async def on_ready():
    print("Bot aktif")
    bot.loop.create_task(kontrol())


bot.run(TOKEN)