export default {
    props: ['gameData'],
    template: `
    <div class="screen active p-10 flex flex-col items-center justify-center overflow-hidden bg-slate-950">
        
        <div class="absolute inset-0 z-0 opacity-30 blur-[100px] scale-150">
            <img :src="gameData.activeSong?.artwork_url" class="w-full h-full object-cover">
        </div>

        <div class="z-10 w-full max-w-6xl">
            
            <div class="flex flex-col md:flex-row items-center gap-12 mb-16 animate-in slide-in-from-top-12 duration-700">
                <div class="relative">
                    <div class="absolute -inset-4 bg-white/10 rounded-[3rem] blur-xl"></div>
                    <img :src="gameData.activeSong?.artwork_url" 
                         class="relative w-72 h-72 rounded-[2.5rem] shadow-2xl border-4 border-white/20 object-cover rotate-3 hover:rotate-0 transition-transform duration-500" />
                </div>

                <div class="text-left flex-1">
                    <span class="px-4 py-1 bg-indigo-500 text-white text-xs font-black uppercase tracking-widest rounded-full mb-4 inline-block">
                        Die Auflösung
                    </span>
                    <h1 class="text-6xl font-black text-white leading-tight mb-2 tracking-tighter">
                        {{ gameData.activeSong?.title }}
                    </h1>
                    <h2 class="text-3xl font-bold text-indigo-400 italic">
                        {{ gameData.activeSong?.artist }}
                    </h2>
                </div>

                <div v-if="gameData.roundWinner" class="bg-green-500 p-8 rounded-[3rem] shadow-[0_0_50px_rgba(34,197,94,0.4)] rotate-12 flex flex-col items-center">
                    <span class="text-[10px] font-black uppercase text-green-900 tracking-widest mb-1">Punkt für</span>
                    <img :src="gameData.roundWinner.avatar_url" class="w-16 h-16 rounded-full border-2 border-white mb-2" />
                    <span class="text-xl font-black text-white uppercase">{{ gameData.roundWinner.name }}</span>
                </div>
                <div v-else class="bg-red-500/20 border-2 border-red-500/50 p-8 rounded-[3rem] flex flex-col items-center opacity-80">
                    <span class="text-4xl mb-2">🤷‍♂️</span>
                    <span class="text-lg font-black text-red-500 uppercase">Niemand wusste es</span>
                </div>
            </div>

            <div class="glass rounded-[3rem] border border-white/10 p-8 shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-bottom-12 delay-300 duration-1000">
                <div class="flex items-center justify-between mb-8 px-4">
                    <h3 class="text-2xl font-black text-white uppercase italic tracking-tighter">Aktueller Punktestand</h3>
                    <div class="text-indigo-400 text-xs font-bold uppercase tracking-widest bg-white/5 px-4 py-2 rounded-full border border-white/5">
                        Ziel: {{ gameData.settings?.targetPoints }} PKT
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(p, idx) in [...gameData.players].sort((a,b) => b.points - a.points)" 
                         :key="p.id"
                         class="flex items-center justify-between p-4 rounded-2xl border transition-all duration-300"
                         :class="p.id === gameData.roundWinner?.id ? 'bg-indigo-500/20 border-indigo-500' : 'bg-white/5 border-white/5'">
                        
                        <div class="flex items-center gap-4">
                            <span class="text-xl font-black italic text-white/20 w-6">#{{ idx + 1 }}</span>
                            <div class="relative">
                                <img :src="p.avatar_url" class="w-12 h-12 rounded-full border-2 shadow-lg" :style="{borderColor: p.color}">
                                <div v-if="idx === 0" class="absolute -top-2 -left-2 text-xl">👑</div>
                            </div>
                            <div>
                                <div class="text-lg font-black text-white uppercase tracking-tight">{{ p.name }}</div>
                                <div class="h-1.5 w-32 bg-white/10 rounded-full mt-1 overflow-hidden">
                                    <div class="h-full bg-indigo-500 transition-all duration-1000" 
                                         :style="{ width: Math.min((p.points / gameData.settings.targetPoints) * 100, 100) + '%' }"></div>
                                </div>
                            </div>
                        </div>

                        <div class="text-right px-4">
                            <span class="text-3xl font-black italic text-white">{{ p.points }}</span>
                            <span class="text-[10px] block font-bold text-indigo-400 uppercase tracking-widest">Punkte</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="absolute bottom-6 animate-bounce opacity-50 text-white/50 text-[10px] uppercase font-black tracking-[0.3em]">
            Warte auf Spielleiter...
        </div>
    </div>
    `
};