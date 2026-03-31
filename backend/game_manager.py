from enum import Enum
from collections.abc import Callable
from backend.buzzer_manager import *
from backend.SpotifyPlayer import *
from backend.spotify_playlist import *
import socket
import json
import random
from pathlib import Path

PLAYLISTS_FILE = Path(__file__).parent.parent / "assets" / "playlists" / "playlists.json"

class GameWebsocketConnection:
    websocket: WebSocket
    on_disconnect_callback: Callable

    on_message_listeners: list[Callable] = []

    def __init__(self, websocket: WebSocket, on_disconnect_callback: Callable):
        self.websocket = websocket
        self.on_disconnect_callback = on_disconnect_callback
        self.on_message_listeners = []

    def register_on_message_cb(self, cb: Callable):
        self.on_message_listeners.append(cb)

    async def poll_websocket_until_error(self):
        try:
            while True:
                # Empfange Button-Daten
                data = await self.websocket.receive_text()
                msg = json.loads(data)

                for cb in self.on_message_listeners:
                    cb(self, msg)
                
        except WebSocketDisconnect as e:
            # Manager bereinigt sich selbst in send_to_buzzer, 
            # aber wir printen es hier zur Info
            print(f'exception: {e}')
            if self.on_disconnect_callback is not None:
                self.on_disconnect_callback(self)

class Player:
    id: str
    name: str
    avatar_url: str
    buzzer: Buzzer
    sound: str
    color: str
    ready: bool = False
    judge: bool = False
    points: int = 0
    eliminated: bool = False

    def __init__(self, id: str, name: str, avatar_url: str, color: str, buzzer: Buzzer, sound: str, points: int = 0):
        self.id = id
        self.name = name
        self.avatar_url = avatar_url
        self.color = color
        self.buzzer = buzzer
        self.sound = sound
        self.ready = False
        self.judge = False
        self.points = points
        self.eliminated = False
        pass

    def toDict(self):
        return {
            'name': self.name,
            'id': self.id,
            'avatar_url': self.avatar_url,
            'sound': self.sound,
            'color': self.color,
            'buzzer': self.buzzer.toDict(),
            'ready': self.ready,
            'judge': self.judge,
            'points': self.points,
            'eliminated': self.eliminated
        }
    
    def toggle_ready(self):
        self.ready = not self.ready

class ProgrammingError(TypeError):  # hehe
    pass

"""
1 PLAYER_REGISTRATION_WAIT_EVERYONE_READY   -> 2
2 INGAME_JUDGE_ASSIGNMENT                   -> 3
3 INGAME_MUSIC_PLAYING                      -> 4
4 INGAME_BUZZED                             -> 3, 5
5 INGAME_SONG_END                           -> 2, 6
6 INGAME_ROUND_END                          -> 1
"""

class GameState(Enum):
	UNDEFINED = -1
	UDP_BROADCAST_SETUP = "UDP_BROADCAST_SETUP",
	PLAYER_REGISTRATION_WAIT_EVERYONE_READY = "PLAYER_REGISTRATION_WAIT_EVERYONE_READY",
	INGAME_JUDGE_ASSIGNMENT = "INGAME_JUDGE_ASSIGNMENT",
	INGAME_MUSIC_PLAYING = "INGAME_MUSIC_PLAYING",
	INGAME_BUZZED = "INGAME_BUZZED",
	INGAME_SONG_END = "INGAME_SONG_END",
	INGAME_ROUND_END = "INGAME_ROUND_END"

class GameManager:
    pass

class AbstractGameStateManager:

    _name = "AbstractGameStateManager"
    _foreign = False

    _handled_state: GameState
    _game_manager: GameManager

    abort = False

    def __init__(self, game_manager: GameManager, game_state: GameState = GameState.UNDEFINED):
        self._game_manager = game_manager
        if game_state is GameState.UNDEFINED:
            print('[WARN] you should never ever see this warning, as this is an abstract class')
        self._handled_state = game_state

    async def run_state_loop(self):
        raise ProgrammingError("this is an abstract method, go implement it in your subclass!")

    async def on_state_enter(self):
        raise ProgrammingError("this is an abstract method, go implement it in your subclass!")

    async def on_state_leave(self):
        raise ProgrammingError("this is an abstract method, go implement it in your subclass!")

    async def handle_buzzer_message(self, buzzer: Buzzer, message: dict):
        raise ProgrammingError("this is an abstract method, go implement it in your subclass!")
    
    async def update_buzzers(self):
        raise ProgrammingError("this is an abstract method, go implement it in your subclass!")
    

# ++++ GameStateHandlers - logic for state transitions between gamestates ++++

