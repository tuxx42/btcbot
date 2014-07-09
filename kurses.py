#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses
import curses.textpad
import cmd


def maketextbox(h,w,y,x,value="",deco=None,textColorpair=0,decoColorpair=0):
    # thanks to http://stackoverflow.com/a/5326195/8482 for this
    nw = curses.newwin(h,w,y,x)
    txtbox = curses.textpad.Textbox(nw,insert_mode=True)
    if deco=="frame":
        screen.attron(decoColorpair)
        curses.textpad.rectangle(screen,y-1,x-1,y+h,x+w)
        screen.attroff(decoColorpair)
    elif deco=="underline":
        screen.hline(y+1,x,underlineChr,w,decoColorpair)

    nw.addstr(0,0,value,textColorpair)
    nw.attron(textColorpair)
    screen.refresh()
    return nw,txtbox

class Commands(cmd.Cmd):
    """Simple command processor example."""

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "> "
        self.intro  = "Welcome to console!"  ## defaults to None

    def do_greet(self, line):
	self.write("hello "+line)

    def default(self,line) :
	self.write("Don't understand '" + line + "'")

    def do_quit(self, line):
	curses.endwin()
        return True

    def write(self,text) :
        screen.clear()
	textwin.clear()
        screen.addstr(3,0,text)
        screen.refresh()


if __name__ == '__main__':
    screen = curses.initscr()
    curses.noecho()
    textwin,textbox = maketextbox(1,40, 1,1,"")
    flag = False
    while not flag :
        text = textbox.edit()
	curses.beep()
        flag = Commands().onecmd(text)
