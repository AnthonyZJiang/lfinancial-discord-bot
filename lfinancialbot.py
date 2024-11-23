from dotenv import load_dotenv
from typing import Final
import os

import discord
from discord import app_commands, channel

from config import load_config, save_config

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

VERSION: Final[str] = 'MK-I-0.1.1'


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        self.config = load_config()
        self.channels_to_relay: dict[int, channel.TextChannel] = {}
        self.target_channel: channel.TextChannel = None
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    def save_config(self):
        save_config(self.config)

    def initialise(self):
        if "admin_ids" not in self.config:
            self.config["admin_ids"] = []
        for channel_id in self.config['channels_to_relay']:
            self.channels_to_relay[channel_id] = self.get_channel(channel_id)
        self.target_channel = self.get_channel(
            self.config['target_channel']) if self.config['target_channel'] else None

    async def on_message(self, message: discord.Message):
        if message.author.id == self.user.id:
            # ignore messages from the bot itself
            return
        await self.relay_message(message)

    async def relay_message(self, message: discord.Message):
        if self.target_channel is None:
            return
        if message.channel.id not in self.channels_to_relay.keys():
            return
        await self.target_channel.send(f'{message.author.name}: \n{message.content}')
        for attachment in message.attachments:
            await self.target_channel.send(attachment.url)

    async def setup_hook(self):
        if not self.config['test_mode']:
            return
        for guild_id in self.config['test_guild_ids']:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)


    async def check_admin(self, interaction: discord.Interaction):
        if not interaction.user.id in self.config['admin_ids']:
            await interaction.response.send_message('你没有权限使用此命令。')
            return False
        return True


if __name__ == '__main__':
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(intents=intents)

    @client.event
    async def on_ready():
        client.initialise()
        print(f'Logged in as {client.user} (ID: {client.user.id})')
        print('------')


    @client.tree.command()
    async def relay_info(interaction: discord.Interaction):
        """显示当前转播频道和目标频道"""
        if not await client.check_admin(interaction):
            return
        msg = f'已设置转播频道: \n{"\n".join([f"{c.guild.name} : {c.name}" for k, c in client.channels_to_relay.items()]) if len(client.channels_to_relay) else "无"}'
        msg += f'\n\n已设置转播目标频道: \n{f"{client.target_channel.guild.name} : {client.target_channel.name}" if client.target_channel else "无"}'
        msg += f'\n\n机器人版本: {VERSION}'
        await interaction.response.send_message(msg)


    @client.tree.command()
    async def reset_relay(interaction: discord.Interaction):
        """重置转播设置"""
        if not await client.check_admin(interaction):
            return
        client.channels_to_relay.clear()
        client.target_channel = None
        client.config['channels_to_relay'] = []
        client.config['target_channel'] = 0
        await interaction.response.send_message('已重置转播设置。')
        client.save_config()


    @client.tree.command()
    @app_commands.describe(y_or_n='输入"y"开始转播当前频道, 输入"n"结束转播。')
    async def relay_this(interaction: discord.Interaction, y_or_n: str):
        """设置当前频道是否转播"""
        if not await client.check_admin(interaction):
            return
        if y_or_n.lower() == 'y':
            if interaction.channel_id in client.channels_to_relay.keys():
                await interaction.response.send_message('当前频道已经在转播列表中。')
                return
            client.channels_to_relay[interaction.channel_id] = interaction.channel
            client.config['channels_to_relay'].append(interaction.channel_id)
            await interaction.response.send_message('小人物金融机器人开始转播当前频道的消息。')
        elif y_or_n.lower() == 'n':
            if interaction.channel_id not in client.channels_to_relay:
                await interaction.response.send_message('当前频道不在转播列表中。')
                return
            client.channels_to_relay.pop(interaction.channel_id)
            client.config['channels_to_relay'].remove(interaction.channel_id)
            await interaction.response.send_message('小人物金融机器人停止转播当前频道的消息。')
        else:
            await interaction.response.send_message('输入错误，请输入"y"或"n"。')
            return
        client.save_config()


    @client.tree.command()
    @app_commands.describe(y_or_n='输入"y"将消息转播到当前频道, 输入"n"结束转播。')
    async def relay_to(interaction: discord.Interaction, y_or_n: str):
        """设置是否转播消息到当前频道"""
        if not await client.check_admin(interaction):
            return
        if y_or_n.lower() == 'y':
            if interaction.channel == client.target_channel:
                await interaction.response.send_message('当前频道已经是转播目标频道。')
                return
            client.target_channel = interaction.channel
            client.config['target_channel'] = client.target_channel.id
            await interaction.response.send_message('小人物金融机器人将会把消息转播到当前频道。')
        elif y_or_n.lower() == 'n':
            client.target_channel = None
            client.config['target_channel'] = 0
            await interaction.response.send_message('小人物金融机器人已停止转播消息。')
        else:
            await interaction.response.send_message('输入错误，请输入"y"或"n"。')
            return
        client.save_config()

    client.run(TOKEN)
