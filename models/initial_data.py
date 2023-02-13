from dataclasses import dataclass
from typing import List, Set

from ordered_set import OrderedSet

from serializer import DataClassJSONSerializer
from conftest import data_string


@dataclass
class InitItem(DataClassJSONSerializer):
    id: str
    title: str

    @classmethod
    def _post_deserialize_id(cls, obj):
        """
        >>> InitItem._post_deserialize_id(InitItem(id="tt1233333", title=""))
        >>> InitItem._post_deserialize_id(InitItem("string", ""))
        Traceback (most recent call last):
        AssertionError: Not starting with tt
        """
        assert obj.id.startswith('tt'), "Not starting with tt"


@dataclass
class InitialData(DataClassJSONSerializer):
    """
    >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": ""}, {"id":"tt1233334", "title": ""}], "title": ""})
    InitialData(items=[InitItem(id='tt1233333', title=''), InitItem(id='tt1233334', title='')], title='')
    >>> InitialData.from_json('{"items": [{"id":"tt1233333", "title": ""}, {"id":"tt1233334", "title": ""}], "title": ""}')
    InitialData(items=[InitItem(id='tt1233333', title=''), InitItem(id='tt1233334', title='')], title='')
    """
    items: List[InitItem]
    title: str

    def ids_items(self) -> List[dict]:
        """
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": ""}, {"id":"tt1233334", "title": ""}], "title": ""}).ids_items()
        [{'id': 'tt1233333'}, {'id': 'tt1233334'}]
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": ""}], "title": ""}).ids_items()
        [{'id': 'tt1233333'}]
        """
        return [{"id": str(item.id)} for item in self.items]

    def ids_to_set(self) -> OrderedSet[str]:
        """
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": ""}, {"id":"tt1233334", "title": ""}], "title": ""}).ids_to_set()
        OrderedSet(['tt1233333', 'tt1233334'])
        >>> InitialData.from_dict({"items": [{"id": "tt1233333", "title": ""}], "title": ""}).ids_to_set()
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
        InitialData(items=[InitItem(id='tt1233334', title='1.Вышка'), InitItem(id='tt1233332', title='2.Джунгли')], title='Suspense, Survey .1.')
        """

        string = self.string.split("\n")
        items = []

        for item in string[1:]:
            split_item = item.split("|")
            items.append(
                InitItem.from_dict({"id": split_item[1].strip(), "title": split_item[0].strip()})
            )

        return InitialData(items=items, title=string[0])
