import discord
import os
import pymongo
from pymongo import MongoClient
import datetime as dt
from discord.ext import commands


# def add_match(match):
# 	for user in data.find():
# 		data.update_one({"Nickname": user["Nickname"]}, {"$set": {match: {"winner": "", "bet_money": 0}}})
#
# 	return match


def delete_m(m):
	all_matches = []
	for user in data.find():
		all_matches.extend(user["Matches"])
	odds.delete_one({"match": m})

	if m in blocked_bets:
		blocked_bets.remove(m)

	if m in all_matches:
		data.update({}, {"$unset": {f"Matches.{m}": ""}}, multi=True)
		return True
	else:
		return False


def restart_money():
	for user in data.find():
		data.update_one({"user_id": user["user_id"]}, {"$set": {"Money": STARTING_CASH}})


client = pymongo.MongoClient("mongodb+srv://ludz:<password>@cluster0.29w3m.mongodb.net/?retryWrites=true&w=majority")
db = client.test
data = db.test
odds = db.odds

#######################################################

STARTING_CASH = 200
BETTING_ADMIN_NAME = "💵┆admin-komendy"
BETTING_ADMIN_ID = 988416123340988460
JOIN_BETTING_ID = 988421788432232509
JOIN_BETTING_NAME = "💵┆dolacz_do_zakladow"
BETTING_ID = 988421825539227698
BETTING_NAME = "💵┆zaklady"
BETTING_LOG_ID = 988421854962278430
BETTING_LOG_NAME = "bukmacherka_log"
BETTING_NEWS_ID = 988421889305243658
BETTING_NEWS_NAME = "💵┆info_zaklady"
CATEGORY_NAME = "💵┆bukmacherka"

LOGO = "https://cdn.discordapp.com/attachments/813422647604936725/852118105999933440/logopolskaliga.png"

bets_possible = True
blocked_bets = []

client = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)

#########################################################

@client.event
async def on_ready():
	print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
	if str(message.channel) == BETTING_NAME or str(message.channel) == JOIN_BETTING_NAME:
		try:
			await message.add_reaction("🖐️")
		except discord.errors.NotFound:
			print("bug")

	await client.process_commands(message)


@client.command(aliases=['av'])
async def avatar(context, user: discord.User = None):
	embed = discord.Embed(title="Avatar", color=0xff0000)
	if user:
		embed.add_field(name=f"{user}", value="-----------", inline=False)
		embed.set_image(url=user.avatar_url)
	else:
		embed.add_field(name=f"{context.author}", value="-----------", inline=False)
		embed.set_image(url=context.message.author.avatar_url)
	await context.channel.send(embed=embed)


@client.command(aliases=['del_bet'])
async def delete_bet(context, match_raw):
	global blocked_bets
	match = match_raw.lower()
	embed = discord.Embed(color=0xff0000)
	embed.set_author(name=context.author)
	embed.set_thumbnail(url=LOGO)
	action_info = ""
	if data.find_one({"user_id": context.author.id}):
		if match not in blocked_bets:
			user_matches = data.find_one({"user_id": context.author.id})["Matches"]
			user_bets = ""
			if match in user_matches:
				bet_money = data.find_one({"user_id": context.author.id})["Matches"][match]["bet_money"]
				winner = data.find_one({"user_id": context.author.id})["Matches"][match]["winner"]
				data.update_one({"user_id": context.author.id}, {"$inc": {"Money": bet_money}})
				odds.update_one({"match": match}, {"$inc": {f"votes.{winner}": -1}})
				data.update_one({"user_id": context.author.id}, {"$unset": {f"Matches.{match}": ""}})

				action_info = f"Usunąłeś mecz **{match}** ze swojej listy zakładów."
			else:
				action_info = f"Nie znaleziono meczu **{match}** na liście twoich zakładów!"
		else:
			action_info = f"Już za późno, żeby wycofać się z tego zakładu."
	else:
		action_info = f"Nie ma Cię w naszej bazie.\n " \
					f"Kliknij w reakcję na kanale {client.get_channel(JOIN_BETTING_ID).mention}."


	embed.add_field(name="Usunięcie zakładu", value=action_info)
	await context.channel.send(embed=embed)