class PlayerRegistrationWaitEveryoneReadyManager(AbstractGameStateManager):
    def __init__(self, game_manager: GameManager):
        super().__init__(game_manager, GameState.PLAYER_REGISTRATION_WAIT_EVERYONE_READY)
        self._name = "PlayerRegistrationWaitEveryoneReadyManager"

    async def on_state_enter(self):
        print(f'[{self._name}] on_state_enter')
        # ensure all buzzers are in a sane state
        for buzzer in self._game_manager.buzzer_manager.active_buzzers:
            if buzzer.get_state() not in [BuzzerState.PreGameConnectedAssignedNotReady, BuzzerState.PreGameConnectedAssignedReady, BuzzerState.PreGameConnectedUnassigned]:
                # we have a different state .. check if previously assigned
                try:
                    player = self._game_manager.player_for_buzzer_id(buzzer.id)
                    player.ready = False
                    buzzer.set_state(BuzzerState.PreGameConnectedAssignedNotReady)
                except:
                    buzzer.set_state(BuzzerState.PreGameConnectedUnassigned)
    
    async def on_state_leave(self):
        print(f'[{self._name}] on_state_leave')
        # initialize spotify playlist manager here
        self._game_manager.initialize_spotify_playlist_manager()

    async def run_state_loop(self):
        while not self.ensure_all_players_ready() or not self.ensure_at_least_one_playlist():
            await asyncio.sleep(0.5)
        # trigger state transition to next state
        self._game_manager.set_state(GameState.INGAME_JUDGE_ASSIGNMENT)

    async def handle_buzzer_message(self, buzzer: Buzzer, message: dict):
        print(f'[{self._name}] buzzer={buzzer.mac} id={buzzer.id} message={message}')
        value = message['val']
        if value == BuzzerButton.BIG:
            # handle big button buzzer
            # toggle player ready
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            player.toggle_ready()
            player.buzzer.set_state(BuzzerState.PreGameConnectedAssignedReady if player.ready else BuzzerState.PreGameConnectedAssignedNotReady)
            await self._game_manager.broadcast_state()
            self.ensure_all_players_ready()           
        else:
            print(f'[{self._name}] unhandled buzzer button value={value}')

    def ensure_all_players_ready(self):
        enough_players = len(self._game_manager.players) >= self._game_manager.game_settings['numPlayers']
        all_ready = all(player.ready for player in self._game_manager.players) and len(self._game_manager.players)
        if all_ready and enough_players:
            return True
        else:
            return False
        
    def ensure_at_least_one_playlist(self) -> bool:
        return len(self._game_manager.game_settings["playlists"]) > 0

    async def update_buzzers(self):
        unassigned_buzzers = self._game_manager.buzzer_manager.get_by_states([BuzzerState.PreGameConnectedUnassigned])
        assigned_buzzers_ready = self._game_manager.buzzer_manager.get_by_states([BuzzerState.PreGameConnectedAssignedReady])
        assigned_buzzers_notready = self._game_manager.buzzer_manager.get_by_states([BuzzerState.PreGameConnectedAssignedNotReady])

        for buzzer in unassigned_buzzers:
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 2, f'#{buzzer.id}', True, "fullscreen",3)
        for buzzer in assigned_buzzers_notready:
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{player.name}', True,"", 2)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 4, f'Buzzer druecken!', False)
        for buzzer in assigned_buzzers_ready:
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{player.name}', True)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 3, f'Bereit!', False, "", 2)

class IngameJudgeAssignmentManager(AbstractGameStateManager):
    _btn_mutex: int = 1
    _judge_ack = False

    def __init__(self, game_manager: GameManager):
        super().__init__(game_manager, GameState.INGAME_JUDGE_ASSIGNMENT)
        self._name = "IngameJudgeAssignmentManager"

    async def on_state_enter(self):
        print(f'[{self._name}] on_state_enter')
        self._btn_mutex = 1
        self._judge_ack = False
        # all buzzers which have been ready and assigned must move to InGameRandomJudgeAssign
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.PreGameConnectedAssignedReady, BuzzerState.InGameAfterSong]):
            buzzer.set_state(BuzzerState.InGameRandomJudgeAssign)
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'Spieler {player.name}', True)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 1, f' ', False)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 2, f'Bestimmung des Judge ..', False)
        await self._game_manager.write_buzzer_colors()

    async def on_state_leave(self):
        print(f'[{self._name}] on_state_leave')
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameRandomJudgeAssign]):
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'Spieler {player.name}', True)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 1, f' ', False)
            if player.judge:
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 2, f'>> Judge <<', False)
            else:
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 2, f'>> Spieler <<', False)
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 4, f'Bereit machen!', True)
        if self._game_manager.sp_manager is None:
            raise ValueError('SpotifyPlaylist manager not yet initialized!!!!')
        self._game_manager.sp_player.startsong(self._game_manager.sp_manager.current_track, start_second=self._game_manager.game_settings["startSecond"])

    async def write_assignment_results(self):
        # select random song from playlist and start 
        if self._game_manager.sp_manager is None:
            raise ValueError('SpotifyPlaylist manager not yet initialized!!!!')
        song = self._game_manager.sp_manager.getrandomsong()
        self._game_manager.sp_manager.current_track = song
        title = song["title"]
        artist = song["artist"]
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameRandomJudgeAssign]):
            player = self._game_manager.player_for_buzzer_id(buzzer.id)

            if player.judge:
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{title}', True, "",1 )
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 3, f'{artist}', False, "",1)
            else:
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{player.name}', True)
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 1, f' ', False)
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 2, f'Spieler', False, "", 3)

    async def run_state_loop(self):
        i = 0
        while len([p for p in self._game_manager.players if p.judge]) < 1 and i < 10:
            await asyncio.sleep(0.5)
            i += 1 # timeout of 5 seconds
        if i >= 10:
            # trigger assignment manually
            await self.assign_judge()
        # when done, write data to buzzers to inform who is who
        await self.write_assignment_results()
        while self._judge_ack is False and self.abort is False:
            await asyncio.sleep(0.5)
        if self.abort:
            # this has been aborted, reset to state PlayerRegistration
            self._game_manager.set_state(GameState.PLAYER_REGISTRATION_WAIT_EVERYONE_READY)
        else:
            self._game_manager.set_state(GameState.INGAME_MUSIC_PLAYING)

    async def assign_judge(self):
        self._btn_mutex -= 1
        if self._game_manager.judge_index < 0:
            print(f'[{self._name}] assigning random judge NOW!!')
            # get random number 10 times, add them together
            random_sum = 0
            for i in range(10):
                random_sum += random.randint(0, 100)
            self._game_manager.judge_index = random_sum % len(self._game_manager.players)
        else:
            print(f'[{self._name}] moving judge once more around')
            self._game_manager.judge_index = (self._game_manager.judge_index + 1) % len(self._game_manager.players)
        targetIndex = self._game_manager.judge_index
        # unset judge flag on all players
        for player in self._game_manager.players:
            player.judge = False

        # set judge on this index
        self._game_manager.players[targetIndex].judge = True
        self._game_manager.current_judge = self._game_manager.players[targetIndex]
        await self._game_manager.broadcast_state()

    async def handle_buzzer_message(self, buzzer: Buzzer, message: dict):
        # any button triggers the judge-assignment
        if self._btn_mutex > 0:
            await self.assign_judge()
        # else ignore, we're already in the assignment OR we're waiting for the judge to accept
        if self._game_manager.buzzer_is_judge(buzzer.id) and message['val'] == BuzzerButton.BIG:
            self._judge_ack = True

    async def update_buzzers(self):
        pass


