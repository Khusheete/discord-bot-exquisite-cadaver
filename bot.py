import discord
import game


ENV: dict
HELP: str

with open("env.json", "r") as f:
    import json
    ENV = json.load(f)

with open("help.txt") as f:
    HELP = f.read()


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents = intents)
current_games: list[game.ExquisiteCadaver] = []


@client.event
async def on_ready():
    print(f'{client.user} connected to Discord!')


@client.event
async def on_message(message):
    #ignore messages from self
    if message.author == client.user:
        return

    #it is a game command
    
    if isinstance(message.channel, discord.channel.DMChannel) or message.content.startswith("ExquisiteCadaver") or message.content.startswith("!ec"):
        if message.content.startswith("ExquisiteCadaver") or message.content.startswith("!ec"):
            command: list[str] = message.content.split(" ")[1::]
        else:
            command: list[str] = message.content.split(" ")

        if len(command) == 0 or command[0] == "help":
            await message.channel.send(HELP)
        elif command[0] == "create":
            if len(command) < 2:
                await message.channel.send("Specify at least the mode of the game (modes are \"whole_sentence\", \"last_words\" and \"first_words\").")
                await message.channel.send(HELP)
                return
            #check if the author already has a game at his name
            for g in current_games:
                if g.game_admin == message.author:
                    await message.channel.send("You already have created an Exquisite Cadaver (id: {}]).".format(g.game_id))
                    return
            
            mode: game.GameMode
            character_limit: int = 120
            word_count: int = 3

            if command[1] == "whole_sentence":
                mode = game.GameMode.WHOLE_SENTENCE
            elif command[1] == "last_words":
                mode = game.GameMode.LAST_WORDS
            elif command[1] == "first_words":
                mode = game.GameMode.FIRST_WORDS
            elif command[1] == "random_words":
                mode = game.GameMode.RANDOM_WORDS
            
            if len(command) >= 3:
                try:
                    character_limit = int(command[2])
                except Exception:
                    pass
            if len(command) >= 4:
                try:
                    word_count = int(command[3])
                except Exception:
                    pass
            
            g = game.ExquisiteCadaver(mode, message.author, word_count, character_limit)
            current_games.append(g)

            await message.channel.send(f"Created {message.author}'s game with id {g.game_id}.\nIf you want to join this game enter the command \"join {g.game_id}\"")
        elif command[0] == "end" or command[0] == "stop":
            if len(command) < 2:
                await message.channel.send("Specify game id for the game you want to terminate.")
                await message.channel.send(HELP)
                return
            
            game_id: int

            try:
                game_id = int(command[1])
            except Exception:
                await message.channel.send(f"Could not read id \"{command[1]}\"")
                return

            for g in current_games:
                #check for the author
                if g.game_id == game_id:
                    if g.game_admin == message.author:
                        if g.started():
                            #print the result of the game
                            mentions: str = ""
                            for i in range(len(g.participents)):
                                mentions += f"<@{g.participents[i].id}>"
                                if i + 1 < len(g.participents):
                                    mentions += ", "
                            await message.channel.send(f"{mentions} The game {g.game_id} from {g.game_admin} was {g.current_turn} turn long and the result is:")
                            print("\r\nGame {g.game_id}:\r\n")
                            for tale in g.get_tale():
                                print(f"\x1b[1m{tale}\x1b[m\r\n")
                                await message.channel.send(f"\r\n{tale}")
                        else:
                            await message.channel.send(f"Deleted game {g.game_id}.")
                        current_games.remove(g)
                        return
                    else:
                        await message.channel.send(f"You do not own the game with id {game_id}.")
                        return

            await message.channel.send(f"There is no game with id {game_id}.")
        elif command[0] == "join":
            if len(command) < 2:
                await message.channel.send("Specify game id for the game you want to join.")
                await message.channel.send(HELP)
                return
            
            game_id: int

            try:
                game_id = int(command[1])
            except Exception:
                await message.channel.send(f"Could not read id \"{command[1]}\"")
                return

            for g in current_games:
                if g.game_id == game_id:
                    error = g.register_participent(message.author)
                    if error == game.GameError.ALREADY_JOINED:
                        await message.channel.send(f"You already joined the game {g.game_id}.")
                    elif error == game.GameError.ALREADY_STARTED:
                        await message.channel.send(f"The game {g.game_id} was already started.")
                    elif error == game.GameError.OK:
                        await message.add_reaction("👍")
                    return
            
            await message.channel.send(f"Could not find the game {game_id}.")
        elif command[0] == "start":
            if len(command) < 2:
                await message.channel.send("Specify game id for the game you want to start.")
                await message.channel.send(HELP)
                return

            game_id: int

            try:
                game_id = int(command[1])
            except Exception:
                await message.channel.send(f"Could not read id \"{command[1]}\"")
                return

            for g in current_games:
                if g.game_id == game_id:
                    if g.game_admin == message.author:
                        error = g.start_game()
                        if error == game.GameError.NOT_ENOUGH_PLAYERS:
                            await message.channel.send(f"There are not enough players to start game {g.game_id}.")
                        elif error == game.GameError.ALREADY_STARTED:
                            await message.channel.send(f"The game {g.game_id} was already started.")
                        elif error == game.GameError.OK:
                            mentions: str = ""
                            for i in range(len(g.participents)):
                                mentions += f"<@{g.participents[i].id}>"
                                if i + 1 < len(g.participents):
                                    mentions += ", "
                            await message.channel.send(f"{mentions} Started game {g.game_id}.")
                            print(f"[{g.get_next_player().name}] Now writing")
                            await g.get_next_player().send(f"It is your turn to add a sentence to the game {g.game_id} by {g.game_admin} using the command \"post {g.game_id} <your sentence>\".")
                    else:
                        await message.channel.send(f"You do not own the game with id {game_id}.")
                    return
            
            await message.channel.send(f"Could not find the game {game_id}.")
        elif command[0] == "post":
            if len(command) < 3:
                await message.channel.send("Specify game id for the game you want to post to and the sentence you want to write.")
                await message.channel.send(HELP)
                return
            
            game_id: int

            try:
                game_id = int(command[1])
            except Exception:
                await message.channel.send(f"Could not read id \"{command[1]}\"")
                return

            if message.content.startswith("ExquisiteCadaver") or message.content.startswith("!ec"):
                sentence: str = message.content.split(" ", 3)[3]
            else:
                sentence: str = message.content.split(" ", 2)[2]

            for g in current_games:
                if g.game_id == game_id:
                    error, data = g.push_sentence(message.author, sentence + " ")
                    if error == game.GameError.WRONG_PARTICIPENT:
                        print(f"[{message.author.name}] Wrong Participent")
                        await message.author.send("It is not your turn to post a sentence.")
                    elif error == game.GameError.TOO_MUCH_CHARS:
                        print(f"[{message.author.name}] Too much chars")
                        await message.author.send(f"The maximum number of characters you can post in this game is {g.character_limit}, you need to remove {data['diff']} chars.")
                    elif error == game.GameError.NOT_STARTED:
                        print(f"[{message.author.name}] Not Started")
                        await message.author.send("This game was not started yet.")
                    elif error == game.GameError.OK:
                        print(f"[{message.author.name}] Posted sucessfully")
                        await message.add_reaction("👍")
                        print(f"\n[{g.get_next_player().name}] Now writing")
                        await g.get_next_player().send(f"It is your turn to add a sentence to the game {g.game_id} by {g.game_admin} using the command \"post {g.game_id} <your sentence>\".\nThis is your indication to write: \n\"{g.get_given_info()}\"")
                    return
            
            await message.channel.send(f"Could not find the game {game_id}.")


client.run(ENV["discord_token"])