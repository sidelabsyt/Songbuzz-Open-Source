export default {
    props: ['gameData'],
    template: `
    <div class="screen active p-10 flex flex-col items-center justify-center overflow-hidden bg-slate-950">
        
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgba(99,102,241,0.2),transparent_60%)] z-0"></div>

        <div class="z-10 flex flex-col items-center max-w-4xl text-center">
            
            <div class="mb-6 animate-in slide-in-from-top-8 duration-700">
                <span class="px-6 py-2 bg-indigo-500/10 border border-indigo-500/30 rounded-full text-indigo-400 text-sm font-black uppercase tracking-[0.4em]">
                    Nächste Runde
                </span>
            </div>

            <h2 class="text-2xl font-light text-white/60 uppercase tracking-widest mb-12 animate-pulse">
                Der neue Judge ist...
            </h2>

            <div class="relative group mb-12">
                <div class="absolute inset-0 -m-8 rounded-full border border-indigo-500/20 animate-ping duration-[3000ms]"></div>
                <div class="absolute inset-0 -m-4 rounded-full border border-indigo-500/40 animate-pulse duration-[2000ms]"></div>
                
                <div class="relative glass rounded-[4rem] p-4 border-2 border-white/20 shadow-[0_0_80px_rgba(99,102,241,0.3)] transform transition-transform group-hover:scale-105 duration-500">
                    <div class="w-64 h-64 rounded-[3.5rem] overflow-hidden border-4 border-white/10 shadow-2xl bg-slate-800">
                        <img v-if="gameData.currentJudge?.avatar_url" 
                             :src="gameData.currentJudge?.avatar_url" 
                             class="w-full h-full object-cover shadow-inner" />
                        <div v-else class="w-full h-full flex items-center justify-center text-8xl font-black text-white bg-indigo-600">
                            {{ gameData.currentJudge?.name?.charAt(0) }}
                        </div>
                    </div>
                </div>

                <div class="absolute -top-6 -right-6 w-20 h-20 bg-yellow-500 rounded-2xl flex items-center justify-center shadow-2xl rotate-12 border-4 border-slate-950">
                    <span class="text-4xl">👑</span>
                </div>
            </div>

            <h1 class="text-8xl font-black text-white uppercase tracking-tighter italic mb-8 drop-shadow-2xl">
                {{ gameData.currentJudge?.name }}
            </h1>

            <div class="glass px-10 py-6 rounded-[2.5rem] border border-white/10 flex flex-col items-center gap-4 animate-in fade-in slide-in-from-bottom-8 delay-500 duration-1000">
                <div class="flex items-center gap-6">
                    <div class="w-12 h-12 bg-red-600 rounded-full shadow-[0_0_20px_red] animate-bounce"></div>
                    <p class="text-xl font-bold text-indigo-100 uppercase tracking-wide">
                        Drücke den <span class="text-white underline decoration-red-500 decoration-4 underline-offset-4">großen Buzzer</span>
                    </p>
                </div>
                <span class="text-[10px] text-white/40 font-black uppercase tracking-[0.2em]">Um die Musik zu starten</span>
            </div>

        </div>

        <div class="absolute bottom-10 w-full px-20 flex justify-between items-center opacity-30 italic font-medium text-white">
            <span>Runde {{ gameData.roundNumber || 1 }}</span>
            <span class="text-sm">Bereite dich vor...</span>
            <span>Ziel: {{ gameData.settings?.targetPoints }} PKT</span>
        </div>
    </div>
    `
};