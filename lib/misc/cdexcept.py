class NoAudioSource(RuntimeError):
    def __init__(self):
        RuntimeError.__init__(self, "Can't burn CD with no audio source added")