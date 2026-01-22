'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useCopilotChat } from "@copilotkit/react-core";
import { Mic, MicOff, Square, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceChatProps {
  className?: string;
  onTranscriptChange?: (transcript: string) => void;
}

export function VoiceChat({ className, onTranscriptChange }: VoiceChatProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  
  const { appendMessage } = useCopilotChat();
  const recognitionRef = useRef<any>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    // Check for browser support
    if (typeof window === 'undefined') {
      setIsSupported(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || 
                              (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setIsSupported(false);
      setError('Speech recognition is not supported in this browser');
      return;
    }

    // Initialize speech recognition
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsRecording(true);
      setError(null);
    };

    recognition.onresult = (event: any) => {
      let finalTranscript = '';
      let interimText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcriptText = result[0].transcript;
        
        if (result.isFinal) {
          finalTranscript += transcriptText + ' ';
        } else {
          interimText += transcriptText;
        }
      }

      if (finalTranscript) {
        setTranscript(prev => prev + finalTranscript);
      }
      setInterimTranscript(interimText);
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      
      switch (event.error) {
        case 'not-allowed':
          setError('Microphone access denied. Please allow microphone access.');
          break;
        case 'no-speech':
          setError('No speech detected. Please try again.');
          break;
        case 'network':
          setError('Network error. Please check your connection.');
          break;
        default:
          setError(`Error: ${event.error}`);
      }
      
      setIsRecording(false);
      setIsProcessing(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    if (onTranscriptChange) {
      onTranscriptChange(transcript + interimTranscript);
    }
  }, [transcript, interimTranscript, onTranscriptChange]);

  const startRecording = useCallback(async () => {
    if (!recognitionRef.current || !isSupported) {
      setError('Speech recognition not available');
      return;
    }

    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      
      // Clear previous transcript
      setTranscript('');
      setInterimTranscript('');
      setError(null);
      
      // Start recognition
      recognitionRef.current.start();
    } catch (err: any) {
      console.error('Error starting recording:', err);
      setError('Could not access microphone. Please check permissions.');
    }
  }, [isSupported]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
    }
    
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    setIsRecording(false);
  }, [isRecording]);

  const sendTranscript = useCallback(async () => {
    const finalText = (transcript + interimTranscript).trim();
    
    if (!finalText) {
      setError('No speech detected. Please try again.');
      return;
    }

    setIsProcessing(true);
    
    try {
      await appendMessage({
        role: 'user',
        content: finalText
      });
      
      // Clear transcript after sending
      setTranscript('');
      setInterimTranscript('');
    } catch (err: any) {
      console.error('Error sending message:', err);
      setError('Failed to send message. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  }, [transcript, interimTranscript, appendMessage]);

  const handleToggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const handleSendAndStop = useCallback(() => {
    stopRecording();
    sendTranscript();
  }, [stopRecording, sendTranscript]);

  if (!isSupported) {
    return (
      <div className={cn("voice-chat p-4 bg-yellow-50 rounded-lg", className)}>
        <p className="text-sm text-yellow-800">
          Voice chat is not supported in this browser. Please use Chrome, Edge, or Safari.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("voice-chat", className)}>
      {/* Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleToggleRecording}
          disabled={isProcessing}
          className={cn(
            "p-3 rounded-full transition-all duration-200",
            isRecording 
              ? "bg-red-500 hover:bg-red-600 text-white animate-pulse" 
              : "bg-blue-500 hover:bg-blue-600 text-white",
            isProcessing && "opacity-50 cursor-not-allowed"
          )}
          title={isRecording ? "Stop recording" : "Start recording"}
        >
          {isProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : isRecording ? (
            <MicOff className="w-5 h-5" />
          ) : (
            <Mic className="w-5 h-5" />
          )}
        </button>

        {isRecording && (
          <button
            onClick={handleSendAndStop}
            className="p-3 rounded-full bg-green-500 hover:bg-green-600 text-white transition-all duration-200"
            title="Send message"
          >
            <Square className="w-5 h-5" />
          </button>
        )}

        {!isRecording && (transcript || interimTranscript) && (
          <button
            onClick={sendTranscript}
            disabled={isProcessing}
            className={cn(
              "px-4 py-2 rounded-lg bg-green-500 hover:bg-green-600 text-white text-sm font-medium transition-all duration-200",
              isProcessing && "opacity-50 cursor-not-allowed"
            )}
          >
            {isProcessing ? "Sending..." : "Send"}
          </button>
        )}
      </div>

      {/* Status indicator */}
      {isRecording && (
        <div className="mt-2 flex items-center gap-2">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <span className="text-sm text-gray-600">Listening...</span>
        </div>
      )}

      {/* Transcript display */}
      {(transcript || interimTranscript) && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-800">
            {transcript}
            <span className="text-gray-400">{interimTranscript}</span>
          </p>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Instructions */}
      {!isRecording && !transcript && !error && (
        <p className="mt-2 text-xs text-gray-500">
          Click the microphone to start voice input
        </p>
      )}
    </div>
  );
}

export default VoiceChat;