class InGameMusicPlayingManager(AbstractGameStateManager):
    _player_buzz: Player = None
    _playing = True
    _judge_decision = None
    
    def __init__(self, game_manager: GameManager):
        super().__init__(game_manager, GameState.INGAME_MUSIC_PLAYING)
        self._name = "InGameMusicPlayingManager"

    async def run_state_loop(self):
        # music playing .. wait until some player presses the buzzer
        while self._judge_decision is None and self.abort is not True:
            # emit music state
            try:
                if self._playing and not self._game_manager.sp_player.playing:
                    self._game_manager.sp_player.play()
                elif not self._playing and self._game_manager.sp_player.playing:
                    self._game_manager.sp_player.pause()
            except:
                pass
            await asyncio.sleep(0.1)
            allbuzzers = self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameJudgeMusicPlaying, BuzzerState.InGamePlayerMusicPlaying, BuzzerState.InGameJudgeBuzzedDecision, BuzzerState.InGamePlayerBuzzed, BuzzerState.InGamePlayerNotBuzzed, BuzzerState.InGamePlayerWon])
            if len(allbuzzers) < 2:
                    self.abort = True
        self._game_manager.set_state(GameState.INGAME_SONG_END)

    async def on_state_enter(self):
        self._player_buzz = None
        self._playing = True
        self._judge_decision = None
        self.abort = False
        print(f'[{self._name}] on_state_enter')
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameRandomJudgeAssign]):
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            if player.judge:
                song = self._game_manager.sp_player.current_track
                title = song["title"]
                artist = song["artist"]
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{title}', True, "",1 )
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 3, f'{artist}', False, "",1)
                buzzer.set_state(BuzzerState.InGameJudgeMusicPlaying)
            else:
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{player.name}', True)
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 1, f' ', False)
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 2, f'???', False, "", 3)
                buzzer.set_state(BuzzerState.InGamePlayerMusicPlaying)
        
    async def on_state_leave(self):
        print(f'[{self._name}] on_state_leave')
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameJudgeMusicPlaying, BuzzerState.InGamePlayerMusicPlaying, BuzzerState.InGameJudgeBuzzedDecision, BuzzerState.InGamePlayerBuzzed, BuzzerState.InGamePlayerEliminated, BuzzerState.InGamePlayerNotBuzzed, BuzzerState.InGamePlayerWon]):
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'Spieler {player.name}', True)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 1, f' ', False)
            if player.judge:
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 2, f'>> Judge <<', False)
            else:
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 2, f'>> Spieler <<', False)
            song = self._game_manager.sp_player.current_track
            title = song["title"]
            artist = song["artist"]
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 3, f'{title}', False)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 4, f'{artist}', False)
            if self._player_buzz is not None:
                if buzzer.id == self._player_buzz.buzzer.id:
                    # round end and we're the buzzer -> won
                    await self._game_manager.buzzer_manager.writetext(buzzer.mac, 5, f'Korrekt!', False, "fullscreen")
                else:
                    await self._game_manager.buzzer_manager.writetext(buzzer.mac, 5, f'Spieler {self._player_buzz.name} hat gewonnen', False)
            else:
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 5, f'Kein Gewinner', False)
        self._game_manager.sp_player.play()
        self._game_manager.current_judge = None
         # get winner
        winner = self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGamePlayerWon])
        if len(winner) > 0:
            player = self._game_manager.player_for_buzzer_id(winner[0].id)
            player.points += 1

    async def handle_buzzer_message(self, buzzer: Buzzer, message: dict):
        print(f'[{self._name}] handle_buzzer_message')

        if self._game_manager.buzzer_is_judge(buzzer.id):
            # judge pressed something..
            if message['val'] == BuzzerButton.BIG:
                if self._player_buzz is None:
                    self._playing = not self._playing # toggle playing / pause
            elif self._player_buzz is not None:
                # we got a buzz from a player, only decide on OK / FAIL
                if message['val'] == BuzzerButton.LEFT:
                    # FAIL
                    self._player_buzz.eliminated = True
                    self._player_buzz.buzzer.set_state(BuzzerState.InGamePlayerEliminated)
                    self._player_buzz = None
                    # check if there is any player left, abort otherwise
                    allbuzzers = self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameJudgeMusicPlaying, BuzzerState.InGamePlayerMusicPlaying, BuzzerState.InGameJudgeBuzzedDecision, BuzzerState.InGamePlayerBuzzed, BuzzerState.InGamePlayerNotBuzzed, BuzzerState.InGamePlayerWon])
                    # one judge
                    if len(allbuzzers) < 2:
                        self.abort = True
                    else:
                        # continue playing as there are players left
                        self._playing = True
                elif message['val'] == BuzzerButton.RIGHT:
                    self._player_buzz.buzzer.set_state(BuzzerState.InGamePlayerWon)
                    self._judge_decision = True
                    await self._game_manager.write_buzzer_colors()
        else:
            if self._player_buzz is None and buzzer.get_state() != BuzzerState.InGamePlayerEliminated:
                # player buzzed!
                player = self._game_manager.player_for_buzzer_id(buzzer.id)
                if message['val'] == BuzzerButton.BIG:
                    self._player_buzz = player
                    self._playing = False
                    buzzer.set_state(BuzzerState.InGamePlayerBuzzed)
                elif message['val'] == BuzzerButton.LEFT:
                    # Spieler eliminiert sich selbst für diese Runde
                    player.eliminated = True
                    player.buzzer.set_state(BuzzerState.InGamePlayerEliminated)
                    await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{player.name}', True)
                    await self._game_manager.buzzer_manager.writetext(buzzer.mac, 4, f'Ausgeschieden ...', False)
                    await self._game_manager.buzzer_manager.setled(buzzer.mac, '#000000') # LED aus
                    # Optional: Sound abspielen für "falsch"
                    # await self._game_manager.buzzer_manager.playsound(buzzer.mac, "wrong.mp3") 
                    self._check_abort_condition()
            else:
                print(f'already buzzed!')
        await self._game_manager.broadcast_state()

    def _check_abort_condition(self):
        # Alle Zustände einschließen, die bedeuten, dass ein Spieler noch aktiv ist
        active_players = self._game_manager.buzzer_manager.get_by_states([
            BuzzerState.InGamePlayerMusicPlaying, 
            BuzzerState.InGamePlayerBuzzed,
            BuzzerState.InGamePlayerNotBuzzed # WICHTIG!
        ])
        
        # Wenn kein Spieler mehr aktiv ist, breche ab
        if len(active_players) < 1:
            self.abort = True
            print("Runde abgebrochen: Keine Spieler übrig.")
    
    async def update_buzzers(self):
        print(f'[{self._name}] update_buzzers')
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameJudgeMusicPlaying, BuzzerState.InGamePlayerMusicPlaying, BuzzerState.InGameJudgeBuzzedDecision, BuzzerState.InGamePlayerBuzzed, BuzzerState.InGamePlayerEliminated, BuzzerState.InGamePlayerNotBuzzed, BuzzerState.InGamePlayerWon]):
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{player.name}', True)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 1, f' ', False)
            if player.judge:
                song = self._game_manager.sp_player.current_track
                title = song["title"]
                artist = song["artist"]
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'{title}', True, "",1 )
                await self._game_manager.buzzer_manager.writetext(buzzer.mac, 3, f'{artist}', False, "",1)
                if self._player_buzz is not None:
                    await self._game_manager.buzzer_manager.writetext(buzzer.mac, 5, f'Spieler {self._player_buzz.name} hat gebuzzed!', False)
                    buzzer.set_state(BuzzerState.InGameJudgeBuzzedDecision)
            else:
                #await self._game_manager.buzzer_manager.writetext(buzzer.mac, 3, f'', False)
                if self._player_buzz is not None:
                    if self._player_buzz.id == player.id:
                        # we have buzzed
                        if buzzer.get_state() != BuzzerState.InGamePlayerWon:
                            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'Deine Antwort?', True, "", 3)
                            buzzer.set_state(BuzzerState.InGamePlayerBuzzed)
                    else:
                        await self._game_manager.buzzer_manager.writetext(buzzer.mac, 3, f'Spieler ', False,2)
                        await self._game_manager.buzzer_manager.writetext(buzzer.mac, 4, f'{self._player_buzz.name}', False,2)
                        await self._game_manager.buzzer_manager.writetext(buzzer.mac, 5, f' hat gebuzzed!', False,2)
                        if buzzer.get_state() != BuzzerState.InGamePlayerEliminated:
                            buzzer.set_state(BuzzerState.InGamePlayerNotBuzzed)
                else:
                    if buzzer.get_state() == BuzzerState.InGamePlayerEliminated:
                        await self._game_manager.buzzer_manager.writetext(buzzer.mac, 4, f'Ausgeschieden ...', False)
                    else:
                        await self._game_manager.buzzer_manager.writetext(buzzer.mac, 4, f'???', False)
                        buzzer.set_state(BuzzerState.InGamePlayerMusicPlaying)