@client.command()
async def get_id(context):
	guild = context.guild
	memberlist = guild.members
	for member in memberlist:
		print(member.name)


@client.command()
async def refresh_id(context):
	guild = context.guild
	memberlist = guild.members
	for member in memberlist:
		if data.find({"Nickname": member.name}):
			data.update_one({"Nickname": member.name}, {"$set": {"user_id": member.id}})


@client.command(aliases=['bot_info', 'bet_info', 'bot_help'])
async def bet_help(context):
	embed = discord.Embed(title="Lista komend", color=0xff0000)
	embed.set_thumbnail(url=LOGO)
	embed.add_field(name="**!money**", value="Stan konta.", inline=False)
	embed.add_field(name="**!my_bets**", value="Lista obecnych zakładów danego użytkownika.", inline=False)
	embed.add_field(name="**!daily**", value="Odbiór bonusu 10 monet - jedno na dzień.", inline=False)
	embed.add_field(name="**!top**", value="TOP 5 serwera pod względem ilości monet.", inline=False)
	embed.add_field(name="**!del_bet**", value="Anulowanie zakładu.", inline=False)
	await context.channel.send(embed=embed)


@client.command()
async def daily(context):
	current_time = dt.datetime.now() + dt.timedelta(hours=2)
	if data.find_one({"user_id": context.author.id}):
		if str(current_time.date()) != str(data.find_one({"user_id": context.author.id})["last_daily"]):
			data.update_one({"user_id": context.author.id}, {"$set": {"last_daily": str(current_time.date())}})
			data.update_one({"user_id": context.author.id}, {"$inc": {"Money": 10}})

			daily_info = f"Do twojego konta zostało dodane 10 monet."
		else:
			daily_info = f"Dzisiaj już odebrałeś swój bonus, poczekaj do jutra!"
	else:
		daily_info = f"Nie ma Cię w naszej bazie.\n " \
					f"Kliknij w reakcję na kanale {client.get_channel(JOIN_BETTING_ID).mention}."

	embed = discord.Embed(color=0xff0000, title="Daily")
	embed.set_thumbnail(url=LOGO)
	embed.add_field(name=context.author, value=daily_info, inline=False)
	await context.channel.send(embed=embed)


@client.command()
async def my_bets(context):
	user_bets = ""
	if data.find_one({"user_id": context.author.id}):
		i = 1
		user_matches = data.find_one({"user_id": context.author.id})["Matches"]

		for match in user_matches:
			user_winner = data.find_one({"user_id": context.author.id})["Matches"][match]["winner"]
			user_bet_money = data.find_one({"user_id": context.author.id})["Matches"][match]["bet_money"]
			if user_bet_money > 0:
				user_bets += f"**{i}. {match}: {user_winner} - {user_bet_money}**\n"
				i += 1
		if user_bets == "":
			user_bets = "Nie masz żadnych zakładów"
	else:
		user_bets = f"Nie ma Cię w naszej bazie.\n " \
					f"Kliknij w reakcję na kanale {client.get_channel(JOIN_BETTING_ID).mention}."

	embed = discord.Embed(color=0xff0000, title="Zakłady")
	embed.set_thumbnail(url=LOGO)
	embed.add_field(name=context.author, value=user_bets, inline=False)
	await context.channel.send(embed=embed)


@client.command(aliases=['bal'])
async def money(context, user: discord.User = None):
	embed = discord.Embed(title="Stan konta", color=0xff0000)
	command_user = ""
	if not user:
		command_user = context.author
		embed.set_thumbnail(url=context.author.avatar_url)
		if data.find_one({"user_id": context.author.id}):
			money_info = f"{data.find_one({'user_id': context.author.id})['Money']}"
		else:
			money_info = f"Nie ma Cię w naszej bazie.\n " \
					f"Kliknij w reakcję na kanale {client.get_channel(JOIN_BETTING_ID).mention}."
	else:
		command_user = user
		embed.set_thumbnail(url=user.avatar_url)
		if data.find_one({"user_id": user.id}):
			money_info = f"{data.find_one({'user_id': user.id})['Money']}"
		else:
			money_info = f"Nie znaleziono użytkownika **{user.name}** w bazie."

	embed.add_field(name=command_user, value=money_info, inline=False)
	await context.channel.send(embed=embed)


