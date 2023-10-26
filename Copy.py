from datetime import datetime, timedelta
import discord
from discord.ext import commands
import aiomysql
import asyncio
import json


DB_HOST = 'host'
DB_USER = 'doadmin'
DB_PASS = 'Pass'
DB_NAME = 'defaultdb'

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)



####################################### Initialize the database connection pool #######################################
#-----------------------------------------------Call the init_db function-----------------------------------------------
async def init_db():
    global pool
    try:
        # Create a new connection pool
        pool = await aiomysql.create_pool(
            host=DB_HOST,
            port=111111,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            autocommit=True
        )

        # Acquire a connection from the pool
        async with pool.acquire() as conn:

            # Create a new cursor
            async with conn.cursor() as cur:
                # Drop the existing tables if they exist

                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS special_users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT UNIQUE,
                        user_type ENUM('King', 'Omega', 'Super')
                    );
                    """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS actions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT,
                        actor_id BIGINT,
                        action_type ENUM('report', 'boost', 'super_boost'),
                        report_type VARCHAR(255) NULL,
                        report_section ENUM('Sexual', 'Spam', 'Hateful', 'Fraud') NULL,
                        reason TEXT NULL,
                        votes JSON,
                        report_timestamp TIMESTAMP NULL,
                        cemented BOOLEAN DEFAULT FALSE,
                        hidden BOOLEAN DEFAULT FALSE,
                        UNIQUE (user_id, actor_id, action_type, report_type)
                    );
                """)

                # Create reputation table if it does not exist
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS reputation (
                        user_id BIGINT PRIMARY KEY,
                        reputation INT,
                        total_reports INT,
                        total_boosts INT,
                        total_super_boosts INT
                    );
                    """)

                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_attributes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT UNIQUE,
                        is_banned BOOLEAN DEFAULT FALSE,
                        banned_by BIGINT NULL,
                        ban_reason TEXT NULL,
                        is_hidden BOOLEAN DEFAULT FALSE,
                        super_hidden BOOLEAN DEFAULT FALSE,
                        hidden_by BIGINT NULL,
                        hidden_reason TEXT NULL,
                        is_famous BOOLEAN DEFAULT FALSE,
                        famous_by BIGINT NULL,
                        famous_reason TEXT NULL,
                        is_devil BOOLEAN DEFAULT FALSE,
                        devil_by BIGINT NULL,
                        devil_reason TEXT NULL,
                        is_angel BOOLEAN DEFAULT FALSE,
                        angel_by BIGINT NULL,
                        angel_reason TEXT NULL,
                        is_server_owner BOOLEAN DEFAULT FALSE,
                        owner_by BIGINT NULL,
                        owner_reason TEXT NULL,
                        is_server_admin BOOLEAN DEFAULT FALSE,
                        admin_by BIGINT NULL,

                    );
                """)

                # Commit the changes to the database
                await conn.commit()

    except Exception as e:
        # Print any errors that occur
        print(f"An error occurred: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    await init_db()



####################################### Admin Commands Secure ID based // Keep Hidden #################################
#---------------------------------------------------Moderation Checkers-------------------------------------------------

#King Checker
async def is_user_king(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_type FROM special_users WHERE user_id = %s
            """, (user_id,))
            result = await cur.fetchone()
            return result and result[0] == 'King'

#Omega checker
async def is_user_omega(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_type FROM special_users WHERE user_id = %s
            """, (user_id,))
            result = await cur.fetchone()
            return result is not None and result[0] == 'Omega'

# King OR Omega Checker
async def is_user_authorized(user_id):
    return await is_user_king(user_id) or await is_user_omega(user_id)

#Super checker
async def is_user_super(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_type FROM special_users WHERE user_id = %s
            """, (user_id,))
            result = await cur.fetchone()
            return result is not None and result[0] == 'Super'

# King OR Omega OR Super Checker
async def is_user_elevated(user_id):
    return await is_user_king(user_id) or await is_user_omega(user_id) or await is_user_super(user_id)



####################################### Admin Commands Secure ID based // Keep Hidden #################################
#---------------------------------------------------Moderation Fetchers-------------------------------------------------

#King Fetcher
async def fetch_king():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id FROM special_users WHERE user_type = 'King'
            """)
            result = await cur.fetchone()
            return result[0] if result else None

#Omega Fetcher
async def fetch_all_omegas():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id FROM special_users WHERE user_type = 'Omega'
            """)
            return await cur.fetchall()

# Super Fetcher
async def fetch_all_supers():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id FROM special_users WHERE user_type = 'Super'
            """)
            return await cur.fetchall()

# Omega and Super Fetcher
async def fetch_all_omegas_and_supers():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Fetch all Omegas
            await cur.execute("""
                SELECT user_id, user_type FROM special_users WHERE user_type = 'Omega'
            """)
            omegas = await cur.fetchall()

            # Fetch all Supers
            await cur.execute("""
                SELECT user_id, user_type FROM special_users WHERE user_type = 'Super'
            """)
            supers = await cur.fetchall()

            # Combine both lists
            return omegas + supers



####################################### Admin Commands Secure ID based // Keep Hidden #################################
#---------------------------------------------------King Only Commands-------------------------------------------------

