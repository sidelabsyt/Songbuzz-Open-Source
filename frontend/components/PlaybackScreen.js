export default {
    props: ['gameData'],
    data() {
        return {
            elapsed: 0,
            timerInterval: null
        };
    },
    watch: {
        'gameData.buzzedPlayer'(newVal) {
            if (newVal) {
                this.elapsed = 0;
                if (this.timerInterval) clearInterval(this.timerInterval);
                this.timerInterval = setInterval(() => {
                    this.elapsed += 0.1;
                }, 100);
            } else {
                if (this.timerInterval) {
                    clearInterval(this.timerInterval);
                    this.timerInterval = null;
                }
                this.elapsed = 0;
            }
        }
    },
    computed: {
        barWidth() {
            return Math.min((this.elapsed / 10) * 100, 100);
        },
        elapsedDisplay() {
            return this.elapsed.toFixed(1);
        }
    },
    unmounted() {
        if (this.timerInterval) clearInterval(this.timerInterval);
    },
    template: `
    <div class="screen active overflow-hidden flex flex-col" style="height: 100vh;">
        <div class="absolute inset-0 bg-gradient-to-br from-indigo-900/20 via-black to-purple-900/20 z-0"></div>

        <!-- Wenn niemand gebuzzt hat: Visualizer oben, Spielerkacheln unten -->
        <div v-if="!gameData.buzzedPlayer" class="relative z-10 flex flex-col h-full px-10 pt-8 pb-6 gap-8">

            <!-- Visualizer + Titel -->
            <div class="flex flex-col items-center">
                <div class="flex items-end gap-2 h-24 mb-4">
                    <div v-for="i in 24" :key="i"
                         class="w-3 bg-gradient-to-t from-indigo-600 to-purple-400 rounded-full"
                         :style="{
                             height: (20 + Math.random() * 80) + '%',
                             opacity: 0.4 + (Math.random() * 0.6),
                             animation: 'pulse 1.5s infinite ' + (i * 0.1) + 's'
                         }">
                    </div>
                </div>
                <h1 class="text-5xl font-black text-white uppercase tracking-tighter animate-pulse">Hören & Buzzern</h1>
                <span class="mt-2 px-4 py-1 bg-white/5 border border-white/10 rounded-full text-indigo-300 font-black tracking-widest text-xs uppercase">
                    Musik läuft...
                </span>
            </div>

            <!-- Spieler-Kacheln -->
            <div class="flex-1 flex items-center justify-center">
                <div class="grid gap-6 w-full"
                     :style="{ gridTemplateColumns: 'repeat(' + gameData.players.length + ', minmax(0, 1fr))' }">
                    <div v-for="p in gameData.players" :key="p.id"
                         class="relative flex flex-col items-center gap-4 py-8 px-4 rounded-[2rem] border transition-all duration-500"
                         :class="{
                             'opacity-30 grayscale': p.eliminated,
                             'scale-105': p.judge
                         }"
                         :style="{
                             background: p.judge ? p.color + '18' : 'rgba(255,255,255,0.04)',
                             borderColor: p.judge ? p.color + '80' : 'rgba(255,255,255,0.08)',
                             boxShadow: p.judge ? '0 0 40px ' + p.color + '33' : 'none'
                         }">

                        <!-- Judge Crown -->
                        <div v-if="p.judge" class="absolute -top-6 left-1/2 -translate-x-1/2 text-5xl drop-shadow-lg">👑</div>

                        <!-- Eliminated overlay -->
                        <div v-if="p.eliminated" class="absolute inset-0 flex items-center justify-center z-10 rounded-[2rem] bg-black/40">
                            <span class="text-6xl">❌</span>
                        </div>

                        <!-- Avatar -->
                        <div class="rounded-full overflow-hidden shadow-2xl"
                             style="width: clamp(80px, 12vw, 160px); height: clamp(80px, 12vw, 160px);"
                             :style="{ border: '5px solid ' + p.color, boxShadow: '0 0 30px ' + p.color + '55' }">
                            <img :src="p.avatar_url" class="w-full h-full object-cover">
                        </div>

                        <!-- Name -->
                        <span class="text-xl font-black text-white uppercase tracking-wide text-center leading-tight">{{ p.name }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Wenn jemand gebuzzt hat: Buzzed-Karte oben, Spielerkacheln unten -->
        <div v-else class="relative z-10 flex flex-col h-full px-10 pt-8 pb-6 gap-6">

            <!-- Buzzed Player Card -->
            <div class="flex justify-center">
                <div class="relative animate-in zoom-in duration-300">
                    <div class="absolute -inset-6 rounded-full blur-3xl animate-pulse" :style="{ background: gameData.buzzedPlayer.color + '40' }"></div>
                    <div class="relative glass rounded-[3rem] px-16 py-8 border-2 border-white/20 flex flex-col items-center shadow-2xl">
                        <div class="w-36 h-36 rounded-full overflow-hidden border-8 mb-4 shadow-2xl"
                             :style="{ borderColor: gameData.buzzedPlayer.color || '#6366F1' }">
                            <img :src="gameData.buzzedPlayer.avatar_url" class="w-full h-full object-cover">
                        </div>
                        <h2 class="text-5xl font-black text-white uppercase tracking-tighter mb-2">
                            {{ gameData.buzzedPlayer.name }}
                        </h2>
                        <div class="bg-white text-black px-8 py-2 rounded-2xl font-black text-2xl italic transform -rotate-2">
                            ANTWORTET...
                        </div>
                    </div>
                    <!-- Timer Badge -->
                    <div class="absolute -top-4 -right-4 w-20 h-20 bg-red-600 rounded-full flex items-center justify-center border-4 border-white shadow-2xl transform rotate-12">
                        <span class="text-2xl font-black text-white font-mono">{{ elapsedDisplay }}s</span>
                    </div>
                </div>
            </div>

            <!-- Spieler-Kacheln (etwas kleiner wenn jemand buzzed) -->
            <div class="flex-1 flex items-center justify-center">
                <div class="grid gap-4 w-full"
                     :style="{ gridTemplateColumns: 'repeat(' + gameData.players.length + ', minmax(0, 1fr))' }">
                    <div v-for="p in gameData.players" :key="p.id"
                         class="relative flex flex-col items-center gap-3 py-5 px-3 rounded-[1.5rem] border transition-all duration-500"
                         :class="{
                             'opacity-30 grayscale': p.eliminated,
                             'scale-105 ring-2 ring-white/20': p.judge
                         }"
                         :style="{
                             background: p.judge ? p.color + '18' : 'rgba(255,255,255,0.04)',
                             borderColor: p.judge ? p.color + '80' : 'rgba(255,255,255,0.08)'
                         }">

                        <div v-if="p.judge" class="absolute -top-5 left-1/2 -translate-x-1/2 text-3xl">👑</div>

                        <div v-if="p.eliminated" class="absolute inset-0 flex items-center justify-center z-10 rounded-[1.5rem] bg-black/40">
                            <span class="text-4xl">❌</span>
                        </div>

                        <div class="w-16 h-16 rounded-full overflow-hidden shadow-xl"
                             :style="{ border: '3px solid ' + p.color, boxShadow: '0 0 15px ' + p.color + '44' }">
                            <img :src="p.avatar_url" class="w-full h-full object-cover">
                        </div>

                        <span class="text-sm font-black text-white uppercase tracking-wide text-center">{{ p.name }}</span>

                        <div class="flex items-baseline gap-1">
                            <span class="text-2xl font-black" :style="{ color: p.color }">{{ p.points }}</span>
                            <span class="text-xs text-white/40 font-bold uppercase">Pkt</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Roter Timer-Balken -->
        <div v-if="gameData.buzzedPlayer" class="fixed bottom-0 left-0 right-0 h-2 z-50">
            <div class="h-full bg-red-500 transition-all duration-100 ease-linear"
                 :style="{ width: barWidth + '%' }">
            </div>
        </div>

    </div>
    `
};