class InGameSongEndManager(AbstractGameStateManager):
    def __init__(self, game_manager: GameManager):
        super().__init__(game_manager, GameState.INGAME_SONG_END)
        self._name = "InGameSongEndManager"

    async def run_state_loop(self):
        # simply wait for 5 seconds, decide what to do then
        await asyncio.sleep(12)
        self._game_manager.current_round += 1
        self._game_manager.sp_player.pause()

        if all(player.points < self._game_manager.game_settings["targetPoints"] for player in self._game_manager.players): 
            #if self._game_manager.current_round < self._game_manager.game_settings['numRounds']:
            # switch into judge assignment
            self._game_manager.set_state(GameState.INGAME_JUDGE_ASSIGNMENT)
        else:
            # game over
            self._game_manager.set_state(GameState.INGAME_ROUND_END)

    async def on_state_enter(self):
        print(f'[{self._name}] on_state_enter')
        self.abort = False
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameJudgeMusicPlaying, BuzzerState.InGamePlayerMusicPlaying, BuzzerState.InGameJudgeBuzzedDecision, BuzzerState.InGamePlayerBuzzed, BuzzerState.InGamePlayerEliminated, BuzzerState.InGamePlayerNotBuzzed, BuzzerState.InGamePlayerWon]):
            buzzer.set_state(BuzzerState.InGameAfterSong)
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            player.judge = False
            player.eliminated = False 

    async def on_state_leave(self):
        print(f'[{self._name}] on_state_leave')
        pass

    async def handle_buzzer_message(self, buzzer: Buzzer, message: dict):
        print(f'[{self._name}] handle_buzzer_message')
        pass
    
    async def update_buzzers(self):
        print(f'[{self._name}] update_buzzers')
        pass

