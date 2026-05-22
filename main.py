import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput

import os
TOKEN = os.getenv("TOKEN")

# Kanal ID'leri
MAZERET_KANAL = 1505330270398578857
ONAY_KANAL = 1505330270696505465
LOG_KANAL = 1505330270696505467

# Yetkili rolü
YETKILI_ROL = 1505330268204961816

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# ==========================
# MAZERET FORMU
# ==========================

class MazaretModal(Modal, title="Mazaret Başvurusu"):

    neden = TextInput(
        label="Mazaret Nedeni",
        placeholder="Mazaretinizi yazın",
        style=discord.TextStyle.paragraph
    )

    tarih = TextInput(
        label="Tarih",
        placeholder="22.05.2026"
    )

    saat = TextInput(
        label="Saat",
        placeholder="14:30"
    )

    async def on_submit(self, interaction: discord.Interaction):

        onay_kanali = bot.get_channel(ONAY_KANAL)

        embed = discord.Embed(
            title="Yeni Mazaret Başvurusu",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Kullanıcı",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Neden",
            value=self.neden.value,
            inline=False
        )

        embed.add_field(
            name="Tarih",
            value=self.tarih.value,
            inline=True
        )

        embed.add_field(
            name="Saat",
            value=self.saat.value,
            inline=True
        )

        await onay_kanali.send(
            embed=embed,
            view=OnayView(interaction.user)
        )

        await interaction.response.send_message(
            "Mazaretiniz gönderildi.",
            ephemeral=True
        )


# ==========================
# BAŞVURU BUTONU
# ==========================

class BasvuruView(View):

    @discord.ui.button(
        label="📝 Mazaret Gönder",
        style=discord.ButtonStyle.green
    )
    async def basvur(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            MazaretModal()
        )


# ==========================
# ONAY / RED
# ==========================

class OnayView(View):

    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici


    def yetkili_mi(self, interaction):

        return discord.utils.get(
            interaction.user.roles,
            id=YETKILI_ROL
        )


    @discord.ui.button(
        label="Onayla",
        style=discord.ButtonStyle.success
    )
    async def onayla(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.yetkili_mi(interaction):

            return await interaction.response.send_message(
                "Yetkiniz yok.",
                ephemeral=True
            )

        log = bot.get_channel(LOG_KANAL)

        embed = discord.Embed(
            title="Mazaret Onaylandı",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Kullanıcı",
            value=self.kullanici.mention
        )

        embed.add_field(
            name="Onaylayan",
            value=interaction.user.mention
        )

        await log.send(embed=embed)

        try:
            await self.kullanici.send(
                "Mazaretiniz onaylandı."
            )
        except:
            pass

        await interaction.response.send_message(
            "Mazaret onaylandı."
        )


    @discord.ui.button(
        label="Reddet",
        style=discord.ButtonStyle.danger
    )
    async def reddet(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.yetkili_mi(interaction):

            return await interaction.response.send_message(
                "Yetkiniz yok.",
                ephemeral=True
            )

        log = bot.get_channel(LOG_KANAL)

        embed = discord.Embed(
            title="Mazaret Reddedildi",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Kullanıcı",
            value=self.kullanici.mention
        )

        embed.add_field(
            name="Reddeden",
            value=interaction.user.mention
        )

        await log.send(embed=embed)

        try:
            await self.kullanici.send(
                "Mazaretiniz reddedildi."
            )
        except:
            pass

        await interaction.response.send_message(
            "Mazaret reddedildi."
        )


# ==========================
# KUR KOMUTU
# ==========================

@bot.command()
async def kur(ctx):

    kanal = bot.get_channel(MAZERET_KANAL)

    embed = discord.Embed(
        title="Mazaret Sistemi",
        description="Mazaret oluşturmak için aşağıdaki butona basın.",
        color=discord.Color.blue()
    )

    embed.set_image(
        url="https://media.discordapp.net/attachments/1023953372467966023/1507325447183274154/ChatGPT_Image_22_May_2026_13_12_39.png?ex=6a117db7&is=6a102c37&hm=609b7c3d8ae933f003298d4a8894e9dc0db77fe54602b41d0f0043e6dfa6cfd0&=&format=webp&quality=lossless&width=1163&height=930"
    )

    await kanal.send(
        embed=embed,
        view=BasvuruView()
    )

    await ctx.send("Kurulum tamamlandı.")


# ==========================
# BOT HAZIR
# ==========================

@bot.event
async def on_ready():
    print(f"{bot.user} aktif!")


bot.run(TOKEN)