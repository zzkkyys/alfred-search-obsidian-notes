# %%
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import List

# %%
@dataclass
class Alfred_Item:
    title: str
    subtitle: str
    valid: bool = True
    match: str = None
    arg: str = None
    icon: str = None
    
    def __post_init__(self) -> None:
        if self.match is None:
            self.match = "{} {}".format(self.title, self.subtitle)

    def to_dict(self):
        return self.__dict__

def custom_serializer(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


# %%
@dataclass
class Alfred:
    items: List[Alfred_Item] = field(default_factory=list) 
    

    @staticmethod
    def log_info(info:str, *args, **kwargs):
        """log information to the Alfred debug terminal

        Args:
            info (str): some info ...
        """
        print("Log info: ", info, *args, file=sys.stderr)

    
    def output_items(self, items=None):
        
        if items is None:
            items = self.items
        
        if not isinstance(items, list):
            items = [items]
        json.dump(dict(items=items), sys.stdout, default=custom_serializer)
    
    def add_item(self,title, subtitle, arg, valid=True,icon=None, match=None, *args, **kwargs):
        _item = Alfred_Item(
            title=title,
            subtitle=subtitle,
            match="{} {}".format(title, subtitle),
            arg=arg,
            icon=icon,
            valid=valid,
        )
        self.items.append(_item.__dict__)
        return _item