class InGameRoundEndManager(AbstractGameStateManager):
    def __init__(self, game_manager: GameManager):
        super().__init__(game_manager, GameState.INGAME_ROUND_END)
        self._name = "InGameRoundEndManager"

    async def run_state_loop(self):
        # simply wait for 15 seconds, then go back to player assignment
        await asyncio.sleep(15)
        self._game_manager.set_state(GameState.PLAYER_REGISTRATION_WAIT_EVERYONE_READY)

    async def on_state_enter(self):
        print(f'[{self._name}] on_state_enter')
        self.abort = False
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.InGameAfterSong]):
            buzzer.set_state(BuzzerState.PostGame)

    async def on_state_leave(self):
        print(f'[{self._name}] on_state_leave')
        self._game_manager.current_round = 0
        self._game_manager.judge_index = -1
        self._game_manager.sp_manager = None          # ← NEU: zwingt fresh init
        self._game_manager.game_settings["playlists"] = []
        for player in self._game_manager.players:
            player.points = 0
        pass

    async def handle_buzzer_message(self, buzzer: Buzzer, message: dict):
        print(f'[{self._name}] handle_buzzer_message')
        pass
    
    async def update_buzzers(self):
        print(f'[{self._name}] update_buzzers')
        for buzzer in self._game_manager.buzzer_manager.get_by_states([BuzzerState.PostGame]):
            player = self._game_manager.player_for_buzzer_id(buzzer.id)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 0, f'Spieler {player.name}', True)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 1, f' ', False)
            await self._game_manager.buzzer_manager.writetext(buzzer.mac, 4, f' RUNDE VORBEI!!!', False)


