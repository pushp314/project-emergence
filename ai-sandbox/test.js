        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        let ws;
        const eventsDiv = document.getElementById('events');
        const messagesDiv = document.getElementById('messages');

        function connect() {
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = function() {
                const mel = document.createElement('div');
                mel.className = 'event-item';
                mel.innerHTML = `<span class="agent-identity" style="color: #10b981;">System:</span> Connected to Jarvis Core.`;
                messagesDiv.insertBefore(mel, messagesDiv.firstChild);
            };

            ws.onclose = function(e) {
                const mel = document.createElement('div');
                mel.className = 'event-item';
                mel.innerHTML = `<span class="agent-identity" style="color: #ef4444;">System:</span> Connection lost. Jarvis is rebooting... Retrying in 2s.`;
                messagesDiv.insertBefore(mel, messagesDiv.firstChild);
                setTimeout(function() {
                    connect();
                }, 2000);
            };

            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
            
            // Generic Event Log
            const el = document.createElement('div');
            el.className = 'event-item';
            
            let payloadStr = typeof data.payload === 'object' ? JSON.stringify(data.payload) : data.payload;
            // truncate very long payloads for UI
            if (payloadStr && payloadStr.length > 200) {
                payloadStr = payloadStr.substring(0, 200) + '...';
            }
            
            el.innerHTML = `<span class="event-type">${data.type}</span> <span style="color: var(--text-secondary)">${payloadStr}</span>`;
            eventsDiv.insertBefore(el, eventsDiv.firstChild);

            // Message specific
            if (data.type === "agent.message" || data.type === "agent.think" || data.type === "agent.plan") {
                const mel = document.createElement('div');
                mel.className = 'event-item';
                const id = data.payload.identity || data.payload.agent_id || 'System';
                
                let content = data.payload.content || data.payload.plan || data.payload.thought || '';
                
                mel.innerHTML = `<span class="agent-identity">${id}:</span> ${content}`;
                messagesDiv.insertBefore(mel, messagesDiv.firstChild);
                
                // Play audio if available
                if (data.audio_base64) {
                    const audio = new Audio("data:audio/mp3;base64," + data.audio_base64);
                    audio.play().catch(e => console.error("Audio play failed:", e));
                }
            }
        }; // End of ws.onmessage
        } // End of connect()
        
        // Initialize connection
        connect();

        // --- Always-On Jarvis (Wake Word) Logic ---
        let mediaRecorder;
        let voiceWs;
        let isRecording = false;
        let wakeWordRecognizer;
        const ATOM = document.getElementById('atomCore');
        
        // Initialize Speech Recognition for Wake Word
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            wakeWordRecognizer = new SpeechRecognition();
            wakeWordRecognizer.continuous = true;
            wakeWordRecognizer.interimResults = false;
            wakeWordRecognizer.lang = 'en-US';
            
            wakeWordRecognizer.onstart = function() {
                console.log("Jarvis Wake Word engine listening...");
                // Standby state is default
            };
            
            wakeWordRecognizer.onresult = function(event) {
                const last = event.results.length - 1;
                const transcript = event.results[last][0].transcript.trim().toLowerCase();
                console.log("Heard:", transcript);
                
                if (transcript.includes("jarvis") || transcript.includes("hey jarvis")) {
                    triggerJarvisRecording();
                }
            };
            
            wakeWordRecognizer.onend = function() {
                // Restart to keep always-on listening active
                wakeWordRecognizer.start();
            };
            
            // Auto-start wake word engine
            setTimeout(() => wakeWordRecognizer.start(), 1000);
        } else {
            console.warn("SpeechRecognition API not supported. Wake word disabled.");
        }
        
        function triggerJarvisRecording() {
            if (isRecording) return;
            
            // Pause wake word engine while recording actual command
            if (wakeWordRecognizer) {
                wakeWordRecognizer.onend = null;
                wakeWordRecognizer.stop();
            }
            
            navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                
                if (!voiceWs || voiceWs.readyState !== WebSocket.OPEN) {
                    voiceWs = new WebSocket(`${protocol}//${window.location.host}/ws/voice`);
                }
                
                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0 && voiceWs.readyState === WebSocket.OPEN) {
                        voiceWs.send(event.data);
                    }
                };
                
                // Set UI state
                isRecording = true;
                ATOM.classList.add('listening');
                
                const micBtn = document.getElementById('micBtn');
                micBtn.innerHTML = "🔴 Listening...";
                micBtn.style.backgroundColor = "#ef4444";
                
                mediaRecorder.start();
                
                // Record for exactly 5 seconds then stop
                setTimeout(() => {
                    stopJarvisRecording();
                }, 5000);
                
            }).catch(err => {
                alert("Microphone access denied or unavailable.");
            });
        }
        
        function stopJarvisRecording() {
            if (!isRecording) return;
            
            mediaRecorder.stop();
            isRecording = false;
            
            // Switch to processing state
            ATOM.classList.remove('listening');
            ATOM.classList.add('processing');
            
            const micBtn = document.getElementById('micBtn');
            micBtn.innerHTML = "🎙️ Voice Mode";
            micBtn.style.backgroundColor = "#8b5cf6";
            
            // Re-enable wake word engine after 3 seconds of processing
            setTimeout(() => {
                ATOM.classList.remove('processing');
                if (wakeWordRecognizer) {
                    wakeWordRecognizer.onend = function() { wakeWordRecognizer.start(); };
                    wakeWordRecognizer.start();
                }
            }, 3000);
        }

        // Manual toggle button now triggers the auto-record loop
        function toggleMic() {
            if (isRecording) {
                stopJarvisRecording();
            } else {
                triggerJarvisRecording();
            }
        }

        function sendCommand(cmdType) {
            ws.send(JSON.stringify({ command_type: cmdType }));
        }

        function assignTask() {
            const taskInput = document.getElementById('taskInput');
            const task = taskInput.value.trim();
            if (task) {
                ws.send(JSON.stringify({ command_type: 'ASSIGN_TASK', payload: { task: task } }));
                taskInput.value = '';
                
                // Add a local echo for UX
                const mel = document.createElement('div');
                mel.className = 'event-item';
                mel.innerHTML = `<span class="agent-identity" style="color: #38bdf8;">Human (You):</span> ${task}`;
                messagesDiv.insertBefore(mel, messagesDiv.firstChild);
            }
        }
        
        async function uploadDocument() {
            const fileInput = document.getElementById('fileUpload');
            if (fileInput.files.length === 0) return;
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            const mel = document.createElement('div');
            mel.className = 'event-item';
            mel.innerHTML = `<span class="agent-identity" style="color: #ec4899;">System:</span> Uploading ${file.name}...`;
            messagesDiv.insertBefore(mel, messagesDiv.firstChild);
            
            try {
                const response = await fetch('/api/documents/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                mel.innerHTML = `<span class="agent-identity" style="color: #ec4899;">System:</span> Ingested ${file.name} (${result.chunks_ingested} chunks). Agents can now query it.`;
            } catch (err) {
                mel.innerHTML = `<span class="agent-identity" style="color: #ef4444;">System Error:</span> Failed to upload ${file.name}.`;
            }
            
            // clear input
            fileInput.value = '';
        }
