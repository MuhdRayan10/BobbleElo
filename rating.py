

def calculate_rating(player1, player2, result):
    outcome = 1 / (1 + (10**((player1 - player2) / 400)))

    rating1 = player1 + (32 * (result - outcome))
    rating2 = player2 + (32 * ((not result if result != 0.5 else 0.5) - outcome))

    return round(rating1, 2), round(rating2, 2)


def calculate_team_rating(team1, team2, result):
    team1_r = sum(team1)/len(team1)
    team2_r = sum(team2)/len(team2)

    new_ratings = calculate_rating(team1_r, team2_r, result)

    change1, change2 = new_ratings[0] - team1_r, new_ratings[1] - team2_r

    return [round(change1+p) for p in team1], [round(change2+p) for p in team2]


