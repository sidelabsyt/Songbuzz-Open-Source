import HomeScreen from './components/HomeScreen.js';
import LobbyScreen from './components/LobbyScreen.js';
import GameScreen from './components/GameScreen.js';
import WinScreen from './components/WinScreen.js';
import JoinScreen from './components/JoinScreen.js';
import PlaybackScreen from './components/PlaybackScreen.js';
import JudgeScreen from './components/JudgeScreen.js';
import SongRevealScreen from './components/SongRevealScreen.js';

const LobbyActionType = {
    changeSetting: 'CHANGE_SETTING',
    setField: 'SET_FIELD',
    previewPlaylist: 'PREVIEW_PLAYLIST',
    confirmPlaylist: 'CONFIRM_PLAYLIST',
    removePlaylist: 'REMOVE_PLAYLIST',
    startGame: 'START_GAME',
    addToPool: 'ADD_TO_POOL',
    removeFromPool: 'REMOVE_FROM_POOL',
    kickPlayer: 'KICK_PLAYER'
}


const { createApp, ref, computed, onMounted, watch } = Vue;

const app = createApp({
    components: { HomeScreen, LobbyScreen, GameScreen, WinScreen, JoinScreen, PlaybackScreen, JudgeScreen, SongRevealScreen },
    setup() {
        const defaultJoinUrl = window.location.origin + '/join';
        const gameState = ref('HOME'); // HOME, LOBBY, GAME, WIN
        const gameData = ref({
            players: [],
            settings: { targetPoints: 10, playlistUrl: '' },
            currentJudge: null,
            activeSong: null,
            timer: 0,
            statusLabel: 'Warte auf Server...',
            joinUrl: defaultJoinUrl
        });

        const getRoute = () => {
            const hash = window.location.hash.replace(/^#\/?/, '').toLowerCase();
            const path = window.location.pathname.replace(/^\//, '').toLowerCase();
            if (hash === 'join' || path === 'join') return 'join';
            return '';
        };

        const route = ref(getRoute());

        // WebSocket Verbindung zum Python Backend
        const socket = ref(null);

        onMounted(() => {
            // Verbindung zum Python Backend aufbauen
            const proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const wsUrl = proto + window.location.host + '/ws';
            socket.value = new WebSocket(wsUrl);
            socket.value.onopen = () => {
                console.log('[WS] connected', wsUrl);
            };
            socket.value.onerror = (e) => {
                console.error('[WS] error', e);
            };

            socket.value.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                const payload = msg.payload || {};
                console.log('[WS] message type', msg.type, 'players', (payload.players || []).length);
                // Do not change the current screen state based on WS messages
                gameData.value = {
                    ...gameData.value,
                    ...payload,
                    joinUrl: payload.joinUrl || defaultJoinUrl
                };

                if ('state' in payload) {
                    switch (payload.state) {
                        case 'INGAME_MUSIC_PLAYING':
                            gameState.value = 'PLAY';
                            break;
                        case 'INGAME_JUDGE_ASSIGNMENT':
                            gameState.value = 'JUDGE';
                            break;
                        case 'INGAME_SONG_END':
                            gameState.value = 'SONG_END';
                            break;
                        case 'INGAME_ROUND_END':
                            gameState.value = 'WIN';
                            break;
                        default:
                            gameState.value = 'LOBBY';
                            break;
                    }
                }
            };

            window.addEventListener('hashchange', () => {
                route.value = getRoute();
            });
            window.addEventListener('popstate', () => {
                route.value = getRoute();
            });
        });

        const currentComponent = computed(() => {
            if (route.value === 'join') return JoinScreen;
            const mapping = {
                'HOME': HomeScreen,
                'LOBBY': LobbyScreen,
                'GAME': GameScreen,
                'WIN': WinScreen,
                'JUDGE': JudgeScreen,
                'PLAY': PlaybackScreen,
                'SONG_END': SongRevealScreen
            };
            return mapping[gameState.value] || HomeScreen;
        });

        // Log gameState after every change
        watch(gameData, () => {
            console.log('[GAMEDATA]', gameData);
        });

        const handleNav = (nextState) => {
            console.log('[NAV] switching state to', nextState);
            if (nextState === 'JOIN') {
                // Prefer clean path for sharing
                if (window.location.pathname !== '/join') {
                    window.history.pushState({}, '', '/join');
                }
                route.value = 'join';
                return;
            }
            if (route.value === 'join') {
                window.history.pushState({}, '', '/');
                route.value = '';
            }
            gameState.value = nextState;
        };

        const handleAction = (payload) => {
            // these are the lobby config actions
            const actionType = payload.type;
            switch (actionType) {
                case LobbyActionType.confirmPlaylist:
                case LobbyActionType.previewPlaylist:
                case LobbyActionType.removePlaylist:
                case LobbyActionType.setField:
                case LobbyActionType.startGame:
                case LobbyActionType.changeSetting:
                case LobbyActionType.addToPool:
                case LobbyActionType.removeFromPool:
                case LobbyActionType.kickPlayer:
                    socket.value.send(JSON.stringify({
                        ...payload
                    }))
                    break;
            }
        }

        return { gameState, gameData, currentComponent, handleNav, handleAction };
    },
    template: `
        <div class="app-container">
            <transition name="fade" mode="out-in">
                <component :is="currentComponent" :gameData="gameData" @nav="handleNav" @action="handleAction" />
            </transition>
        </div>
    `
});

app.mount('#app');
