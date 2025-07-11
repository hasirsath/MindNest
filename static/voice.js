
  const micBtn = document.getElementById('micBtn');
  const entry = document.getElementById('entry');
  const languageSelect = document.getElementById('language');
  const journalForm = document.getElementById('journalForm');

  let isRecording = false;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();

  recognition.continuous = true;
  recognition.interimResults = false;

  micBtn.addEventListener('click', () => {
    if (isRecording) {
      recognition.stop();
      micBtn.classList.remove('active');
      isRecording = false;
    } else {
      recognition.lang = languageSelect?.value || 'en-IN';
      recognition.start();
      micBtn.classList.add('active');
      isRecording = true;
    }
  });

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript.trim();
    if (transcript) {
      entry.value += (entry.value ? ' ' : '') + transcript;
    }
  };

  recognition.onerror = (event) => {
    console.error('Speech recognition error:', event.error);
    alert('Voice input error: ' + event.error);
    micBtn.classList.remove('active');
    isRecording = false;
  };

  recognition.onend = () => {
    micBtn.classList.remove('active');
    isRecording = false;
  };

  // Prevent form submission if both voice and text are empty
  journalForm.addEventListener('submit', (e) => {
    if (!entry.value.trim()) {
      e.preventDefault();
      alert('Please type or speak something before submitting your journal entry.');
    }
  });
