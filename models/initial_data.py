from dataclasses import dataclass
from typing import List, Set

from ordered_set import OrderedSet

from serializer import DataClassJSONSerializer

data_string = "Suspense, Survey .1.#1.Вышка | tt1233334 | background_audio | Fall Description#2.Джунгли | tt1233332 | background_audio | Jungle Description"


@dataclass
class InitItem(DataClassJSONSerializer):
    id: str
    title: str
    description: str
    background_audio: str

    @classmethod
    def _post_deserialize_id(cls, obj):
        """
        >>> InitItem._post_deserialize_id(InitItem(id="tt1233333", title="", description="", background_audio=""))
        >>> InitItem._post_deserialize_id(InitItem("string", "", "", ""))
        Traceback (most recent call last):
        AssertionError: Not starting with tt
        """
        assert obj.id.startswith('tt'), "Not starting with tt"


@dataclass
class InitialData(DataClassJSONSerializer):
    """
    >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": "", "description": "", "background_audio": ""}, {"id":"tt1233334", "title": "", "description": "", "background_audio": ""}], "title": ""})
    InitialData(items=[InitItem(id='tt1233333', title='', description='', background_audio=''), InitItem(id='tt1233334', title='', description='', background_audio='')], title='')
    >>> InitialData.from_json('{"items": [{"id":"tt1233333", "title": "", "description": "", "background_audio": ""}, {"id":"tt1233334", "title": "", "description": "", "background_audio": ""}], "title": ""}')
    InitialData(items=[InitItem(id='tt1233333', title='', description='', background_audio=''), InitItem(id='tt1233334', title='', description='', background_audio='')], title='')
    """
    items: List[InitItem]
    title: str

    def items_to_dict(self):
        return {item.id: item for item in self.items}

    def ids_items(self) -> List[dict]:
        """
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": "", "description": "", "background_audio": ""}, {"id":"tt1233334", "title": "", "description": "", "background_audio": ""}], "title": ""}).ids_items()
        [{'id': 'tt1233333'}, {'id': 'tt1233334'}]
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": "", "description": "", "background_audio": ""}], "title": ""}).ids_items()
        [{'id': 'tt1233333'}]
        """
        return [{"id": str(item.id)} for item in self.items]

    def ids_to_set(self) -> OrderedSet[str]:
        """
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": "", "description": "", "background_audio": ""}, {"id":"tt1233334", "title": "", "description": "", "background_audio": ""}], "title": ""}).ids_to_set()
        OrderedSet(['tt1233333', 'tt1233334'])
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": "", "description": "", "background_audio": ""}], "title": ""}).ids_to_set()
        OrderedSet(['tt1233333'])
        """
        return OrderedSet([item.id for item in self.items])

    @classmethod
    def items_id_to_query_string(cls, ids: OrderedSet) -> str:
        """
        >>> InitialData.items_id_to_query_string(OrderedSet(["tt1233333", "tt1233334"]))
        '?ids=tt1233333&ids=tt1233334'
        >>> InitialData.items_id_to_query_string(OrderedSet(["tt1233333"]))
        '?ids=tt1233333'
        """
        str_ = "&ids=".join(tuple(map(lambda i: str(i), ids)))
        return f"?ids={str_}"


@dataclass
class ParseInitialData(DataClassJSONSerializer):
    string: str

    @classmethod
    def _post_deserialize_string(cls, obj):
        obj.string = obj.string.strip()

    def from_string(self):
        """
        >>> ParseInitialData.from_dict({"string": data_string}).from_string()
        InitialData(items=[InitItem(id='tt1233334', title='Вышка', description='Fall Description', background_audio='background_audio'), InitItem(id='tt1233332', title='Джунгли', description='Jungle Description', background_audio='background_audio')], title='Suspense, Survey .1.')
        """

        string = self.string
        items = []

        for item in string[1:]:
            split_item = item.split("|")
            items.append(
                InitItem.from_dict({"id": split_item[1].strip(), "title": split_item[0].strip().split('.')[1], "background_audio": split_item[2].strip(), "description": split_item[3].strip()})
            )

        return InitialData(items=items, title=string[0])
