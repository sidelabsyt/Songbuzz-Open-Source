export default {
    emits: ['nav'],
    data() {
        return {
            name: '',
            file: null,
            previewUrl: '',
            selectedBuzzer: null,
            selectedColor: '#4f46e5',
            selectedSound: '',
            
            // Diese Listen werden nun dynamisch gefüllt
            availableBuzzer: [1, 2, 3, 4, 5, 6, 7, 8], 
            availableSounds: [], // Startet leer
            colors: ['#ff0000ff', '#ffa200ff', '#00ffaaff', '#0062ffff', '#4c00ffff', '#ff0080ff', '#00d9ffff', '#99ff00ff', '#ff002bff', '#ffffff'],

            error: '',
            success: '',
            submitting: false,
            submitted: false,
            audioPreview: null
        };
    },
    async mounted() {
        try {
            const res = await fetch('/api/sounds');
            if (res.ok) {
                this.availableSounds = await res.json();
                console.log("Sounds geladen:", this.availableSounds);
            } else {
                console.error("Server antwortete mit Fehler:", res.status);
            }
        } catch (err) {
            console.error("Netzwerkfehler beim Laden der Sounds:", err);
        }
    },
    methods: {
        onFileChange(event) {
            const selected = event.target.files && event.target.files[0];
            if (!selected) return;
            this.file = selected;
            this.previewUrl = URL.createObjectURL(selected);
        },

        previewSound(sound) {
            if (this.audioPreview) {
                this.audioPreview.pause();
            }
            this.selectedSound = sound;
            // Dieser Pfad ist der "virtuelle" Pfad aus dem app.mount im Backend
            this.audioPreview = new Audio(`/winsounds/${sound}`);
            this.audioPreview.play();
        },

        async submit() {
            // Validierung: Prüfen, ob alles ausgefüllt ist
            if (!this.name || !this.file || !this.selectedBuzzer) {
                alert("Bitte Name, Foto und Buzzer wählen!");
                return;
            }

            this.submitting = true;
            this.error = '';

            try {
                // Wir nutzen FormData, um das Bild UND die Texte zu senden
                const formData = new FormData();
                formData.append('name', this.name);
                formData.append('avatar', this.file);
                formData.append('buzzer_id', this.selectedBuzzer);
                formData.append('color', this.selectedColor);
                formData.append('sound', this.selectedSound);

                const res = await fetch('/api/join', {
                    method: 'POST',
                    body: formData
                    // Wichtig: Keinen Content-Type Header setzen, 
                    // das macht der Browser bei FormData automatisch inkl. Boundary!
                });

                if (res.ok) {
                    const data = await res.json();
                    console.log("Erfolgreich beigetreten:", data);
                    this.submitted = true;
                    this.success = 'Erfolgreich beigetreten!';
                } else {
                    const errData = await res.json();
                    this.error = errData.detail || 'Fehler beim Beitreten';
                    alert(this.error);
                }
            } catch (err) {
                console.error("Netzwerkfehler:", err);
                this.error = 'Verbindung zum Server fehlgeschlagen.';
            } finally {
                this.submitting = false;
            }
        }
    },
    template: `
    <div class="items-center justify-center p-6 text-center flex flex-col min-h-screen bg-slate-950 text-white">
        <div class="mb-6">
            <h1 class="text-4xl font-black italic tracking-tighter mb-1">SONGBUZZ</h1>
            <p class="text-indigo-400 text-xs tracking-widest uppercase">Player Setup</p>
        </div>

        <div v-if="!submitted" class="glass p-5 rounded-2xl w-full max-w-md space-y-6 overflow-y-auto max-h-[90vh]">
            <div class="space-y-3">
                <input v-model="name" class="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10" placeholder="Dein Name" />
                <div class="flex items-center space-x-4 bg-white/5 p-3 rounded-xl border border-white/10">
                    <input type="file" accept="image/*" capture="user" @change="onFileChange" class="hidden" ref="fileInput" />
                    <button @click="$refs.fileInput.click()" class="bg-indigo-600 px-4 py-2 rounded-lg text-sm font-bold">Foto aufnehmen</button>
                    <img v-if="previewUrl" :src="previewUrl" class="w-12 h-12 rounded-full object-cover border-2 border-indigo-500" />
                </div>
            </div>

            <div class="text-left">
                <label class="text-[10px] text-slate-400 uppercase mb-2 block">Buzzer Nummer wählen (siehe Display)</label>
                <div class="flex flex-wrap gap-2">
                    <button v-for="num in availableBuzzer" :key="num" 
                        @click="selectedBuzzer = num"
                        :class="selectedBuzzer === num ? 'bg-indigo-500 border-white' : 'bg-white/5 border-white/10'"
                        class="w-10 h-10 rounded-xl border font-bold transition-all">
                        {{ num }}
                    </button>
                </div>
            </div>

            <div class="text-left">
                <label class="text-[10px] text-slate-400 uppercase mb-2 block">Deine Farbe</label>
                <div class="flex flex-wrap gap-2">
                    <div v-for="c in colors" :key="c" @click="selectedColor = c"
                        :style="{ backgroundColor: c }"
                        :class="selectedColor === c ? 'ring-2 ring-white scale-110' : 'opacity-70'"
                        class="w-7 h-7 rounded-full cursor-pointer transition-all">
                    </div>
                </div>
            </div>

            <div class="text-left">
                <label class="text-[10px] text-slate-400 uppercase mb-2 block">Dein Buzzer-Sound (Klicken zum Testen)</label>
                <div class="grid grid-cols-1 gap-2 max-h-40 overflow-y-auto pr-2 custom-scrollbar">
                    <button v-for="s in availableSounds" :key="s" 
                        @click="previewSound(s)"
                        :class="selectedSound === s ? 'bg-indigo-600/40 border-indigo-400' : 'bg-white/5 border-white/10'"
                        class="px-3 py-2 rounded-lg border text-[11px] truncate text-left flex items-center transition-colors">
                        <span class="mr-2">{{ selectedSound === s ? '🔊' : '🎵' }}</span> 
                        {{ s.replace('.mp3', '').replace(/-/g, ' ') }}
                    </button>
                </div>
            </div>

            <button @click="submit" :disabled="submitting"
                class="w-full py-4 rounded-2xl bg-indigo-600 font-black uppercase tracking-widest shadow-lg shadow-indigo-500/30">
                JETZT BEITRETEN
            </button>
        </div>

        <div v-else class="glass p-8 rounded-3xl w-full max-w-md animate-bounce-in">
            <h2 class="text-2xl font-bold mb-2">Bereit!</h2>
            <p class="text-slate-300 mb-6">{{ name }}, du hast Buzzer {{ selectedBuzzer }}</p>
            <div class="w-24 h-24 mx-auto rounded-full border-4" :style="{ borderColor: selectedColor }">
                <img :src="previewUrl" class="w-full h-full rounded-full object-cover shadow-2xl" />
            </div>
        </div>
    </div>
    `
};