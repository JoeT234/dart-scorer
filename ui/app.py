"""
Main application shell — manages screen transitions.
"""
import tkinter as tk
from ui.theme import BG
from ui.screens.welcome import WelcomeScreen
from ui.screens.setup import SetupScreen
from ui.screens.tutorial import TutorialScreen
from ui.screens.game import GameScreen


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dart Scorer")
        self.configure(bg=BG)
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.resizable(True, True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._current_screen = None
        self.show_welcome()

    def _switch(self, screen):
        if self._current_screen:
            self._current_screen.destroy()
        self._current_screen = screen
        screen.grid(row=0, column=0, sticky="nsew")
        screen.tkraise()

    def show_welcome(self):
        self._switch(WelcomeScreen(
            self,
            on_start=self.show_setup,
            on_tutorial=self.show_tutorial,
        ))

    def show_setup(self):
        self._switch(SetupScreen(
            self,
            on_start_game=self.show_game,
            on_back=self.show_welcome,
        ))

    def show_tutorial(self):
        self._switch(TutorialScreen(
            self,
            on_back=self.show_welcome,
        ))

    def show_game(self, **game_config):
        self._switch(GameScreen(
            self,
            game_config=game_config,
            on_back=self.show_welcome,
        ))
