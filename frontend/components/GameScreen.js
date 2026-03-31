export default {
    props: ['gameData'],
    template: `
    <div class="screen active p-0 bg-slate-950">
        <div class="flex justify-around bg-slate-900/50 border-b border-white/10 py-4 px-8">
            <div v-for="p in gameData.players" :key="p.id" 
                 class="flex flex-col items-center transition-all"
                 :class="{ 'opacity-20': p.locked, 'scale-110': p.id === gameData.currentJudge?.id }">
                <div class="w-12 h-12 rounded-full mb-1 flex items-center justify-center font-bold text-white border-2"
                     :style="{ background: p.color, borderColor: p.id === gameData.currentJudge?.id ? 'white' : 'transparent' }">
                    {{ p.name.charAt(0) }}
                </div>
                <div class="text-xl font-black text-white">{{ p.points }}</div>
            </div>
        </div>

        <div class="flex-grow flex flex-col items-center justify-center p-12 relative overflow-hidden">
            <div id="visualizer" class="absolute inset-0 flex items-center justify-center opacity-10 pointer-events-none">
                <div class="w-96 h-96 border-8 border-indigo-500 rounded-full animate-ping"></div>
            </div>

            <div class="relative z-10 text-center space-y-8">
                <div class="text-indigo-400 font-black uppercase tracking-[0.5em] text-xl">{{ gameData.statusLabel }}</div>
                <h2 class="text-8xl md:text-[8rem] font-black leading-none text-white uppercase tracking-tighter"
                    :style="{ color: gameData.displayColor || 'white' }">
                    {{ gameData.mainDisplayText }}
                </h2>
                <div class="text-2xl text-slate-400 italic">{{ gameData.subDisplayText }}</div>
            </div>
        </div>

        <div class="h-32 bg-slate-900 flex items-center px-12 justify-between">
            <div class="flex items-center gap-6">
                <div class="text-5xl font-black text-white font-mono tracking-widest">{{ gameData.timer }}s</div>
                <span class="text-xs text-slate-500 uppercase">Verbleibende Zeit</span>
            </div>
            <div class="flex gap-4" v-if="gameData.showJudgeControls">
                 <button class="bg-red-900/40 hover:bg-red-600 text-red-100 border border-red-500 px-8 py-3 rounded-xl font-black uppercase">Falsch</button>
                 <button class="bg-green-900/40 hover:bg-green-600 text-green-100 border border-green-500 px-8 py-3 rounded-xl font-black uppercase">Richtig</button>
            </div>
        </div>
    </div>
    `
};