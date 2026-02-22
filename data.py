"""In-memory data model for the todo app."""

from dataclasses import dataclass, field


@dataclass
class TodoList:
    name: str
    items: list[str] = field(default_factory=list)


@dataclass
class AppData:
    lists: list[TodoList] = field(default_factory=list)

    def list_names(self) -> list[str]:
        return [lst.name for lst in self.lists]

    def get_list(self, index: int) -> TodoList:
        return self.lists[index]

    def add_list(self, name: str) -> TodoList:
        lst = TodoList(name=name)
        self.lists.append(lst)
        return lst

    def move_list_to_front(self, index: int) -> None:
        if index == 0:
            return
        self.lists.insert(0, self.lists.pop(index))

    def move_item_to_top(self, list_index: int, item_index: int) -> None:
        lst = self.lists[list_index]
        if item_index == 0:
            return
        lst.items.insert(0, lst.items.pop(item_index))

    def move_item(self, from_list: int, from_index: int, to_list: int, to_index: int) -> None:
        item = self.lists[from_list].items.pop(from_index)
        self.lists[to_list].items.insert(to_index, item)
