from config import *
from constants import *
from utils import *
import pandas as pd
import requests as rq
import json
from IPython.core.display import HTML


def get_puuid():
    """Returns user's puuid"""
    url = PUUID_URL.format(CONTINENT_BASE_URL, INGAME_NAME, USER_TAG, API_KEY)
    response = rq.get(url)
    return json.loads(response.text)["puuid"]


def get_current_version():
    """Returns current LoL's version"""
    response = rq.get(LOL_VERSION_URL)
    return json.loads(response.text)[0]


def get_champions(cur_version):
    """Returns a dataframe with champ's names and champ ids"""
    url = LOL_CHAMPIONS_URL.format(cur_version, LANG)
    response = rq.get(url)
    table = json.loads(response.text)["data"]
    updated_table = pd.DataFrame(table).T
    updated_table = updated_table.astype({"key": int})
    return updated_table[["key", "name"]].sort_values("key")


def get_champ_images():
    """Returns a dataframe with champ's names, ids and icons"""
    table = get_champions(get_current_version())
    table["champImage"] = (
        f"https://ddragon.leagueoflegends.com/cdn/{get_current_version()}/img/champion/"
        + table.index.astype(str)
        + ".png"
    )
    return table


def get_champion_mastery(puuid):
    """Returns a dataframe with champ's names, ids, icons and mastery level"""
    data_table = get_champ_images()
    champ_number = data_table.shape[0]
    url = LOL_CHAMP_MASTERY.format(SERVER_BASE_URL, puuid, champ_number, API_KEY)
    response = rq.get(url)
    table = pd.DataFrame(json.loads(response.text))[
        [
            "championId",
            "championLevel",
            "tokensEarned",
            "chestGranted",
            "championPoints",
            "championPointsUntilNextLevel",
            "lastPlayTime",
        ]
    ]
    table["lastPlayTime"] = table["lastPlayTime"].apply(convert_timestamp_to_data)

    return (
        pd.merge(data_table, table, left_on="key", right_on="championId")
        .drop(["key", "championId"], axis=1)
        .sort_values(
            ["championLevel", "tokensEarned", "championPoints", "chestGranted"],
            ascending=[False, False, False, True],
        )
    )


def apply_format(puuid, mode="token"):
    """Return customized results
    - token: shows closest champs to level 7
    - max: shows top champs mastery points
    - level: shows champs closest to level 5
    - chest: shows champs without collecting chest
    """
    table = get_champion_mastery(puuid)
    if mode == "token":
        new_table = table[
            ~(table["championLevel"] == 7)
            & ~((table["championLevel"] == 6) & (table["tokensEarned"] == 3))
        ]
    elif mode == "max":
        new_table = table[
            (table["championLevel"] == 7)
            | ((table["championLevel"] == 6) & (table["tokensEarned"] == 3))
        ]
    elif mode == "level":
        new_table = table[table["championLevel"] < 5]
    elif mode == "chest":
        new_table = table[table["chestGranted"] == False]

    if mode != "level":
        new_table = new_table.drop('championPointsUntilNextLevel', axis=1)
    else:
        new_table = new_table.drop('championPoints', axis=1)

    new_table = new_table.set_index("name").reset_index()

    return new_table


def check_champs(nb_champs=10, mode="token"):
    """Returns first {nb_champs} instances for each mode"""
    table = apply_format(get_puuid(), mode)
    table = table.head(nb_champs).to_html(
        escape=False, formatters=dict(champImage=path_to_image_html)
    )
    return HTML(table)