class GameManager:
    _game_state: GameState = GameState.UNDEFINED

    sp_player = SpotifyPlayer()
    sp_manager = None
    # --- Simple in-memory game state ---
    players: list[Player] = []
    game_settings: dict = {
        "targetPoints": 10, 
        "playlists": [], 
        "numPlayers": 2,
        "numRounds": 3,
        "startSecond": 40
    }

    available_playlists: list = []

    current_preview_playlist = None
    current_preview_playlist_index = -1

    current_round = 0
    judge_index = -1
    current_judge = None

    active_connections: list[GameWebsocketConnection] = []
    buzzer_manager: BuzzerManager

    # one gamestate manager per state.
    # key = state, val = manager
    game_state_managers: dict[GameState, AbstractGameStateManager] = {}



    def __init__(self, buzzer_manager: BuzzerManager):
        self.buzzer_manager = buzzer_manager
        self.available_playlists = self._load_playlists()
        self.evening_played_ids: set = set()  # wird nie zurückgesetzt, läuft den ganzen Abend
        self._setup_gamestate_managers()
        pass

    # ---------- Playlist-Pool helpers ----------

    def _load_playlists(self) -> list:
        try:
            if PLAYLISTS_FILE.exists():
                with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[PLAYLISTS] Could not load {PLAYLISTS_FILE}: {e}")
        return []

    def _save_playlists(self):
        try:
            PLAYLISTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.available_playlists, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[PLAYLISTS] Could not save {PLAYLISTS_FILE}: {e}")

    def _parse_spotify_uri(self, url_or_uri: str) -> str | None:
        """Converts a Spotify URL or URI to a spotify:playlist:<id> URI."""
        s = url_or_uri.strip()
        if s.startswith("spotify:playlist:"):
            return s
        # https://open.spotify.com/playlist/<id>?...
        if "open.spotify.com/playlist/" in s:
            playlist_id = s.split("open.spotify.com/playlist/")[1].split("?")[0].split("/")[0]
            return f"spotify:playlist:{playlist_id}"
        return None

    async def _add_to_pool_async(self, url_or_uri: str, custom_name: str = None):
        """Fetches playlist name from Spotify (unless custom_name given), adds to pool, saves to disk."""
        uri = self._parse_spotify_uri(url_or_uri)
        if uri is None:
            print(f"[PLAYLISTS] Cannot parse URI from: {url_or_uri}")
            await self.broadcast_state()
            return
        # Check for duplicates
        if any(p["uri"] == uri for p in self.available_playlists):
            print(f"[PLAYLISTS] Already in pool: {uri}")
            await self.broadcast_state()
            return
        if custom_name:
            name = custom_name
        else:
            try:
                from backend.credintals import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
                import spotipy
                from spotipy.oauth2 import SpotifyClientCredentials
                sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                    client_id=SPOTIFY_CLIENT_ID,
                    client_secret=SPOTIFY_CLIENT_SECRET
                ))
                playlist_id = uri.split("spotify:playlist:")[1]
                result = sp.playlist(playlist_id, fields="name")
                name = result["name"]
            except Exception as e:
                print(f"[PLAYLISTS] Could not fetch playlist name: {e}")
                name = uri.split(":")[-1]  # fallback: use raw ID as name
        entry = {"name": name, "uri": uri}
        self.available_playlists.append(entry)
        self._save_playlists()
        print(f"[PLAYLISTS] Added to pool: {entry}")
        await self.broadcast_state()

    def _setup_gamestate_managers(self):
        # instantiate gamestate managers
        self.game_state_managers[GameState.PLAYER_REGISTRATION_WAIT_EVERYONE_READY] = PlayerRegistrationWaitEveryoneReadyManager(self)
        self.game_state_managers[GameState.INGAME_JUDGE_ASSIGNMENT] = IngameJudgeAssignmentManager(self)
        self.game_state_managers[GameState.INGAME_MUSIC_PLAYING] = InGameMusicPlayingManager(self)
        self.game_state_managers[GameState.INGAME_SONG_END] = InGameSongEndManager(self)
        self.game_state_managers[GameState.INGAME_ROUND_END] = InGameRoundEndManager(self)

    def initialize_spotify_playlist_manager(self):
        uris = [p["uri"] for p in self.game_settings['playlists']]
        if self.sp_manager is None:
            self.sp_manager = SpotifyPlaylistManager(uris, evening_played_ids=self.evening_played_ids)
        else:
            self.sp_manager.playlists = uris
            self.sp_manager.played_ids.clear()
            self.sp_manager._queue = []  # Queue neu aufbauen mit neuen Playlists
    
    async def register_player(self, player_dict: dict) -> Player:
        if not 'id' in player_dict.keys() or not 'name' in player_dict.keys() or not 'avatar_url' in player_dict.keys() or not 'buzzer_id' in player_dict.keys() or not 'sound' in player_dict.keys() or not 'color' in player_dict.keys():
            raise ValueError("Player dict must contain id, name, avatar, buzzer_id, sound and color")
        
        if len([p for p in self.players if p.buzzer.id == player_dict['buzzer_id']]) > 0:
            raise ValueError(f'Buzzer with id={player_dict['buzzer_id']} already taken')
        
        target_buzzer = self.buzzer_manager.buzzer_for_id(player_dict['buzzer_id'])
        player = Player(player_dict['id'], player_dict['name'], player_dict['avatar_url'],  player_dict['color'], target_buzzer, player_dict['sound'])
        self.players.append(player)
        target_buzzer.set_state(BuzzerState.PreGameConnectedAssignedNotReady)
        print(f"[JOIN] Added player: {player.id} ({player.name})")
        await self.update_buzzers()
        await self.broadcast_state()
        return player
    
    async def update_buzzers(self):
        if self._game_state in self.game_state_managers:
            handler = self.game_state_managers[self._game_state]
            await handler.update_buzzers()
        await self.write_buzzer_colors()

    def get_local_ip(self) -> str:
        """Ermittelt die aktuelle IP-Adresse des PCs im Netzwerk"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Nutzt Google DNS, um das aktive Netzwerk-Interface zu finden
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    async def broadcast_state(self):

        local_ip = self.get_local_ip()
        join_url = f"http://{local_ip}:8000/join"
        
        buzzed = [b for b in self.buzzer_manager.active_buzzers if b.get_state() == BuzzerState.InGamePlayerBuzzed]
        winner = [b for b in self.buzzer_manager.active_buzzers if b.get_state() == BuzzerState.InGamePlayerWon]

        payload = {
            "players": [p.toDict() for p in self.players],
            "settings": self.game_settings,
            # Client will fallback to window.origin + '/join'
            "joinUrl": join_url,
            "currentPreviewPlaylist": self.current_preview_playlist,
            "state": self.get_state().name,
            "currentJudge": (self.current_judge.toDict()) if self.current_judge is not None else None,
            "buzzedPlayer": self.player_for_buzzer_id(buzzed[0].id).toDict() if len(buzzed) > 0 else None,
            "activeSong": self.sp_player.current_track if self.sp_player.current_track is not None else None,
            "roundWinner":  self.player_for_buzzer_id(winner[0].id).toDict() if len(winner) > 0 else None,
            "availablePlaylists": self.available_playlists,
        }
        message = {"type": "UPDATE", "payload": payload}
        print(f"[WS] Broadcasting state: players={len(self.players)} connections={len(self.active_connections)}")
        stale: list[WebSocket] = []
        for gc in self.active_connections:
            try:
                await gc.websocket.send_json(message)
            except Exception as e:
                stale.append(gc.websocket)
        # Cleanup stale connections
        for ws in stale:
            if ws in self.active_connections:
                self.active_connections.remove(ws)
    
    def game_websocket_on_message(self, game_websocket_connection: GameWebsocketConnection, data: any):
        print(f'Frontend Message received: {game_websocket_connection} -> {data}')
        try:
            type = data["type"]
            if type == "CHANGE_SETTING":
                key = data["key"]
                step = data["step"]
                if key == 'numPlayers':
                    if self.game_settings[key] + step < 2:
                        raise ValueError("Cannot go lower than 2 players.")
                if key == 'targetPoints':
                    if self.game_settings[key] + step < 1:
                        raise ValueError("Cannot go lower than 1 point.")
                if key == 'startSecond':
                    if self.game_settings[key] + step < 0:
                        raise ValueError("Cannot go lower than 0 seconds.")
                self.game_settings[key] += step
            if type == "CONFIRM_PLAYLIST":
                if self.current_preview_playlist is not None:
                    self.game_settings["playlists"].append(self.current_preview_playlist)
            if type == "REMOVE_PLAYLIST":
                uri = data["uri"]
                self.game_settings["playlists"] = [p for p in self.game_settings["playlists"] if p["uri"] != uri]
            if type == "PREVIEW_PLAYLIST":
                if len(self.available_playlists) == 0:
                    pass  # nothing to preview
                else:
                    step = data["step"]
                    self.current_preview_playlist_index = (self.current_preview_playlist_index + step) % len(self.available_playlists)
                    self.current_preview_playlist = self.available_playlists[self.current_preview_playlist_index]
                    sp_preview = SpotifyPlaylistManager([self.current_preview_playlist["uri"]])
                    track = sp_preview.getrandomsong()
                    sp_preview.played_ids.clear()
                    if self.sp_player.playing:
                        self.sp_player.pause()
                    self.sp_player.startsong(track, start_second=self.game_settings["startSecond"])
            if type == "KICK_PLAYER":
                player_id = data.get("playerId")
                player = next((p for p in self.players if p.id == player_id), None)
                if player is not None:
                    player.buzzer.set_state(BuzzerState.PreGameConnectedUnassigned)
                    self.players = [p for p in self.players if p.id != player_id]
                    print(f"[KICK] Removed player {player_id}")
            if type == "ADD_TO_POOL":
                url = data.get("url", "")
                custom_name = data.get("name") or None
                asyncio.create_task(self._add_to_pool_async(url, custom_name))
                return  # _add_to_pool_async broadcasts itself
            if type == "REMOVE_FROM_POOL":
                uri = data.get("uri", "")
                self.available_playlists = [p for p in self.available_playlists if p["uri"] != uri]
                # also remove from active game playlists if present
                self.game_settings["playlists"] = [p for p in self.game_settings["playlists"] if p["uri"] != uri]
                # reset preview index if now out of range
                if len(self.available_playlists) == 0:
                    self.current_preview_playlist_index = -1
                    self.current_preview_playlist = None
                else:
                    self.current_preview_playlist_index = min(self.current_preview_playlist_index, len(self.available_playlists) - 1)
                self._save_playlists()
        except:
            pass
        asyncio.create_task(self.broadcast_state())

    def register_connection(self, websocket: WebSocket) -> GameWebsocketConnection:
        ret = GameWebsocketConnection(websocket, self.unregister_connection)
        ret.register_on_message_cb(self.game_websocket_on_message)
        self.active_connections.append(ret)
        print(f'New websocket connection {ret}')
        asyncio.create_task(self.broadcast_state())
        return ret

    def unregister_connection(self, connection: GameWebsocketConnection):
        print(f'Websocket connection terminate {connection}')
        if connection in self.active_connections:
            self.active_connections.remove(connection)

    async def _buzzer_on_message_async(self, handler: AbstractGameStateManager, buzzer: Buzzer, message: dict):
        try:
            await handler.handle_buzzer_message(buzzer, message)
        except Exception as e:
            print(f'handler {handler._name} failed to handle buzzer message, reason={e}')

    async def register_buzzer(self, mac: str, websocket: WebSocket):
        # Der Manager übernimmt jetzt das Akzeptieren und Registrieren
        buzzer = await self.buzzer_manager.register_buzzer(mac, websocket)
        buzzer.register_on_message_callback(self.buzzer_on_message)
        # check whether this was the first buzzer, then we know UDP BROADCAST done
        if self.get_state() == GameState.UDP_BROADCAST_SETUP:
            self.set_state(GameState.PLAYER_REGISTRATION_WAIT_EVERYONE_READY)

        # now, we max encounter random disconnects/reconnects .. we should remember the buzzer state
        # check if there is already a player assigned to that
        try:
            player = self.player_for_buzzer_id(buzzer.id)
            # restore connection
            player.buzzer = buzzer
            # we must immediately reassign the buzzer state to eliminated
            if self._game_state == GameState.PLAYER_REGISTRATION_WAIT_EVERYONE_READY:
                player.ready = False
                buzzer.set_state(BuzzerState.PreGameConnectedAssignedNotReady)
            if self._game_state == GameState.INGAME_MUSIC_PLAYING:
                buzzer.set_state(BuzzerState.InGamePlayerEliminated)
            if self._game_state == GameState.INGAME_JUDGE_ASSIGNMENT:
                buzzer.set_state(BuzzerState.InGameRandomJudgeAssign)
            if self._game_state == GameState.INGAME_ROUND_END:
                buzzer.set_state(BuzzerState.PostGame)
            if self._game_state == GameState.INGAME_SONG_END:
                buzzer.set_state(BuzzerState.InGameAfterSong)
        except:
            pass
        await self.update_buzzers()
        await buzzer.poll_websocket_until_error()

    def buzzer_on_message(self, buzzer: Buzzer, message: dict):
        print(f'Buzzer {buzzer.mac} -> {message}')
        # dispatch messages depending on game's current state
        try:
            handler = self.game_state_managers[self._game_state]
            if handler is not None:
                asyncio.create_task(self._buzzer_on_message_async(handler, buzzer, message))
            # dispatch buzzer to frontends as well
            async def broadcast_to_fe():
                for conn in self.active_connections:
                    await conn.websocket.send_json({
                        'type': 'BUZZ_BUTTON',
                        'payload': {
                            'id': buzzer.id,
                            'val': message['val']
                        }
                    })
            asyncio.create_task(broadcast_to_fe())
        except Exception as e:
            print(f'cannot handle buzzer message in state {self._game_state}')
        finally:
            asyncio.create_task(self.update_buzzers())

    def set_state(self, state: GameState): 
        handlerBefore = self.game_state_managers[self._game_state] if self._game_state in self.game_state_managers else None
        handlerAfter = self.game_state_managers[state] if state in self.game_state_managers else None
        
        if handlerBefore is not None:
            async def on_state_leave():
                await handlerBefore.on_state_leave()
                await handlerBefore.update_buzzers()
            asyncio.create_task(on_state_leave())

        print(f'[AppState] TRANSITION {self._game_state} -> {state}')
        asyncio.create_task(self.broadcast_state())
        self._game_state = state

        if handlerAfter is not None:
            async def on_state_enter():
                try:
                    handlerAfter.abort = False
                    await handlerAfter.on_state_enter()
                except:
                    pass
                await handlerAfter.update_buzzers()
                await handlerAfter.run_state_loop()
            asyncio.create_task(on_state_enter())

    def get_state(self):
        return self._game_state 
    
    def player_for_buzzer_id(self, buzzer_id: int) -> Player:
        ret = [p for p in self.players if p.buzzer.id == buzzer_id]
        if len(ret) < 1:
            raise ValueError(f'no such player with buzzer id={buzzer_id}')
        return ret[0]
    
    def buzzer_is_judge(self, buzzer_id: int) -> bool:
        ret = [p for p in self.players if p.buzzer.id == buzzer_id]
        return False if len(ret) < 1 else ret[0].judge
    
    async def write_buzzer_colors(self):
        # player needed.
        for buzzer in self.buzzer_manager.active_buzzers:
            try:
                player = self.player_for_buzzer_id(buzzer.id)
                bstate = buzzer.get_state()
                if bstate in [BuzzerState.PreGameConnectedUnassigned, BuzzerState.InGameJudgeMusicPlaying, BuzzerState.InGameJudgeBuzzedDecision]:
                    await self.buzzer_manager.setled(buzzer.mac, '#0012ff')
                if bstate in [BuzzerState.PreGameConnectedAssignedNotReady, BuzzerState.InGameRandomJudgeAssign, BuzzerState.InGameAfterSong, BuzzerState.PostGame]:
                    await self.buzzer_manager.setled(buzzer.mac, player.color)
                if bstate in [BuzzerState.InGamePlayerMusicPlaying]:
                    await self.buzzer_manager.setled(buzzer.mac,  "#C300FF")
                if bstate in [BuzzerState.InGamePlayerBuzzed]:
                    await self.buzzer_manager.setled(buzzer.mac, player.color)
                if bstate in [BuzzerState.InGamePlayerNotBuzzed, BuzzerState.InGamePlayerEliminated]:
                    await self.buzzer_manager.setled(buzzer.mac, '#000000')
                if bstate in [BuzzerState.InGamePlayerWon]:
                    await self.buzzer_manager.setled(buzzer.mac, '#00FF00')
            except:
                await self.buzzer_manager.setled(buzzer.mac, '#FFFFFF') # noplayer -> white