@client.command()
async def top(context):
	embed = discord.Embed(title="Top 10", color=0xff0000)
	top_sorted = data.find().sort("Money", pymongo.DESCENDING).limit(10)
	i = 1
	for user in top_sorted:
		embed.add_field(name=f"{i}. {user['Nickname']}", value=user['Money'], inline=False)
		i += 1
	embed.set_thumbnail(url=LOGO)
	await context.channel.send(embed=embed)


@client.command()
async def add_match(context, match):
	if context.channel.id == BETTING_ADMIN_ID:
		match_lower = match.lower()
		team_1 = match_lower.split("_")[0]
		team_2 = match_lower.split("_")[2]
		odds.insert_one(
			{
				"match": match_lower,
				"odds": {team_1: 0.0, "remis": 0.0, team_2: 0.0}, "votes": {team_1: 1, "remis": 1, team_2: 1}
			}
		)
		embed = discord.Embed(title="Mecz", color=0xff0000)
		embed.add_field(name="Kliknij reakcję 🖐️ by obstawić mecz", value=f"{match_lower}")
		embed.set_thumbnail(url=LOGO)
		await client.get_channel(BETTING_ID).send(embed=embed)


@client.command()
async def delete_match(context, match):
	if context.channel.id == BETTING_ADMIN_ID:
		match_lower = match.lower()
		if delete_m(match_lower):
			await context.channel.send(f"Mecz {match_lower} został usunięty!")
		else:
			await context.channel.send(f"Nie znaleziono meczu {match_lower}.")

		category = discord.utils.get(client.guilds[0].categories, name="💵moje_zaklady")

		for channel in category.text_channels:
			if channel.name.startswith(f"bets-{match_lower}"):
				await channel.delete()

		async for message in client.get_channel(BETTING_ID).history(limit=200):
			if match_lower == message.embeds[0].to_dict()["fields"][0]["value"]:
				await message.delete()


@client.command(aliases=["winner"])
async def win(context, match_and_winner_raw):
	if context.channel.id == BETTING_ADMIN_ID:
		match_and_winner = match_and_winner_raw.lower()
		match = match_and_winner.split("-")[0]
		# team_a = match.split("_")[0]
		# team_b = match.split("_")[2]
		winner = match_and_winner.split("-")[1]

		all_matches = []
		for user in data.find():
			all_matches.extend(user["Matches"])

		if match in all_matches:
			winners_list = ""
			winner_odds = odds.find_one({"match": match})["odds"][winner]
			for user in data.find({f"Matches.{match}": {"$exists": True}}):
				if data.find_one({"user_id": user["user_id"]})["Matches"][match]["winner"] == winner:
					money_won = int(winner_odds * user["Matches"][match]["bet_money"])
					winners_list += f"**{user['Nickname']}** wygrał {money_won} monet.\n"

					data.update_one(
						{"user_id": user["user_id"]},
						{"$inc": {"Money": int(winner_odds * user["Matches"][match]["bet_money"])}}
					)

			embed = discord.Embed(title="Koniec meczu", color=0xff0000)
			embed.set_thumbnail(url=LOGO)
			embed.add_field(name=f"PODSUMOWANIE",
							value=f"Wynik meczu {match}: **{winner}**. Monety zostały rozdane zwycięzcom:\n\n"
								f"{winners_list}", inline=False)
			await client.get_channel(BETTING_NEWS_ID).send(embed=embed)
			delete_m(match)
			category = discord.utils.get(context.guild.categories, name="💵moje_zaklady")

			for channel in category.text_channels:
				if channel.name.startswith(f"bets-{match}"):
					await channel.delete()

			async for message in client.get_channel(BETTING_ID).history(limit=200):
				if match == message.embeds[0].to_dict()["fields"][0]["value"]:
					await message.delete()

		else:
			print(f"Mecz {match} nie istnieje.")


