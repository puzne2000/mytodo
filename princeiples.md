# Purpose of this document
This document gives some rough requirements of a todo app that I would like to create

## UI organization
-- Each todo item is just a rectangle text-box. The text is wrpped inside it
-- todo items can be editted in place
-- todo itmes belongs to lists, and each list is organized as a tab
-- todo items can easily be reordered within a list by dragging it with a mouse
-- each list appears on screen as a tab, clicking on a tab shows its list
-- todo items can be dragged from one list to another
-- each todo item has a "hot zone". double clicking the hot zone moves the item to the top of the list
-- the tabs with the list names also have clickable hot zones - double clicking a hot zone moves the list to the leftmost position
-- each operation can be undone using the ctrl+z

## Infrastructure
-- The lists are maintined in a simple text file which is easily human readable
-- the app should be easy to maintain and expand

