export default {
    props: ['gameData'],
    computed: {
        // Sortiert die Spieler nach Punkten absteigend
        sortedPlayers() {
            return [...this.gameData.players].sort((a, b) => b.points - a.points);
        },
        // Die Top 3 für das Podium
        podium() {
            const players = this.sortedPlayers;
            // Reihenfolge fürs Podium: [2. Platz, 1. Platz, 3. Platz]
            return [players[1], players[0], players[2]].filter(p => p !== undefined);
        },
        // Alle anderen Spieler ab Platz 4
        otherPlayers() {
            return this.sortedPlayers.slice(3);
        }
    },
    template: `
    <div class="screen active p-10 flex flex-col items-center justify-center overflow-hidden bg-slate-950 min-h-screen text-white">
        
        <div class="absolute inset-0 z-0">
            <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-600/20 rounded-full blur-[120px] animate-pulse"></div>
        </div>

        <div class="z-10 w-full max-w-5xl flex flex-col items-center">
            
            <div class="text-center mb-12 animate-in fade-in zoom-in duration-700">
                <h1 class="text-7xl font-black italic tracking-tighter uppercase mb-2">
                    Spiel vorbei!
                </h1>
                <p class="text-indigo-400 font-bold uppercase tracking-[0.4em]">Das finale Ranking</p>
            </div>

            <div class="flex items-end justify-center gap-4 mb-16 h-80 w-full">
                
                <div v-for="(p, idx) in podium" :key="'podium-'+p.id" 
                     class="flex flex-col items-center transition-all duration-1000 animate-in slide-in-from-bottom-20"
                     :class="[
                        p.id === sortedPlayers[0].id ? 'w-64 order-2' : 'w-48 order-1',
                        p.id === sortedPlayers[2]?.id ? 'order-3' : ''
                     ]">
                    
                    <div class="relative mb-4">
                        <div v-if="p.id === sortedPlayers[0].id" class="absolute -top-12 left-1/2 -translate-x-1/2 text-6xl animate-bounce">👑</div>
                        <img :src="p.avatar_url" 
                             class="rounded-full border-4 shadow-2xl"
                             :class="p.id === sortedPlayers[0].id ? 'w-40 h-40 border-yellow-400' : 'w-28 h-28 border-slate-400'"
                             :style="{ borderColor: p.id === sortedPlayers[0].id ? '#fbbf24' : (p.id === sortedPlayers[1].id ? '#94a3b8' : '#92400e') }">
                        <div class="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-white text-slate-900 px-4 py-1 rounded-full font-black text-sm shadow-xl">
                            {{ p.points }} PKT
                        </div>
                    </div>

                    <div class="text-center mb-2">
                        <div class="font-black uppercase tracking-tight truncate w-full" :class="p.id === sortedPlayers[0].id ? 'text-2xl' : 'text-lg'">
                            {{ p.name }}
                        </div>
                    </div>
                    
                    <div class="w-full bg-gradient-to-b from-white/10 to-transparent border-t-2 border-white/20 rounded-t-3xl flex items-start justify-center pt-4"
                         :style="{ height: p.id === sortedPlayers[0].id ? '100%' : (p.id === sortedPlayers[1].id ? '70%' : '50%') }">
                        <span class="text-4xl font-black italic opacity-30">
                            {{ p.id === sortedPlayers[0].id ? '1' : (p.id === sortedPlayers[1].id ? '2' : '3') }}
                        </span>
                    </div>
                </div>
            </div>

            <div v-if="otherPlayers.length > 0" 
                 class="w-full max-w-2xl glass rounded-[2.5rem] border border-white/10 p-6 animate-in fade-in slide-in-from-bottom-8 delay-500 duration-700">
                <div class="space-y-3">
                    <div v-for="(p, idx) in otherPlayers" :key="p.id" 
                         class="flex items-center justify-between p-4 bg-white/5 rounded-2xl hover:bg-white/10 transition-colors">
                        <div class="flex items-center gap-6">
                            <span class="text-xl font-black italic text-white/30 w-8">#{{ idx + 4 }}</span>
                            <img :src="p.avatar_url" class="w-10 h-10 rounded-full">
                            <span class="text-lg font-bold uppercase tracking-tight text-white/80">{{ p.name }}</span>
                        </div>
                        <div class="text-xl font-black text-indigo-400 italic">{{ p.points }} PKT</div>
                    </div>
                </div>
            </div>

            <button @click="$emit('restart')" 
                    class="mt-12 px-10 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-black uppercase tracking-[0.2em] rounded-full transition-all hover:scale-105 active:scale-95 shadow-[0_0_30px_rgba(79,70,229,0.4)]">
                Neue Runde starten
            </button>
        </div>
    </div>
    `
};