@client.command()
async def reset_money(context):
	if context.channel.id == BETTING_ADMIN_ID:
		restart_money()
		await context.channel.send("Zresetowano stan konta wszystkich użytkowników.")


@client.command()
async def block_match(context, match_raw):
	global blocked_bets
	if context.channel.id == BETTING_ADMIN_ID:
		match = match_raw.lower()
		blocked_bets.append(match)
		team_a = match.split("_")[0]
		team_b = match.split("_")[2]

		match_votes = odds.find_one({"match": match})["votes"]
		all_votes = match_votes[team_a] + match_votes["remis"] + match_votes[team_b]
		votes_team_a = match_votes[team_a]
		votes_team_b = match_votes[team_b]
		votes_draw = match_votes["remis"]

		team_a_odds = round((1 / (votes_team_a / all_votes)), 2)
		team_b_odds = round((1 / (votes_team_b / all_votes)), 2)
		draw_odds = round((1 / (votes_draw / all_votes)), 2)

		odds.update_one({"match": match}, {"$set": {f"odds.{team_a}": team_a_odds}})
		odds.update_one({"match": match}, {"$set": {f"odds.{team_b}": team_b_odds}})
		odds.update_one({"match": match}, {"$set": {f"odds.remis": draw_odds}})

		match_odds = odds.find_one({'match': match})['odds']

		await context.channel.send(f"Zablokowano możliwość obstawiania meczu {match}")

		bets_team_a = data.find({f"Matches.{match}.winner": team_a})
		bets_team_b = data.find({f"Matches.{match}.winner": team_b})
		bets_draw = data.find({f"Matches.{match}.winner": "remis"})

		team_a_list = ""
		team_b_list = ""
		draw_list = ""

		for user in bets_team_a:
			team_a_list += f"{user['Nickname']} - {user['Matches'][match]['bet_money']}\n"

		for user in bets_team_b:
			team_b_list += f"{user['Nickname']} - {user['Matches'][match]['bet_money']}\n"

		for user in bets_draw:
			draw_list += f"{user['Nickname']} - {user['Matches'][match]['bet_money']}\n"

		if team_a_list == "":
			team_a_list += "-"
		if team_b_list == "":
			team_b_list += "-"
		if draw_list == "":
			draw_list += "-"

		embed = discord.Embed(title="Kursy", color=0xff0000, description=f"Koniec obstawiania meczu {match}, oto kursy:")
		embed.add_field(name=f"{team_a.upper()}: {match_odds[team_a]}", value=team_a_list, inline=True)
		embed.add_field(name=f"remis: {match_odds['remis']}", value=draw_list, inline=True)
		embed.add_field(name=f"{team_b.upper()}: {match_odds[team_b]}", value=team_b_list, inline=True)
		embed.set_thumbnail(url=LOGO)

		await client.get_channel(BETTING_NEWS_ID).send(embed=embed)


@client.command()
async def unblock_match(context, match):
	global blocked_bets
	if context.channel.id == BETTING_ADMIN_ID:
		blocked_bets.remove(match.lower())
		await context.channel.send(f"Odblokowano możliwość obstawiania meczu {match.lower()}")


@client.command()
async def let_join(context):
	if context.channel.id == BETTING_ADMIN_ID:
		embed = discord.Embed(title="Dołącz", color=0xff0000, description="Aby móc obstawiać mecze kliknij reakcję 🖐️!")
		embed.set_thumbnail(url=LOGO)
		await client.get_channel(JOIN_BETTING_ID).send(embed=embed)


@client.command()
async def stop_bets(context):
	global bets_possible
	if context.channel.id == BETTING_ADMIN_ID:
		bets_possible = False
		await context.channel.send("Zakłady wstrzymane!")

@client.command()
async def start_bets(context):
	global bets_possible
	if context.channel.id == BETTING_ADMIN_ID:
		bets_possible = True
		await context.channel.send("Zakłady wznowione!")

