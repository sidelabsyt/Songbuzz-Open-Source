export default {
    props: ['gameData'],
    emits: ['nav'],
    template: `
    <div class="items-center justify-center p-6 text-center flex flex-col min-h-screen">
        <div class="mb-12">
            <h1 class="text-8xl font-black italic tracking-tighter text-white mb-2 neon-text-indigo">SONGBUZZ</h1>
            <p class="text-indigo-300 text-xl tracking-widest uppercase">The ultimate music hardware quiz</p>
        </div>
        <div class="space-y-4 w-full max-w-md">
            <button @click="$emit('nav', 'LOBBY')" class="btn-primary w-full py-5 rounded-2xl text-2xl font-bold uppercase tracking-widest">New Game</button>
        </div>
        <div class="mt-24 text-slate-500 text-sm flex items-center gap-4">
            <span>SERVER: ONLINE</span>
            <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
        </div>
    </div>
    `
};