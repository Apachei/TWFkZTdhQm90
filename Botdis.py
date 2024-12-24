# Source code for my bot id: 1321183834925957195
import discord
import sqlite3
import jwt
import datetime
from discord.ext import commands

# Define the intents (permissions your bot needs)
intents = discord.Intents.default()
intents.message_content = True  # Allow your bot to read message content

# Create an instance of a bot with the required intents and a command prefix (e.g. "!")
bot = commands.Bot(command_prefix="!", intents=intents)
conn = sqlite3.connect('info.db')
cursor = conn.cursor()

# A simple in-memory session store (you can use a database for better persistence)
sessions = {}


# Function to fetch person information from the database
def get_person_info(name):
    cursor.execute("SELECT Information_description FROM people WHERE Name = ?", (name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return "No information found for this person."


# Function to generate a JWT token for the user (guest or admin login)
def generate_jwt(user_id, role="guest"):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # 1 hour expiration
    token = jwt.encode({'user_id': user_id, 'role': role, 'exp': expiration_time}, SECRET_KEY, algorithm='HS256')
    return token


# Function to decode and verify the JWT token
def verify_jwt(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


# Function to create a session for the user based on JWT token
def login_with_jwt(user_id, token):
    # Verify the JWT token first
    user_data = verify_jwt(token)

    if not user_data:
        return None  # Invalid or expired token

    # If the token is valid, create a session for the user
    sessions[user_id] = {
        'token': token,
        'role': user_data['role'],
        'expires_at': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Session expiry time
    }
    return sessions[user_id]  # Return session data


@bot.event
async def on_ready():
    print(f'Bot {bot.user} is now online and ready!')


# Check if the command is being executed in a DM or a public channel
async def check_dm(ctx):
    if isinstance(ctx.channel, discord.DMChannel):
        return True
    else:
        await ctx.send("Please use this command in DMs, not in public channels.")
        return False


# Command to login and generate a JWT token as a guest (hidden from !help)
@bot.command()
async def login(ctx):
    if not await check_dm(ctx):
        return
    user_id = str(ctx.author.id)  # Use Discord user ID as the unique identifier
    role = "guest"  # Default role is guest
    token = generate_jwt(user_id, role)
    await ctx.author.send(f"Your login was successful as a guest. Here is your JWT token:\n{token}")


# Command to login with an existing JWT token (session management)
@bot.command()
async def login_with_token(ctx, token: str):
    if not await check_dm(ctx):
        return
    user_id = str(ctx.author.id)  # Use Discord user ID as the unique identifier
    session = login_with_jwt(user_id, token)

    if session:
        await ctx.author.send(f"Login successful! Your session has been created.\nRole: {session['role']}")
    else:
        await ctx.author.send("Invalid or expired token. Please log in again to get a valid token.")


# Command to fetch information about a person (authentication required only for "Elsfa7 Elmrta7")
@bot.command()
async def info(ctx, name: str, token: str = None):
    if not await check_dm(ctx):
        return

    # Check if the user is trying to access "Elsfa7 Elmrta7"
    if name == "Elsfa7 Elmrta7":
        # If user is Elsfa7 Elmrta7, they need a valid token or be an admin
        if token:
            user_data = verify_jwt(token)
            if not user_data:
                await ctx.author.send("Invalid or expired token. Please log in again to get a valid token.")
                return
            # Check if the user is an admin
            if user_data['role'] != 'admin':
                await ctx.author.send("You are not authorized to access this information. Admins only.")
                return
        else:
            # If no token is provided, check the session for admin role
            session = sessions.get(str(ctx.author.id))
            if not session or session['role'] != 'admin':
                await ctx.author.send(
                    "You need to provide a valid JWT token with admin privileges to access this feature.")
                return

    # For everyone else (including guests), no authentication required
    name = name.title()
    if not name:
        await ctx.author.send("You need to add a name, buddy.")
    else:
        info = get_person_info(name)
        await ctx.author.send(f'**{name}:** {info}')


# Command to list all names in the database (hidden from !list)
@bot.command()
async def list(ctx):
    cursor.execute("SELECT name FROM people")
    result = cursor.fetchall()
    names = ""
    for i in result:
        names += i[0] + "\n"
    try:
        await ctx.author.send(names)
    except discord.Forbidden:
        await ctx.send("I can't send you a DM. Please enable DMs so I can send you the list.")

bot.run("[REDECATED]")