# @client.command()
# async def set_bot(context):
# 	global bets_possible
# 	overwrites_secret = {
# 				client.guilds[0].default_role: discord.PermissionOverwrite(read_messages=False),
# 				client.guilds[0].me: discord.PermissionOverwrite(read_messages=True)
# 	}
# 	# CREATING CATEGORY
# 	await client.guilds[0].create_category(name="💵moje_zaklady")
#
# 	# CREATING CHANNELS
# 	await client.guilds[0].create_text_channel(
# 		name=BETTING_NAME,
# 		overwrites=overwrites_secret,
# 		category=discord.utils.get(client.guilds[0].categories, name=CATEGORY_NAME)
# 	)
#
# 	await client.guilds[0].create_text_channel(
# 		name=JOIN_BETTING_NAME,
# 		overwrites=overwrites_secret,
# 		category=discord.utils.get(client.guilds[0].categories, name=CATEGORY_NAME)
# 	)
#
# 	await client.guilds[0].create_text_channel(
# 		name=BETTING_LOG_NAME,
# 		overwrites=overwrites_secret,
# 		category=discord.utils.get(client.guilds[0].categories, name=CATEGORY_NAME)
# 	)
#
# 	await client.guilds[0].create_text_channel(
# 		name=BETTING_NEWS_NAME,
# 		overwrites=overwrites_secret,
# 		category=discord.utils.get(client.guilds[0].categories, name=CATEGORY_NAME)
# 	)



@client.command()
async def bet(context, winner_raw, money):
	global blocked_bets
	global bets_possible
	if context.channel.name.startswith("bets"):
		winner = winner_raw.lower()
		if bets_possible:
			match_vs = context.channel.name.split("-")
			match = match_vs[1]
			if match not in blocked_bets:
				if len(context.message.content.split(' ')) == 3:
					try:
						bet_money = int(money)
					except ValueError:
						await context.channel.send("Wprowadzono złe dane!")
					else:
						if int(bet_money) > 0:
							if winner.lower() in match.split("_") or winner.lower() == "remis":
								money_status = data.find_one({"user_id": context.author.id})["Money"]
								updated_money = int(money_status) - int(bet_money)

								if updated_money >= 0:
									embed = discord.Embed(title="Postawiony zakład", color=0xff0000)
									embed.set_thumbnail(url=LOGO)
									embed.add_field(name=f"{context.author} - {match}",
													value=f"Obstawiłeś **{bet_money}** monet na **{winner}**.",
													inline=False)

									await client.get_channel(BETTING_LOG_ID).send(embed=embed)
									# await client.get_channel(BETTING_LOG_ID).send(
									# 	f"{message.author.name} obstawił/a {bet_money} monet na {winner} w meczu {match}.")

									data.update_one({"user_id": context.author.id},
													{"$set":
														{"Money": updated_money,
															f"Matches.{match}": {"winner": winner,
															"bet_money": bet_money}}})

									odds.update_one({"match": match}, {"$inc": {f"votes.{winner}": 1}})
									await context.channel.delete()
								else:
									await context.channel.send(
										f"Nie masz wystarczającej ilości pieniędzy. Posiadasz obecnie {money_status} monet.")
							else:
								await context.channel.send("Nieprawidłowa nazwa drużyny lub złe użycie komendy!")
						else:
							await context.channel.send("Nie można obstawiać za mniej niż 1.")
				else:
					await context.channel.send("Nieprawidłowe użycie komendy!")
			else:
				await context.channel.send("Obstawianie tego meczu zostało zablokowane!")
		else:
			await context.channel.send("Nie można w tej chwili obstawiać!")


