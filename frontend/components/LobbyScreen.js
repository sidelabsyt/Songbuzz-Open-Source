export default {
    props: ['gameData'],
    emits: ['action'],
    data() {
        return {
            showPoolManager: false,
            newPlaylistUrl: '',
            newPlaylistName: '',
            poolPending: false
        };
    },
    watch: {
        'gameData.availablePlaylists': {
            deep: true,
            handler() {
                this.poolPending = false;
            }
        }
    },
    methods: {
        addToPool() {
            if (!this.newPlaylistUrl.trim()) return;
            this.poolPending = true;
            this.$emit('action', {
                type: 'ADD_TO_POOL',
                url: this.newPlaylistUrl.trim(),
                name: this.newPlaylistName.trim() || null
            });
            this.newPlaylistUrl = '';
            this.newPlaylistName = '';
        },
        removeFromPool(uri) {
            this.$emit('action', { type: 'REMOVE_FROM_POOL', uri });
        }
    },
    template: `
    <div class="screen active p-10">
        <div class="max-w-6xl mx-auto w-full flex flex-col h-full">

            <div class="flex justify-between items-start mb-12">
                <div>
                    <h2 class="text-4xl font-black text-white uppercase tracking-tight">Player Lobby</h2>
                    <p class="text-indigo-300">Get all the buzzers ready!</p>
                </div>
                <div class="glass p-4 rounded-2xl border border-white/10 flex items-center gap-4">
                    <div class="bg-white p-2 rounded-lg">
                        <img :src="'https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=' + gameData.joinUrl" class="w-20 h-20">
                    </div>
                    <div class="text-left text-xs">
                        <span class="block font-bold text-indigo-400 uppercase tracking-widest">Scan to Join</span>
                        <span class="text-white/60 font-mono">{{ gameData.joinUrl }}</span>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div v-for="p in gameData.players" :key="p.id"
                     class="group relative player-card glass rounded-3xl h-60 border border-white/10 p-6 flex flex-col items-center justify-between transition-all hover:border-indigo-500/50" :class="{'bg-green-900': p.ready}">
                    <!-- Kick Button -->
                    <button @click.stop="$emit('action', {type: 'KICK_PLAYER', playerId: p.id})"
                            class="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity bg-red-600/80 hover:bg-red-500 text-white text-[10px] font-black uppercase px-2 py-1 rounded-lg">
                        ✕ Kick
                    </button>
                    <div class="w-24 h-24 rounded-full overflow-hidden border-4 shadow-xl" :style="{ borderColor: p.color }">
                        <img v-if="p.avatar_url" :src="p.avatar_url" alt="Avatar" class="w-full h-full object-cover"/>
                        <div v-else class="w-full h-full flex items-center justify-center text-4xl font-black text-white" :style="{ background: p.color }">{{ p.name.charAt(0) }}</div>
                    </div>
                    <div class="text-center">
                        <span class="block text-xl font-black text-white uppercase tracking-tighter">{{ p.name }}</span>
                        <div class="flex items-center justify-center gap-1 mt-1">
                            <span class="w-2 h-2 rounded-full animate-pulse" :class="{'bg-green-500': p.ready,'bg-red-500': !p.ready }"></span>
                            <span class="text-[10px] text-indigo-300 uppercase font-black tracking-widest">{{p.ready ? 'Ready' : 'Not ready' }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="mt-auto bg-white/5 p-8 rounded-[2.5rem] border border-white/10 flex flex-col gap-6 shadow-2xl backdrop-blur-md">

                <div class="flex justify-between items-center border-b border-white/5 pb-3">
                    <span class="text-[10px] text-indigo-400 uppercase font-black tracking-[0.2em]">Game Configuration</span>
                    <div class="flex gap-4 items-center">
                         <span class="text-[9px] text-white/30 uppercase font-bold italic">◀ ▶ Change</span>
                         <span class="text-[9px] text-indigo-400 uppercase font-black italic">🔘 Buzzer = OK</span>
                    </div>
                </div>

                <div class="space-y-2">
                    <div
                         class="flex items-center justify-between transition-all duration-300 cursor-pointer"
                         @click="$emit('action', {type: 'SET_FIELD', field: 0})">
                        <span class="text-xs uppercase font-black w-24 text-left">Max Player</span>
                        <div class="flex items-center gap-8 flex-1 justify-center text-indigo-500">
                            <span class="text-3xl font-black select-none" @click.stop="$emit('action', {type: 'CHANGE_SETTING', key: 'numPlayers', step: -1})">◀</span>
                            <span class="text-5xl font-black italic text-white min-w-[100px] text-center">{{ gameData.settings.numPlayers }}</span>
                            <span class="text-3xl font-black select-none" @click.stop="$emit('action', {type: 'CHANGE_SETTING', key: 'numPlayers', step: 1})">▶</span>
                        </div>
                        <div class="w-24"></div>
                    </div>

                    <div
                         class="flex items-center justify-between transition-all duration-300 cursor-pointer"
                         @click="$emit('action', {type: 'SET_FIELD', field: 1})">
                        <span class="text-xs uppercase font-black w-24 text-left">Points To Win</span>
                        <div class="flex items-center gap-8 flex-1 justify-center text-indigo-500">
                            <span class="text-3xl font-black select-none" @click.stop="$emit('action', {type: 'CHANGE_SETTING', key: 'targetPoints', step: -1})">◀</span>
                            <div class="flex items-baseline min-w-[100px] justify-center text-white">
                                <span class="text-5xl font-black italic">{{ gameData.settings.targetPoints }}</span>
                                <span class="text-sm ml-1 opacity-50 font-bold">PKT</span>
                            </div>
                            <span class="text-3xl font-black select-none" @click.stop="$emit('action', {type: 'CHANGE_SETTING', key: 'targetPoints', step: 1})">▶</span>
                        </div>
                        <div class="w-24"></div>
                    </div>

                    <div
                         class="flex items-center justify-between transition-all duration-300 cursor-pointer"
                         @click="$emit('action', {type: 'SET_FIELD', field: 2})">
                        <span class="text-xs uppercase font-black w-24 text-left">Song Start</span>
                        <div class="flex items-center gap-8 flex-1 justify-center text-indigo-500">
                            <span class="text-3xl font-black select-none" @click.stop="$emit('action', {type: 'CHANGE_SETTING', key: 'startSecond', step: -5})">◀</span>
                            <div class="flex items-baseline min-w-[100px] justify-center text-white">
                                <span class="text-5xl font-black italic">{{ gameData.settings.startSecond }}</span>
                                <span class="text-sm ml-1 opacity-50 font-bold">SEK</span>
                            </div>
                            <span class="text-3xl font-black select-none" @click.stop="$emit('action', {type: 'CHANGE_SETTING', key: 'startSecond', step: 5})">▶</span>
                        </div>
                        <div class="w-24"></div>
                    </div>

                    <div
                         class="flex items-center justify-between transition-all duration-300 pt-2 cursor-pointer"
                         @click="$emit('action', {type: 'SET_FIELD', field: 3})">
                        <span class="text-xs uppercase font-black w-24 text-left">Playlist</span>
                        <div class="flex items-center gap-8 flex-1 justify-center bg-white/5 py-4 rounded-3xl border border-white/5 shadow-inner">
                            <span class="text-2xl font-black text-indigo-500 ml-4 animate-pulse select-none" @click.stop="$emit('action', {type: 'PREVIEW_PLAYLIST', step: -1})">◀</span>
                            <div class="flex-1 text-center px-4" @click.stop="$emit('action', {type: 'CONFIRM_PLAYLIST'})">
                                <span class="text-2xl font-black italic tracking-tight text-white uppercase block">💿 {{ gameData.currentPreviewPlaylist?.name || 'Select playlist...' }}</span>
                                <span class="text-[9px] text-indigo-400 font-bold uppercase tracking-widest">Press the buzzer to add</span>
                            </div>
                            <span class="text-2xl font-black text-indigo-500 mr-4 animate-pulse select-none" @click.stop="$emit('action', {type: 'PREVIEW_PLAYLIST', step: 1})">▶</span>
                        </div>
                        <div class="w-24"></div>
                    </div>
                </div>

                <!-- Pool Manager -->
                <div class="border border-white/10 rounded-2xl overflow-hidden">
                    <button @click="showPoolManager = !showPoolManager"
                            class="w-full flex items-center justify-between px-5 py-3 bg-white/5 hover:bg-white/10 transition-colors">
                        <div class="flex items-center gap-2">
                            <span class="text-[10px] text-indigo-400 uppercase font-black tracking-[0.2em]">🎵 Manage playlist pool</span>
                            <span class="bg-indigo-600/40 text-indigo-200 text-[9px] font-black px-2 py-0.5 rounded-full">{{ (gameData.availablePlaylists || []).length }}</span>
                        </div>
                        <span class="text-indigo-400 text-sm">{{ showPoolManager ? '▲' : '▼' }}</span>
                    </button>

                    <div v-if="showPoolManager" class="p-4 flex flex-col gap-3">
                        <!-- Add new playlist -->
                        <div class="flex flex-col gap-2">
                            <div class="flex gap-2">
                                <input v-model="newPlaylistUrl"
                                       @keyup.enter="addToPool"
                                       placeholder="Paste a Spotify URL or URI..."
                                       class="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 outline-none focus:border-indigo-500/50 transition-colors" />
                                <button @click="addToPool"
                                        :disabled="poolPending || !newPlaylistUrl.trim()"
                                        class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-black uppercase px-4 py-2 rounded-xl transition-colors whitespace-nowrap">
                                    {{ poolPending ? '...' : '+ Add' }}
                                </button>
                            </div>
                            <input v-model="newPlaylistName"
                                   @keyup.enter="addToPool"
                                   placeholder="Name (optional – otherwise the Spotify name will be used)"
                                   class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 outline-none focus:border-indigo-500/50 transition-colors" />
                        </div>

                        <!-- Pool list -->
                        <div class="max-h-48 overflow-y-auto flex flex-col gap-1 pr-1">
                            <div v-if="!gameData.availablePlaylists || gameData.availablePlaylists.length === 0"
                                 class="text-white/20 text-[11px] font-black uppercase italic tracking-widest py-3 text-center">
                                The pool is empty – add your first playlist
                            </div>
                            <div v-for="pl in gameData.availablePlaylists" :key="pl.uri"
                                 class="group flex items-center justify-between bg-white/5 hover:bg-white/10 rounded-xl px-4 py-2 transition-colors">
                                <div class="flex items-center gap-2 min-w-0">
                                    <span class="text-base flex-shrink-0">💿</span>
                                    <span class="text-sm font-bold text-white truncate">{{ pl.name }}</span>
                                </div>
                                <button @click="removeFromPool(pl.uri)"
                                        class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 text-xs font-black uppercase ml-3 flex-shrink-0 transition-opacity">
                                    ✕ Remove
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="mt-4 text-left animate-in fade-in duration-700">
                    <div class="flex items-center gap-2 mb-3">
                        <div class="h-[1px] flex-1 bg-white/10"></div>
                        <span class="text-[9px] text-slate-500 uppercase font-black tracking-widest px-2">Active Playlist Mix</span>
                        <div class="h-[1px] flex-1 bg-white/10"></div>
                    </div>

                    <div class="flex flex-wrap gap-3 justify-center min-h-[50px]">
                        <div v-for="(pl, idx) in gameData.settings.playlists" :key="idx"
                             class="animate-in zoom-in slide-in-from-bottom-2 duration-300">
                            <div @click.stop="$emit('action', {type: 'REMOVE_PLAYLIST', uri: pl.uri})" class="bg-indigo-600/20 border border-indigo-500/40 px-4 py-2 rounded-xl flex items-center gap-3 shadow-lg backdrop-blur-sm">
                                <span class="text-lg">💿</span>
                                <span class="text-sm font-black italic text-white uppercase tracking-tight">{{ pl.name }}</span>
                                <div class="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_8px_indigo]"></div>
                            </div>
                        </div>

                        <div v-if="!gameData.settings.playlists || gameData.settings.playlists.length === 0"
                             class="text-white/10 text-[11px] font-black uppercase italic tracking-[0.3em] py-2">
                            Please add at least one playlist
                        </div>
                    </div>
                </div>

                <button @click="$emit('action', {type: 'START_GAME'})"
                        :class="(gameData.players.length >= 1 && gameData.settings.playlists?.length > 0) ? 'bg-indigo-600 shadow-[0_0_50px_rgba(79,70,229,0.4)] hover:bg-indigo-500 scale-100' : 'bg-white/5 text-white/10 scale-95 opacity-50 cursor-not-allowed'"
                        class="w-full py-6 mt-2 rounded-[2rem] text-2xl font-black uppercase transition-all transform active:scale-90 border border-white/10 flex items-center justify-center gap-4">
                    <span>{{ gameData.players.length >= 1 ? (gameData.settings.playlists?.length > 0 ? 'START GAME' : 'SELECT PLAYLIST') : 'WAITING FOR PLAYERS' }}</span>
                    <div v-if="gameData.settings.playlists?.length > 0" class="bg-black/40 px-3 py-1 rounded-lg text-xs font-black italic">
                        {{ gameData.settings.playlists.length }} Mix
                    </div>
                </button>
            </div>
        </div>
    </div>
    `
};
