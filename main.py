import asyncio

from api.get_meta_data import GetMetaData

data = {
    "title": "action",
    "items": [
        {
            "title": {"en": "John Wick: Chapter 4"},
            "id": "tt10366206"
        },
        {
            "title": {"en": "Top Gun: Maverick"},
            "id": "tt1745960"
        },
        {
            "title": {"en": "Fast X"},
            "id": "tt5433140"
        },
        {
            "title": {"en": "Extraction 2"},
            "id": "tt12263384"
        },
        {
            "title": {"en": "The Batman"},
            "id": "tt1877830"
        },
        {
            "title": {"en": "Mission: Impossible – Dead Reckoning Part One"},
            "id": "tt9603212"
        },
        {
            "title": {"en": "Bullet Train"},
            "id": "tt12593682"
        },
        {
            "title": {"en": "The Equalizer 3"},
            "id": "tt17024450"
        },
        {
            "title": {"en": "Godzilla x Kong: The New Empire"},
            "id": "tt14539740"
        },
        {
            "title": {"en": "Rebel Moon: Part One – A Child of Fire"},
            "id": "tt14998742"
        }
    ]
}


async def handler(_data: dict):
    await GetMetaData(data=_data).run()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(handler(data))