#King Only to be used by owner // Change special_user_id to your ID
async def make_user_king(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Check if the user is already a King
            await cur.execute("""
                SELECT user_type
                FROM special_users
                WHERE user_id = %s
            """, (user_id,))
            result = await cur.fetchone()

            if result:
                if result[0] == 'King':
                    return "You are already a King."
                else:
                    await cur.execute("""
                        UPDATE special_users
                        SET user_type = 'King'
                        WHERE user_id = %s
                    """, (user_id,))
                    return "Your user type has been updated to King."
            else:
                await cur.execute("""
                    INSERT INTO special_users (user_id, user_type)
                    VALUES (%s, 'King')
                """, (user_id,))
                return "You have been made a King."
@bot.command(name="king", hidden=True)
async def make_me_king(ctx):
    special_user_id = 0

    if ctx.author.id == special_user_id:
        result_message = await make_user_king(ctx.author.id)
        await ctx.send(f"{result_message} Lets get to work : )")
    else:
        pass

#Turn others into omegas "Admins"
class ConfirmRankingView(discord.ui.View):
    def __init__(self, ctx, member, command_to_execute):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.member = member
        self.command_to_execute = command_to_execute

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        result_message = await self.command_to_execute(self.member.id)
        await interaction.response.send_message(result_message, ephemeral=True)
        self.stop()

    @discord.ui.button(label='Abort', style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Operation aborted.', ephemeral=True)
        self.stop()
async def make_user_omega(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Check if the user already exists in the special_users table
            await cur.execute("""
                SELECT user_type FROM special_users WHERE user_id = %s
            """, (user_id,))
            result = await cur.fetchone()

            if result:
                if result[0] == 'Omega':
                    return "This user is already an Omega."
                else:
                    await cur.execute("""
                        UPDATE special_users SET user_type = 'Omega' WHERE user_id = %s
                    """, (user_id,))
                    return "User type has been updated to Omega."
            else:
                await cur.execute("""
                    INSERT INTO special_users (user_id, user_type) VALUES (%s, 'Omega')
                """, (user_id,))
                return "The user has been made an Omega."
@bot.command(name="omega", hidden=True)
async def make_omega(ctx, member_id: int):
    if await is_user_king(ctx.author.id):
        if ctx.author.id == member_id:
            await ctx.send("I prevented you from de-ranking yourself silly")
            return

        member = await bot.fetch_user(member_id)

        embed = discord.Embed(
            title=f"Make {member.name} an Omega?",
            description="Confirm to make this user an Omega",
            color=0xFF5733
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        view = ConfirmRankingView(ctx, member, make_user_omega)
        await ctx.send(embed=embed, view=view)
    else:
        pass

#derank others from omegas "Admins"
async def derank_user_omega(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_type FROM special_users WHERE user_id = %s
            """, (user_id,))
            user_type_result = await cur.fetchone()

            if user_type_result is None:
                return 'not_exists'

            if user_type_result[0] != 'Omega':
                return 'not_omega'

            await cur.execute("""
                DELETE FROM special_users WHERE user_id = %s AND user_type = 'Omega'
            """, (user_id,))
            await conn.commit()

            # Check if the deletion was successful
            affected_rows = cur.rowcount
            return 'success' if affected_rows > 0 else 'failed'
@bot.command(name="unomega", hidden=True)
async def unomega(ctx, member_id: int):
    if await is_user_king(ctx.author.id):
        if member_id == ctx.author.id:
            await ctx.send("You cannot derank yourself.")
            return

        if not await is_user_omega(member_id):
            await ctx.send("That user is not an Omega.")
            return

        member = await bot.fetch_user(member_id)  # Fetch User object

        embed = discord.Embed(
            title=f"Derank {member.name}?",
            description="Confirm to remove this user from Omega rank",
            color=0xFF5733
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        view = ConfirmRankingView(ctx, member, derank_user_omega)
        await ctx.send(embed=embed, view=view)
    else:
        pass

#Omega Flip book
class OmegaPaginationView(discord.ui.View):
    def __init__(self, ctx, omega_list):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.omega_list = omega_list
        self.current_index = 0
        self.members = {}  # Store pre-fetched member data

    async def fetch_member(self, member_id):
        if member_id not in self.members:
            self.members[member_id] = await bot.fetch_user(member_id)
        return self.members[member_id]

    async def refresh_embed(self):
        member_id = self.omega_list[self.current_index]
        member = await self.fetch_member(member_id)
        embed = discord.Embed(title=f"Omega Users ({self.current_index+1}/{len(self.omega_list)})",
                              description=f"ID: {member.id}\nName: {member.name}",
                              color=0xFF5733)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.message.edit(embed=embed)

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.current_index > 0:
            self.current_index -= 1
        await self.refresh_embed()

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.current_index < len(self.omega_list) - 1:
            self.current_index += 1
        await self.refresh_embed()

    async def start(self):
        await self.refresh_embed()
@bot.command(name="omegas", hidden=True)
async def omegas(ctx):
    if await is_user_king(ctx.author.id):
        omega_list = [row[0] for row in await fetch_all_omegas()]

        if not omega_list:
            await ctx.send("No Omegas found.")
            return

        view = OmegaPaginationView(ctx, omega_list)
        view.message = await ctx.send("Fetching first Omega...", view=view)
        await view.start()


#Emergency purge of all omega (admins) and super (mods)
async def remove_all_except_king():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Count the number of users who are not Kings
            await cur.execute("""
                SELECT COUNT(*) FROM special_users WHERE user_type != 'King'
            """)
            initial_count = await cur.fetchone()

            # Perform the DELETE operation
            await cur.execute("""
                DELETE FROM special_users WHERE user_type != 'King'
            """)
            await conn.commit()

            # Count the number of users who are not Kings again
            await cur.execute("""
                SELECT COUNT(*) FROM special_users WHERE user_type != 'King'
            """)
            final_count = await cur.fetchone()

    # Check if the count dropped to zero, indicating successful deletion
    if initial_count[0] == 0:
        return "No users to remove."
    elif final_count[0] == 0:
        return f"Emergency purge completed. {initial_count[0]} users were removed."
    else:
        return "Emergency purge partially completed. Some users could not be removed."
class ConfirmPurgeView(discord.ui.View):
    def __init__(self, ctx, command_to_execute):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.command_to_execute = command_to_execute

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = await self.command_to_execute()
        await interaction.response.send_message(f"Command executed: {result}", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Abort", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Command aborted.", ephemeral=True)
        self.stop()
@bot.command(name="purge", hidden=True)
async def emergency_purge(ctx):
    if await is_user_king(ctx.author.id):
        embed = discord.Embed(
            title="Emergency Purge",
            description="This will remove all special users except for the King. Are you sure?",
            color=0xFF5733
        )

        view = ConfirmPurgeView(ctx, remove_all_except_king)
        await ctx.send(embed=embed, view=view)
    else:
        pass



####################################### Admin Commands Secure ID based // Keep Hidden #################################
#--------------------------------------------------- Admin Commands ---------------------------------------------------

#Turn others into Super "Mods"
async def make_user_super(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_type FROM special_users WHERE user_id = %s
            """, (user_id,))
            result = await cur.fetchone()

            if result:
                if result[0] == 'Super':
                    return "This user is already a Super."
                else:
                    await cur.execute("""
                        UPDATE special_users SET user_type = 'Super' WHERE user_id = %s
                    """, (user_id,))
                    return "User type has been updated to Super."
            else:
                await cur.execute("""
                    INSERT INTO special_users (user_id, user_type) VALUES (%s, 'Super')
                """, (user_id,))
                return "The user has been made a Super."
@bot.command(name="super", hidden=True)
async def make_super(ctx, member_id: int):
    if await is_user_authorized(ctx.author.id):  # Checks if the user is King or Omega
        if ctx.author.id == member_id:
            await ctx.send("You cannot de-rank yourself.")
            return

        # Check if target is Omega
        is_omega = await is_user_omega(member_id)
        if is_omega and not await is_user_king(ctx.author.id):  # If target is Omega and user is not King
            await ctx.send("You cannot de-rank an Omega into a Super.")
            return

        member = await bot.fetch_user(member_id)

        embed = discord.Embed(
            title=f"Make {member.name} a Super?",
            description="Confirm to make this user a Super",
            color=0xFF5733
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        view = ConfirmRankingView(ctx, member, make_user_super)  # Assuming ConfirmRankingView is defined elsewhere
        await ctx.send(embed=embed, view=view)
    else:
        pass


# derank others from Super "Omegas"
async def derank_user_super(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_type FROM special_users WHERE user_id = %s
            """, (user_id,))
            user_type_result = await cur.fetchone()

            if user_type_result is None:
                return 'not_exists'

            if user_type_result[0] != 'Super':
                return 'not_super'

            await cur.execute("""
                DELETE FROM special_users WHERE user_id = %s AND user_type = 'Super'
            """, (user_id,))
            await conn.commit()

            # Check if the deletion was successful
            affected_rows = cur.rowcount
            return 'success' if affected_rows > 0 else 'failed'
@bot.command(name="unsuper", hidden=True)
async def unsuper(ctx, member_id: int):
    if await is_user_authorized(ctx.author.id):
        if member_id == ctx.author.id:
            await ctx.send("You cannot derank yourself.")
            return

        if not await is_user_super(member_id):
            await ctx.send("That user is not a Super.")
            return

        member = await bot.fetch_user(member_id)

        embed = discord.Embed(
            title=f"Derank {member.name}?",
            description="Confirm to remove this user from Super rank",
            color=0xFF5733
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        view = ConfirmRankingView(ctx, member, derank_user_super)
        await ctx.send(embed=embed, view=view)
    else:
        pass


#Super Flip book
class SuperPaginationView(discord.ui.View):
    def __init__(self, ctx, super_list):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.super_list = super_list
        self.current_index = 0
        self.members = {}  # Store pre-fetched member data

    async def fetch_member(self, member_id):
        if member_id not in self.members:
            self.members[member_id] = await bot.fetch_user(member_id)
        return self.members[member_id]

    async def refresh_embed(self):
        member_id = self.super_list[self.current_index]
        member = await self.fetch_member(member_id)
        embed = discord.Embed(title=f"Super Users ({self.current_index+1}/{len(self.super_list)})",
                              description=f"ID: {member.id}\nName: {member.name}",
                              color=0xFF5733)
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.message.edit(embed=embed)

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.current_index > 0:
            self.current_index -= 1
        await self.refresh_embed()

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.current_index < len(self.super_list) - 1:
            self.current_index += 1
        await self.refresh_embed()

    async def start(self):
        await self.refresh_embed()
@bot.command(name="supers", hidden=True)
async def supers(ctx):
    if await is_user_authorized(ctx.author.id):  # Checks if user is King or Omega
        super_list = [row[0] for row in await fetch_all_supers()]

        if not super_list:
            await ctx.send("No Super users found.")
            return

        view = SuperPaginationView(ctx, super_list)
        view.message = await ctx.send("Fetching first Super user...", view=view)
        await view.start()


# Function to perform the Fallon Sword operation
async def fall_on_sword(initiator_id, target_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                DELETE FROM special_users WHERE user_id = %s OR user_id = %s
            """, (initiator_id, target_id))
            await conn.commit()


# Command to initiate the Fallon Sword operation
class ConfirmFallonSwordView(discord.ui.View):
    def __init__(self, ctx, initiator_id, target_id):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.initiator_id = initiator_id
        self.target_id = target_id

    async def fetch_user_info(self, user_id):
        return await bot.fetch_user(user_id)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await fall_on_sword(self.initiator_id, self.target_id)

        initiator_user = await self.fetch_user_info(self.initiator_id)
        target_user = await self.fetch_user_info(self.target_id)

        king_id = await fetch_king()
        if king_id:
            king_user = await bot.fetch_user(king_id)

            # Create the embeds
            embed1_title = initiator_user.name
            embed1_desc = f"{initiator_user.name} has fallen on their sword."
            embed1 = discord.Embed(title=embed1_title, description=embed1_desc)
            embed1.set_thumbnail(url=initiator_user.display_avatar.url)

            embed2_title = target_user.name
            embed2_desc = f"{target_user.name} was deranked by {initiator_user.name}."
            embed2 = discord.Embed(title=embed2_title, description=embed2_desc)
            embed2.set_thumbnail(url=target_user.display_avatar.url)

            # Send the message to the King
            await king_user.send(
                f"{initiator_user.name} has fallen on their sword to derank {target_user.name}",
                embeds=[embed1, embed2]
            )

        await interaction.response.send_message("Both you and the target have been deranked.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Abort", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Operation aborted.", ephemeral=True)
        self.stop()
@bot.command(name="corruption", hidden=True)
async def fall_on_sword_command(ctx, target_id: int):
    if await is_user_omega(ctx.author.id):
        if ctx.author.id == target_id:
            await ctx.send("You cannot target yourself.")
            return

        # Ensure that the target is also an Omega
        is_omega_target = await is_user_omega(target_id)
        if not is_omega_target:
            await ctx.send("The target must be an Omega.")
            return

        target = await bot.fetch_user(target_id)
        embed = discord.Embed(
            title="Fall on Sword",
            description=f"This will derank both you and {target.name}. Are you sure?",
            color=0xFF5733
        )
        view = ConfirmFallonSwordView(ctx, ctx.author.id, target_id)
        await ctx.send(embed=embed, view=view)
    else:
        pass


# Emergency derank of all Super users
async def remove_all_supers():
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Fetch the IDs of all Super users
            await cur.execute("""
                SELECT user_id FROM special_users WHERE user_type = 'Super'
            """)
            super_ids = [row[0] for row in await cur.fetchall()]

            # Count the number of users who are Supers
            initial_count = len(super_ids)

            # Perform the DELETE operation
            await cur.execute("""
                DELETE FROM special_users WHERE user_type = 'Super'
            """)
            await conn.commit()

            # Count the number of users who are Supers again
            await cur.execute("""
                SELECT COUNT(*) FROM special_users WHERE user_type = 'Super'
            """)
            final_count = await cur.fetchone()[0]

    # Prepare list of de-ranked Supers for the King
    super_list = "\n".join([str(super_id) for super_id in super_ids])

    return initial_count, final_count, super_list
@bot.command(name="deranksupers", hidden=True)
async def emergency_derank_supers(ctx):
    if await is_user_omega(ctx.author.id):
        embed = discord.Embed(
            title="Emergency Derank Supers",
            description="This will remove all Super users. Are you sure?",
            color=0xFF5733
        )

        view = ConfirmSuperDerankView(ctx, remove_all_supers)
        await ctx.send(embed=embed, view=view)
class ConfirmSuperDerankView(discord.ui.View):
    def __init__(self, ctx, command_to_execute):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.command_to_execute = command_to_execute

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        initial_count, final_count, super_list = await self.command_to_execute()
        await interaction.response.send_message(f"Command executed.", ephemeral=True)

        if initial_count == 0:
            await interaction.followup.send("No Super users to remove.")
        elif final_count == 0:
            await interaction.followup.send(f"Emergency deranking completed. {initial_count} Super users were removed.")
            await notify_omegas_and_king(self.ctx, super_list)
        else:
            await interaction.followup.send("Emergency deranking partially completed. Some Super users could not be removed.")

    @discord.ui.button(label="Abort", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Command aborted.", ephemeral=True)
        self.stop()


# Send a message to all Omegas and King when an Omega uses the emegency command
async def notify_omegas_and_king(ctx, super_list):
    omega_ids = [row[0] for row in await fetch_all_omegas()]
    king_ids = [row[0] for row in await fetch_king()]

    for omega_id in omega_ids:
        omega_user = await bot.fetch_user(omega_id)
        await omega_user.send(f"An emergency deranking of Super users has been initiated by {ctx.author.name}.")

    for king_id in king_ids:
        king_user = await bot.fetch_user(king_id)
        await king_user.send(f"An emergency deranking of Super users has been initiated by {ctx.author.name}.\nList of de-ranked Supers:\n{super_list}")



####################################### Admin Commands Secure ID based // Keep Hidden #################################
#---------------------------------------------------- Mod Commands ----------------------------------------------------

class ModCheckReportsView(discord.ui.View):
    def __init__(self, ctx, reports, member: discord.User, user_type):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.reports = list(reports)
        self.current_report_index = 0
        self.member = member
        self.user_type = user_type  # King, Omega, or Super

    def generate_embed(self):
        if not self.reports:  # Check if the reports list is empty
            embed = discord.Embed(
                title=f"No reports for {self.member.name}",
                description="This user has no reports left."
            )
            return embed
        report = self.reports[self.current_report_index]
        report_id, report_type, reason, votes_json, cemented = report  # Updated for cemented
        votes = json.loads(votes_json or '{}')
        agree_count = sum(1 for vote in votes.values() if vote == 'agree')
        disagree_count = sum(1 for vote in votes.values() if vote == 'disagree')


        cemented_status = 'Yes' if cemented else 'No'

        embed = discord.Embed(
            title=f"Mod View: Report against {self.member.name}",
            description=(
                f"Type: {report_type}\n\n"
                f"Reason: {reason}\n\n"
                f"Votes: {agree_count} agree, {disagree_count} disagree\n\n"
                f"Cemented: {cemented_status}"
            )
        )
        embed.set_thumbnail(url=self.member.display_avatar.url)
        footer_text = f"Report {self.current_report_index + 1} of {len(self.reports)}"
        embed.set_footer(text=footer_text)
        return embed

    async def update_cement_status(self, status: bool):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                report_id = self.reports[self.current_report_index][0]
                await cur.execute("UPDATE actions SET cemented = %s WHERE id = %s", (status, report_id))

                # Convert the tuple to a list for modification
                reports_list = self.reports

                # Update the self.reports list with new cement status
                report_id, report_type, reason, votes_json = reports_list[self.current_report_index]
                updated_report_tuple = (report_id, report_type, reason, votes_json, status)

                # Update the element and convert back to a tuple if needed
                reports_list[self.current_report_index] = updated_report_tuple

    async def delete_report_from_db(self):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                report_id = self.reports[self.current_report_index][0]
                await cur.execute("DELETE FROM actions WHERE id = %s", (report_id,))

    @discord.ui.button(label="Cement", style=discord.ButtonStyle.success)
    async def cement_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_type == 'King' or (self.user_type == 'Omega' and not await is_user_elevated(self.member.id)):
            await self.update_cement_status(True)
            await interaction.response.edit_message(embed=self.generate_embed())

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.danger)
    async def remove_report(self, interaction: discord.Interaction, button: discord.ui.Button):
        can_remove = False
        report = self.reports[self.current_report_index]
        report_id, report_type, reason, votes_json, cemented = report

        if self.user_type == 'King':
            can_remove = True
        elif self.user_type == 'Omega':
            can_remove = (
                                 not await is_user_elevated(self.member.id) and
                                 self.member.id != interaction.user.id
                         ) or cemented  # Can remove if cemented
        elif self.user_type == 'Super':
            can_remove = (
                    not await is_user_elevated(self.member.id) and
                    not await is_user_super(self.member.id) and
                    self.member.id != interaction.user.id and
                    not cemented  # Cannot remove if cemented
            )

        if can_remove:
            if cemented:  # If report is cemented, send a message to the King
                king_id = await fetch_king()
                if king_id:
                    king_user = await bot.fetch_user(king_id)
                    embed = discord.Embed(
                        title=f"Deleted Report: {report_type}",
                        description=f"A report against {self.member.name} with reason: {reason} was deleted by {interaction.user.name}.",
                        color=0xFF5733
                    )
                    await king_user.send(
                        f"A cemented report against {self.member.name} was deleted by {interaction.user.name}",
                        embed=embed
                    )
            await self.delete_report_from_db()
            del self.reports[self.current_report_index]

            if not self.reports:
                self.current_report_index = 0
            else:
                self.current_report_index = min(
                    self.current_report_index, len(self.reports) - 1)

            await interaction.response.edit_message(embed=self.generate_embed())

class ModCheckHiddenView(discord.ui.View):
    def __init__(self, ctx, hidden_users):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.hidden_users = list(hidden_users)
        self.current_hidden_user_index = 0

    def generate_embed(self):
        if not self.hidden_users:
            embed = discord.Embed(
                title="No hidden users",
                description="There are no users with the hidden tag."
            )
            return embed

        user_id, hidden_by, hidden_reason = self.hidden_users[self.current_hidden_user_index]
        embed = discord.Embed(
            title=f"Mod View: Hidden User {user_id}",
            description=f"Hidden By: {hidden_by}\nReason: {hidden_reason}"
        )
        footer_text = f"User {self.current_hidden_user_index + 1} of {len(self.hidden_users)}"
        embed.set_footer(text=footer_text)
        return embed

    async def update_hidden_status(self, hidden_status: bool, super_hidden_status: bool):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                user_id = self.hidden_users[self.current_hidden_user_index][0]
                await cur.execute("""
                    UPDATE user_attributes
                    SET is_hidden = %s, super_hidden = %s
                    WHERE user_id = %s
                """, (hidden_status, super_hidden_status, user_id))

    @discord.ui.button(label="Unhide", style=discord.ButtonStyle.success)
    async def unhide_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_hidden_status(False, False)
        del self.hidden_users[self.current_hidden_user_index]
        if not self.hidden_users:
            self.current_hidden_user_index = 0
        else:
            self.current_hidden_user_index = min(
                self.current_hidden_user_index, len(self.hidden_users) - 1
            )
        await interaction.response.edit_message(embed=self.generate_embed())

    @discord.ui.button(label="Cement Hidden", style=discord.ButtonStyle.danger)
    async def cement_hidden(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_hidden_status(True, True)
        await interaction.response.edit_message(embed=self.generate_embed())

async def get_user_type(user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_type FROM special_users WHERE user_id = %s
            """, (user_id,))
            result = await cur.fetchone()
            return result[0] if result else None

@bot.command(name="mcheck", hidden=True)
async def mod_check_reports(ctx, member_id: int):
    if not await is_user_elevated(ctx.author.id):
        print("not")
        return

    # Fetch the user object based on the ID
    member = await bot.fetch_user(member_id)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT id, report_type, reason, votes, cemented
                FROM actions
                WHERE user_id = %s AND action_type = 'report'
                ORDER BY id ASC
            """, (member.id,))

            reports = await cur.fetchall()

    if not reports:
        await ctx.send(f"No reports are available for {member.name}.")
        return

    user_type = await get_user_type(ctx.author.id)  # Implement this function to get user_type
    view = ModCheckReportsView(ctx, reports, member, user_type)
    await ctx.send(embed=view.generate_embed(), view=view)

@bot.command(name='ban', hidden=True)
async def elevated_ban(ctx, member: discord.User):
    if not await is_user_elevated(ctx.author.id):
        return

    # Ask for the reason
    await ctx.send("Please provide the reason for the ban within 60 seconds.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('You took too long to provide the reason. Operation cancelled.')
        return

    reason = msg.content

    try:
        await ctx.guild.ban(member, reason=reason)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO user_attributes (user_id, is_banned, banned_by, ban_reason)
                    VALUES (%s, TRUE, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    is_banned = TRUE, banned_by = %s, ban_reason = %s
                """, (member.id, ctx.author.id, reason, ctx.author.id, reason))
                await conn.commit()

        embed = discord.Embed(
            title=f"Banned {member.name}",
            description=f"{member.mention} has been banned. Reason: {reason}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"An error occurred: {e}")
        embed = discord.Embed(
            title="Ban Error",
            description=f"An error occurred while banning {member.mention}.",
            color=0xFF0000
        )
        await ctx.send(embed=embed)

@bot.command(name='unban', hidden=True)
async def elevated_unban(ctx, member_id: int):
    # Check if the user executing the command is elevated
    if not await is_user_elevated(ctx.author.id):
        return

    # Execute the unban
    try:
        member = await ctx.guild.fetch_member(member_id)
        await ctx.guild.unban(member)
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE user_attributes
                    SET is_banned = FALSE
                    WHERE user_id = %s
                """, (member_id,))
                await conn.commit()
        embed = discord.Embed(
            title=f"Unbanned {member.name}",
            description=f"{member.mention} has been unbanned.",
            color=0x00FF00  # Green color to indicate a successful action
        )
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"An error occurred: {e}")
        embed = discord.Embed(
            title="Unban Error",
            description=f"An error occurred while unbanning the user with ID {member_id}.",
            color=0xFF0000  # Red color to indicate an error
        )
        await ctx.send(embed=embed)

@bot.command(name='server', hidden=True)
async def elevated_set_admin(ctx, member: discord.User):
    if not await is_user_elevated(ctx.author.id):
        return

    # Ask for the reason
    await ctx.send("Please provide the reason for setting this user as admin within 60 seconds.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('You took too long to provide the reason. Operation cancelled.')
        return

    reason = msg.content

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO user_attributes (user_id, is_server_admin, admin_by)
                    VALUES (%s, TRUE, %s)
                    ON DUPLICATE KEY UPDATE
                    is_server_admin = TRUE, admin_by = %s
                """, (member.id, ctx.author.id, ctx.author.id))
                await conn.commit()

        embed = discord.Embed(
            title=f"Admin set for {member.name}",
            description=f"{member.mention} has been set as an admin. Reason: {reason}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"An error occurred: {e}")
        embed = discord.Embed(
            title="Set Admin Error",
            description=f"An error occurred while setting {member.mention} as an admin.",
            color=0xFF0000
        )
        await ctx.send(embed=embed)

@bot.command(name='unserver', hidden=True)
async def elevated_unset_admin(ctx, member: discord.User):
    if not await is_user_elevated(ctx.author.id):
        return

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE user_attributes
                    SET is_server_admin = FALSE
                    WHERE user_id = %s
                """, (member.id,))
                await conn.commit()

        embed = discord.Embed(
            title=f"Admin unset for {member.name}",
            description=f"{member.mention} is no longer an admin.",
            color=0x00FF00  # Green color to indicate a successful action
        )
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"An error occurred: {e}")
        embed = discord.Embed(
            title="Unset Admin Error",
            description=f"An error occurred while unsetting {member.mention} as an admin.",
            color=0xFF0000  # Red color to indicate an error
        )
        await ctx.send(embed=embed)

@bot.command(name='set_famous', hidden=True)
async def elevated_set_famous(ctx, member: discord.User):
    if not await is_user_elevated(ctx.author.id):
        return

    # Ask for the reason
    await ctx.send("Please provide the reason for setting this user as famous within 60 seconds.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send('You took too long to provide the reason. Operation cancelled.')
        return

    reason = msg.content

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO user_attributes (user_id, is_famous, famous_by, famous_reason)
                    VALUES (%s, TRUE, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    is_famous = TRUE, famous_by = %s, famous_reason = %s
                """, (member.id, ctx.author.id, reason, ctx.author.id, reason))
                await conn.commit()

        embed = discord.Embed(
            title=f"Famous set for {member.name}",
            description=f"{member.mention} has been set as famous. Reason: {reason}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"An error occurred: {e}")
        embed = discord.Embed(
            title="Set Famous Error",
            description=f"An error occurred while setting {member.mention} as famous.",
            color=0xFF0000
        )
        await ctx.send(embed=embed)

@bot.command(name='unset_famous', hidden=True)
async def elevated_unset_famous(ctx, member: discord.User):
    if not await is_user_elevated(ctx.author.id):
        return

    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE user_attributes
                    SET is_famous = FALSE
                    WHERE user_id = %s
                """, (member.id,))
                await conn.commit()

        embed = discord.Embed(
            title=f"Famous unset for {member.name}",
            description=f"{member.mention} is no longer famous.",
            color=0x00FF00  # Green color to indicate a successful action
        )
        await ctx.send(embed=embed)

    except Exception as e:
        print(f"An error occurred: {e}")
        embed = discord.Embed(
            title="Unset Famous Error",
            description=f"An error occurred while unsetting {member.mention} as famous.",
            color=0xFF0000  # Red color to indicate an error
        )
        await ctx.send(embed=embed)

@bot.command(name="hidden", hidden=True)
async def mod_check_hidden(ctx):
    if not await is_user_elevated(ctx.author.id):
        return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT user_id, hidden_by, hidden_reason
                FROM user_attributes
                WHERE is_hidden = TRUE
                ORDER BY user_id ASC
            """)

            hidden_users = await cur.fetchall()

    if not hidden_users:
        await ctx.send("No hidden users are available.")
        return

    view = ModCheckHiddenView(ctx, hidden_users)
    await ctx.send(embed=view.generate_embed(), view=view)



















# Sexual Sub-Report Menu
class SexualSubReportMenuView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label='Predator', style=discord.ButtonStyle.primary, custom_id='Predator')
    async def report_predator(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Predator', 'Sexual')

    @discord.ui.button(label='Creep', style=discord.ButtonStyle.primary, custom_id='Creep')
    async def report_creep(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Creep', 'Sexual')

    @discord.ui.button(label='Other', style=discord.ButtonStyle.primary, custom_id='Other_Sexual')
    async def report_other_sexual(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Other Sexual', 'Sexual')

# Spam Sub-Report Menu
class SpamSubReportMenuView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label='Offensive', style=discord.ButtonStyle.primary, custom_id='Offensive')
    async def report_offensive(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Offensive', 'Spam')

    @discord.ui.button(label='Advertising', style=discord.ButtonStyle.primary, custom_id='Advertising')
    async def report_advertising(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Advertising','Spam')

    @discord.ui.button(label='Other', style=discord.ButtonStyle.primary, custom_id='Other_Spam')
    async def report_other_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Other Spam', 'Spam')

# Hateful Sub-Report Menu
class HatefulSubReportMenuView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label='Hate Speech', style=discord.ButtonStyle.primary, custom_id='Hate_Speech')
    async def report_hate_speech(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Hate Speech', 'Hateful')

    @discord.ui.button(label='Rude', style=discord.ButtonStyle.primary, custom_id='Rude')
    async def report_rude(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Rude', 'Hateful')

    @discord.ui.button(label='Other', style=discord.ButtonStyle.primary, custom_id='Other_Hateful')
    async def report_other_hateful(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Other Hateful', 'Hateful')

# Fraud Sub-Report Menu
class FraudSubReportMenuView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label='Impersonator', style=discord.ButtonStyle.primary, custom_id='Impersonator')
    async def report_impersonator(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Impersonator', 'Fraud')

    @discord.ui.button(label='Scamming', style=discord.ButtonStyle.primary, custom_id='Scamming')
    async def report_scamming(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Scamming', 'Fraud')

    @discord.ui.button(label='Other', style=discord.ButtonStyle.primary, custom_id='Other_Fraud')
    async def report_other_fraud(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.parent_view.handle_report(interaction, 'Other Fraud', 'Fraud')
class ReportMenuView(discord.ui.View):
    cooldown_dict = {}
    def __init__(self, ctx, member_id, pool):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.member_id = member_id
        self.pool = pool


    async def store_report(self, subtype, reason):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await conn.begin()

                try:
                    # Insert action report
                    await cur.execute(
                        "INSERT INTO actions (user_id, actor_id, action_type, report_type, reason) VALUES (%s, %s, 'report', %s, %s)",
                        (self.member_id, self.ctx.author.id, subtype, reason)
                    )

                    # Update reputation and total reports
                    await cur.execute("""
                        INSERT INTO reputation (user_id, reputation, total_reports, total_boosts)
                        VALUES (%s, -1, 1, 0)
                        ON DUPLICATE KEY UPDATE
                        reputation = reputation - 1,
                        total_reports = total_reports + 1
                    """, (self.member_id,))

                    # Commit all changes to the database
                    await conn.commit()

                    # Fetch the reported user and try to send a DM
                    reported_user = await self.ctx.bot.fetch_user(self.member_id)
                    dm_channel = await reported_user.create_dm()

                    #try:
                     #   await dm_channel.send(
                      #      f"You've been reported for {subtype}. You can check your current status by using `!check` & `!karma`.")
                    #except discord.errors.Forbidden:
                     #   print("Couldn't send DM. User has either blocked the bot or disabled DMs for this server.")

                except Exception as e:
                    # Rollback changes in case of any exceptions
                    await conn.rollback()
                    print(e)  # or any other form of logging
                    raise

    async def prompt_for_reason(self, interaction):
        # Fetching the discord.User object using the member_id
        member = await self.ctx.bot.fetch_user(self.member_id)

        # Creating an embed to prompt for the report reason
        embed = discord.Embed(
            title=f"Report against {member.name}",
            description="Please enter the reason for your report within 60 seconds."
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        await interaction.response.send_message(embed=embed)

        def check(m):
            return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id

        try:
            message = await self.ctx.bot.wait_for('message', timeout=60, check=check)
            return message.content
        except asyncio.TimeoutError:
            # If the user takes too long, send an embed informing them that the report has been cancelled
            cancel_embed = discord.Embed(
                title=f"Report against {member.name}",
                description="You took too long to enter a reason. Report has been cancelled.",
                color=0xFF0000  # Optional: Red color for the embed to indicate error/cancellation
            )
            cancel_embed.set_thumbnail(url=member.display_avatar.url)
            await interaction.followup.send(embed=cancel_embed)
            return None


    async def remove_cooldown(self, user_id, maintype):
        await asyncio.sleep(900)
        del self.cooldown_dict[(user_id, maintype)]

    async def handle_report(self, interaction, subtype, maintype):

        # Assign maintype based on subtype
        if subtype in ['Predator', 'Creep', 'Sexual Other']:
            maintype = 'Sexual'
        elif subtype in ['Offensive', 'Advertising', 'Other Spam']:
            maintype = 'Spam'
        elif subtype in ['Hate Speech', 'Rude', 'Other_Hateful']:
            maintype = 'Hateful'
        elif subtype in ['Impersonator', 'Scamming', 'Other Fraud']:
            maintype = 'Fraud'

        # Print current cooldown dictionary before checking for cooldown
        is_on_cooldown = self.cooldown_dict.get((self.member_id, maintype), None)
        if is_on_cooldown and datetime.utcnow() < is_on_cooldown:
            remaining_time = is_on_cooldown - datetime.utcnow()
            minutes_remaining = int(remaining_time.total_seconds() / 60)

            await self.ctx.send(
                f"This user has already been reported for {maintype} in the last 15 minutes. "
                f"Please wait an additional {minutes_remaining} minutes, or upvote their most current {maintype} "
                f"by using !check command"
            )
            return

        # Only proceed to prompt for reason if not on cooldown
        reason = await self.prompt_for_reason(interaction)
        if reason:
            await self.store_report(subtype, reason)

            # Fetching the discord.User object using the member_id
            member = await self.ctx.bot.fetch_user(self.member_id)

            # Creating an embed with the reported user's avatar
            embed = discord.Embed(
                title=f"Report against {member.name}",
                description=f"Type: {subtype}\n\nReason: {reason}"
            )
            embed.set_thumbnail(url=member.display_avatar.url)

            await interaction.followup.send(embed=embed)

            # Set a 15-minute cooldown
            self.cooldown_dict[(self.member_id, maintype)] = datetime.utcnow() + timedelta(minutes=15)

            # Schedule the removal of the cooldown
            asyncio.create_task(self.remove_cooldown(self.member_id, maintype))

            # Print current cooldown dictionary after setting the cooldown
            print(f"Cooldown dict after: {self.cooldown_dict}")


    async def show_subtypes(self, interaction, report_type):
        if interaction.guild:  # Check if interaction is within a guild context
            member = interaction.guild.get_member(self.member_id)
        else:
            member = await self.ctx.bot.fetch_user(self.member_id)

        embed = discord.Embed(
            title=f"Select subtype for {report_type}",
            description=f"Report against {member.name}"
        )

        # Add the member's avatar to the embed
        embed.set_thumbnail(url=member.display_avatar.url)

        if report_type == "Sexual":
            subview = SexualSubReportMenuView(self)
        elif report_type == "Spam":
            subview = SpamSubReportMenuView(self)
        elif report_type == "Hateful":
            subview = HatefulSubReportMenuView(self)
        elif report_type == "Fraud":
            subview = FraudSubReportMenuView(self)

        await interaction.response.send_message(embed=embed, view=subview)

    @discord.ui.button(label="Sexual", style=discord.ButtonStyle.primary)
    async def report_sexual(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_subtypes(interaction, 'Sexual')

    @discord.ui.button(label="Spam", style=discord.ButtonStyle.primary)
    async def report_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_subtypes(interaction, 'Spam')

    @discord.ui.button(label="Hateful", style=discord.ButtonStyle.primary)
    async def report_hateful(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_subtypes(interaction, 'Hateful')

    @discord.ui.button(label="Fraud", style=discord.ButtonStyle.primary)
    async def report_fraud(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_subtypes(interaction, 'Fraud')
async def send_report_menu(ctx, member: discord.User, pool):
    embed = discord.Embed(
        title=f"Report {member.name}",
        description="Choose report type"
    )

    # Add the member's avatar to the embed
    embed.set_thumbnail(url=member.display_avatar.url)

    view = ReportMenuView(ctx, member.id, pool)
    await ctx.send(embed=embed, view=view)


@bot.command(name="report")
async def report(ctx, member: discord.User):
    # Check account age
    age_cutoff = datetime.utcnow() - timedelta(days=90)
    author_created_at_naive = ctx.author.created_at.replace(tzinfo=None)

    if author_created_at_naive > age_cutoff:
        await ctx.send("Your account must be at least 90 days old to submit a report.")
        return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Check if the user is banned from reporting
            await cur.execute(
                "SELECT is_banned FROM user_attributes WHERE user_id = %s",
                (ctx.author.id,)
            )
            banned_record = await cur.fetchone()

            if banned_record and banned_record[0]:
                await ctx.send("You are banned from using the report function.")
                return

            # Check if already reported
            await cur.execute(
                "SELECT * FROM actions WHERE user_id = %s AND actor_id = %s AND action_type = 'report'",
                (member.id, ctx.author.id)
            )

            if await cur.fetchone():
                await ctx.send("You have already reported this user.")
                return

    await send_report_menu(ctx, member, pool)

@bot.command(name="boost")
async def boost(ctx, member: discord.User):
    # Check account age
    age_cutoff = datetime.utcnow() - timedelta(days=90)
    author_created_at_naive = ctx.author.created_at.replace(tzinfo=None)

    if author_created_at_naive > age_cutoff:
        embed = discord.Embed(
            title="Boost Error",
            description="Your account must be at least 3 months old to boost someone.",
            color=0xFF0000  # Red color to indicate an error
        )
        await ctx.send(embed=embed)
        return

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await conn.begin()
            try:
                # Check if user is banned
                await cur.execute(
                    "SELECT is_banned FROM user_attributes WHERE user_id = %s",
                    (ctx.author.id,)
                )
                user_data = await cur.fetchone()
                if user_data and user_data['is_banned']:
                    await conn.rollback()
                    embed = discord.Embed(
                        title="Boost Error",
                        description="You are banned and cannot boost anyone.",
                        color=0xFF0000  # Red color to indicate an error
                    )
                    await ctx.send(embed=embed)
                    return

                # Check if already boosted
                await cur.execute(
                    "SELECT * FROM actions WHERE user_id = %s AND actor_id = %s AND action_type = 'boost'",
                    (member.id, ctx.author.id)
                )
                if await cur.fetchone():
                    await conn.rollback()
                    embed = discord.Embed(
                        title=f"Boost - {member.name}",
                        description="You have already boosted this user.",
                        color=0xFF0000  # Red color to indicate an error
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    await ctx.send(embed=embed)
                    return

                # Actual boost logic
                await cur.execute(
                    "INSERT INTO actions (user_id, actor_id, action_type) VALUES (%s, %s, 'boost')",
                    (member.id, ctx.author.id)
                )
                await cur.execute("""
                    INSERT INTO reputation (user_id, reputation, total_reports, total_boosts)
                    VALUES (%s, 1, 0, 1)
                    ON DUPLICATE KEY UPDATE
                    reputation = reputation + 1,
                    total_boosts = total_boosts + 1
                """, (member.id,))

                await conn.commit()

                embed = discord.Embed(
                    title=f"Boost - {member.name}",
                    description=f"You've successfully boosted {member.mention}'s reputation.",
                    color=0x00FF00  # Green color to indicate a successful action
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=embed)

            except Exception as e:
                await conn.rollback()
                print(e)  # Logging the exception
                raise

@bot.command(name="rmr")
async def remove_report(ctx, member: discord.User):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await conn.begin()
            try:
                await cur.execute(
                    "SELECT * FROM actions WHERE user_id = %s AND actor_id = %s AND action_type = 'report'",
                    (member.id, ctx.author.id))
                if not await cur.fetchone():
                    await conn.rollback()
                    error_embed = discord.Embed(
                        title=f"Report Removal - {member.name}",
                        description="You haven't reported this user.",
                        color=0xFF0000  # Red color for the embed
                    )
                    error_embed.set_thumbnail(url=member.display_avatar.url)
                    await ctx.send(embed=error_embed)
                    return

                await cur.execute("DELETE FROM actions WHERE user_id = %s AND actor_id = %s AND action_type = 'report'",
                                  (member.id, ctx.author.id))
                await cur.execute("""
                    UPDATE reputation
                    SET reputation = reputation + 1, total_reports = total_reports - 1
                    WHERE user_id = %s
                """, (member.id,))

                await conn.commit()

                success_embed = discord.Embed(
                    title=f"Report Removal - {member.name}",
                    description=f"Successfully removed report against {member.name}.",
                    color=0x00FF00  # Green color for the embed
                )
                success_embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=success_embed)

            except Exception as e:
                await conn.rollback()
                print(e)
                raise

@bot.command(name="rmb")
async def remove_boost(ctx, member: discord.User):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await conn.begin()
            try:
                await cur.execute(
                    "SELECT * FROM actions WHERE user_id = %s AND actor_id = %s AND action_type = 'boost'",
                    (member.id, ctx.author.id))
                if not await cur.fetchone():
                    await conn.rollback()
                    embed = discord.Embed(
                        title=f"Boost Removal - {member.name}",
                        description="You haven't boosted this user.",
                        color=0xFF0000  # Red color to indicate an error or negative action
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    await ctx.send(embed=embed)
                    return

                await cur.execute("DELETE FROM actions WHERE user_id = %s AND actor_id = %s AND action_type = 'boost'",
                                  (member.id, ctx.author.id))
                await cur.execute("""
                    UPDATE reputation
                    SET reputation = reputation - 1, total_boosts = total_boosts - 1
                    WHERE user_id = %s
                """, (member.id,))

                await conn.commit()

                embed = discord.Embed(
                    title=f"Boost Removal - {member.name}",
                    description=f"You've successfully removed a boost for {member.mention}.",
                    color=0x00FF00  # Green color to indicate a successful action
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                await ctx.send(embed=embed)

            except Exception as e:
                await conn.rollback()
                print(e)
                raise

@bot.command(name="karma")
async def check_reputation(ctx, member: discord.User):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT reputation, total_reports, total_boosts FROM reputation WHERE user_id = %s",
                              (member.id,))
            row = await cur.fetchone()

            # Create an embed to display the reputation details
            embed = discord.Embed(
                title=f"{member.name}'s Reputation",
                description=f"Reputation details for {member.mention}",
                color=0x7289da  # Discord blurple color
            )
            embed.set_thumbnail(url=member.display_avatar.url)

            if row:
                embed.add_field(name="Reputation", value=row[0], inline=True)
                embed.add_field(name="Total Reports", value=row[1], inline=True)
                embed.add_field(name="Total Boosts", value=row[2], inline=True)
                await ctx.send(embed=embed)
            else:
                embed.description = f"{member.name} has no reputation yet."
                await ctx.send(embed=embed)

class CheckReportsView(discord.ui.View):
    def __init__(self, ctx, reports, member: discord.User):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.reports = reports
        self.current_report_index = 0
        self.member = member

    def generate_embed(self):
        report = self.reports[self.current_report_index]
        report_id, report_type, reason, votes_json, cemented = (
                report + (None,) * (5 - len(report))
        )
        votes = json.loads(votes_json or '{}')
        agree_count = sum(1 for vote in votes.values() if vote == 'agree')
        disagree_count = sum(1 for vote in votes.values() if vote == 'disagree')

        cemented_text = "Mod verified: Yes" if cemented else "Mod verified: No"

        embed = discord.Embed(
            title=f"Report against {self.member.name}",
            description=(
                f"Type: {report_type}\n\nReason: {reason}\n\n"
                f"Votes: {agree_count} agree, {disagree_count} disagree\n\n"
                f"{cemented_text}"
            )
        )

        embed.set_thumbnail(url=self.member.display_avatar.url)
        footer_text = f"Report {self.current_report_index + 1} of {len(self.reports)}"
        embed.set_footer(text=footer_text)
        return embed

    async def update_votes_in_db(self, new_votes):
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                report_id = self.reports[self.current_report_index][0]
                new_votes_json = json.dumps(new_votes)
                await cur.execute("UPDATE actions SET votes = %s WHERE id = %s", (new_votes_json, report_id))

                # Convert the tuple to a list for modification
                reports_list = list(self.reports)

                # Update the self.reports list with new votes
                report_id, report_type, reason, _ = reports_list[self.current_report_index]
                updated_report_tuple = (report_id, report_type, reason, new_votes_json)

                # Update the element and convert back to a tuple if needed
                reports_list[self.current_report_index] = updated_report_tuple
                self.reports = tuple(reports_list)  # Convert back to a tuple if needed

    @discord.ui.button(label="Agree", style=discord.ButtonStyle.success)
    async def vote_agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        report = self.reports[self.current_report_index]
        _, _, _, votes_json = report
        votes = json.loads(votes_json or '{}')

        # Update the vote of the user, or set it if not set before
        votes[str(interaction.user.id)] = 'agree'

        await self.update_votes_in_db(votes)
        await interaction.response.edit_message(embed=self.generate_embed())

    @discord.ui.button(label="Disagree", style=discord.ButtonStyle.danger)
    async def vote_disagree(self, interaction: discord.Interaction, button: discord.ui.Button):
        report = self.reports[self.current_report_index]
        _, _, _, votes_json = report
        votes = json.loads(votes_json or '{}')

        # Update the vote of the user, or set it if not set before
        votes[str(interaction.user.id)] = 'disagree'

        await self.update_votes_in_db(votes)
        await interaction.response.edit_message(embed=self.generate_embed())

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def go_previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return
        self.current_report_index = (self.current_report_index - 1) % len(self.reports)
        await interaction.response.edit_message(embed=self.generate_embed())

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def go_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return
        self.current_report_index = (self.current_report_index + 1) % len(self.reports)
        await interaction.response.edit_message(embed=self.generate_embed())

@bot.command(name="check")
async def check_reports(ctx, member_id: int):  # Accept the member_id as an integer
    # Fetch the user object based on the ID
    member = await bot.fetch_user(member_id)

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT id, report_type, reason, votes
                FROM actions
                WHERE user_id = %s AND action_type = 'report'
                ORDER BY id ASC
            """, (member.id,))

            reports = await cur.fetchall()

    if not reports:
        await ctx.send(f"No reports are available for {member.name}.")
        return

    view = CheckReportsView(ctx, reports, member)
    await ctx.send(embed=view.generate_embed(), view=view)


bot.run('token')