# 		if msg.startswith("!set_bot"):
# 			overwrites_secret = {
# 				client.guilds[0].default_role: discord.PermissionOverwrite(read_messages=False),
# 				client.guilds[0].me: discord.PermissionOverwrite(read_messages=True)
# 			}
# 			# CREATING CATEGORY
# 			await client.guilds[0].create_category(name="💵moje_zaklady")
#
# 			# CREATING CHANNELS
# 			await client.guilds[0].create_text_channel(
# 				name=BETTING_NAME,
# 				overwrites=overwrites_secret,
# 				category=discord.utils.get(client.guilds[0].categories, name=CATEGORY_NAME)
# 			)
#
# 			await client.guilds[0].create_text_channel(
# 				name=JOIN_BETTING_NAME,
# 				overwrites=overwrites_secret,
# 				category=discord.utils.get(client.guilds[0].categories, name=CATEGORY_NAME)
# 			)
#
# 			await client.guilds[0].create_text_channel(
# 				name=BETTING_LOG_NAME,
# 				overwrites=overwrites_secret,
# 				category=discord.utils.get(client.guilds[0].categories, name=CATEGORY_NAME)
# 			)
#
# 			await client.guilds[0].create_text_channel(
# 				name=BETTING_NEWS_NAME,
# 				overwrites=overwrites_secret,
# 				category=discord.utils.get(client.guilds[0].categories, name=CATEGORY_NAME)
# 			)
#
# 		if msg.startswith("!show_servers"):
# 			for guild in client.guilds:
# 				await message.channel.send(guild.name)
#

@client.event
async def on_raw_reaction_add(payload):
	global bets_possible
	message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
	user = payload.member
	if str(message.channel) == JOIN_BETTING_NAME:
		if str(user.name) != str(message.author.name):
			if not data.find_one({"user_id": user.id}):
				# reaction = discord.utils.get(message.reactions, emoji="🖐️")
				data.insert_one({"Nickname": user.name, "Money": STARTING_CASH, "last_daily": "", "Matches": {},
								"user_id": user.id})
				embed = discord.Embed(title="Nowy użytkownik", color=0xff0000)
				embed.set_thumbnail(url=LOGO)
				embed.add_field(name=f"{user}", value=f"{user.name} został dodany do systemu!", inline=False)
				await client.get_channel(BETTING_LOG_ID).send(embed=embed)

	if str(message.channel) == BETTING_NAME:
		if str(user.name) != str(message.author.name):
			if bets_possible:
				if data.find_one({"user_id": user.id}):
					if data.find_one({"user_id": user.id})['Money'] > 0:
						match = message.embeds[0].to_dict()["fields"][0]["value"]
						match_key = match.replace(" ", "_")
						# user_matches = []

						if match_key not in data.find_one({"user_id": user.id})["Matches"]:
							data.update_one({"user_id": user.id},
											{"$set": {f"Matches.{match_key}": {"winner": "", "bet_money": 0}}})

							overwrites_private = {
								client.guilds[0].default_role: discord.PermissionOverwrite(read_messages=False),
								client.guilds[0].me: discord.PermissionOverwrite(read_messages=True),
							}

							private_channel_id = await client.guilds[0].create_text_channel(
								name=f"bets-{match}-{user.name}",
								overwrites=overwrites_private,
								category=discord.utils.get(client.guilds[0].categories, name="💵moje_zaklady")
							)
							perms = private_channel_id.overwrites_for(user)
							await private_channel_id.set_permissions(user, read_messages=not perms.read_messages)

							match_channel = client.get_channel(private_channel_id.id).name.split('-')[1]

							instruction_betting = f"Aby postawić monety użyj komendy !bet <tag><monety>.\nPrzykład: \n"f"!bet {match_channel.split('_')[0]} 50\n"f"!bet {match_channel.split('_')[2]} 50\n"f"Aby obstawić remis, zamiast tagu drużyny należy wpisać 'remis' - !bet remis 50\n"f"Użyj komendy !money, by sprawdzić swój stan konta."
							embed = discord.Embed(title="Instrukcja", description=instruction_betting, color=0xff0000)
							embed.set_thumbnail(url=LOGO)
							await client.get_channel(private_channel_id.id).send(embed=embed)
							await client.get_channel(private_channel_id.id).send(user.mention)


client.run("ODMxNDc3MjI4NzI1ODYyNDAw.YHVzgw.PyUjMHP08L6GOH5FFI2hizUpO5Q")
