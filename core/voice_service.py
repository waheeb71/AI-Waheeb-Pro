#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Recognition Service
خدمة التعرف على الصوت
"""

import logging
import threading
import time
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
import speech_recognition as sr

logger = logging.getLogger(__name__)

class VoiceWorker(QThread):
    """Worker thread for voice recognition"""
    
    # Signals
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    volume_changed = pyqtSignal(float)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = False
        self.should_stop = False
        
        # Configure recognizer
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        
        # Initialize microphone
        self._initialize_microphone()
    
    def _initialize_microphone(self):
        """Initialize microphone"""
        try:
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info("Microphone initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
            self.microphone = None
    
    def run(self):
        """Main recognition loop"""
        if not self.microphone:
            self.error_occurred.emit("الميكروفون غير متاح")
            return
        
        self.is_listening = True
        self.listening_started.emit()
        
        try:
            while not self.should_stop:
                try:
                    # Listen for audio
                    with self.microphone as source:
                        # Adjust for ambient noise periodically
                        if hasattr(self.recognizer, 'adjust_for_ambient_noise'):
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        
                        # Listen for audio with timeout
                        timeout = self.config.get('voice.recognition_timeout', 5)
                        phrase_timeout = self.config.get('voice.phrase_timeout', 1)
                        
                        audio = self.recognizer.listen(
                            source, 
                            timeout=timeout, 
                            phrase_time_limit=phrase_timeout
                        )
                    
                    if self.should_stop:
                        break
                    
                    # Recognize speech
                    language = self.config.get('voice.language', 'ar-SA')
                    text = self.recognizer.recognize_google(audio, language=language)
                    
                    if text.strip():
                        self.text_recognized.emit(text.strip())
                    
                except sr.WaitTimeoutError:
                    # Timeout is normal, continue listening
                    continue
                    
                except sr.UnknownValueError:
                    # Could not understand audio
                    self.error_occurred.emit("لم يتم فهم الصوت، يرجى المحاولة مرة أخرى")
                    
                except sr.RequestError as e:
                    # API error
                    self.error_occurred.emit(f"خطأ في خدمة التعرف على الصوت: {e}")
                    break
                    
                except Exception as e:
                    logger.error(f"Voice recognition error: {e}")
                    self.error_occurred.emit(f"خطأ غير متوقع: {e}")
                    break
        
        finally:
            self.is_listening = False
            self.listening_stopped.emit()
    
    def stop_listening(self):
        """Stop listening"""
        self.should_stop = True
        self.quit()
    
    def get_microphone_list(self):
        """Get list of available microphones"""
        try:
            return sr.Microphone.list_microphone_names()
        except Exception as e:
            logger.error(f"Failed to get microphone list: {e}")
            return []

class VoiceService(QObject):
    """Voice recognition service"""
    
    # Signals
    text_recognized = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    volume_changed = pyqtSignal(float)
    status_changed = pyqtSignal(str)
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.worker = None
        self.is_enabled = config.get('voice.enabled', True)
        self.is_listening = False
        
        # Volume monitoring timer
        self.volume_timer = QTimer()
        self.volume_timer.timeout.connect(self._monitor_volume)
        
        logger.info("Voice service initialized")
    
    def is_available(self) -> bool:
        """Check if voice recognition is available"""
        try:
            # Test if speech_recognition is working
            recognizer = sr.Recognizer()
            microphones = sr.Microphone.list_microphone_names()
            return len(microphones) > 0
        except Exception as e:
            logger.error(f"Voice recognition not available: {e}")
            return False
    
    def start_listening(self):
        """Start voice recognition"""
        if not self.is_enabled:
            self.error_occurred.emit("التحكم الصوتي معطل")
            return
        
        if not self.is_available():
            self.error_occurred.emit("خدمة التعرف على الصوت غير متاحة")
            return
        
        if self.is_listening:
            self.error_occurred.emit("التسجيل قيد التشغيل بالفعل")
            return
        
        try:
            # Stop any existing worker
            if self.worker and self.worker.isRunning():
                self.worker.stop_listening()
                self.worker.wait(3000)
            
            # Create new worker
            self.worker = VoiceWorker(self.config)
            self.worker.text_recognized.connect(self._on_text_recognized)
            self.worker.error_occurred.connect(self._on_error)
            self.worker.listening_started.connect(self._on_listening_started)
            self.worker.listening_stopped.connect(self._on_listening_stopped)
            self.worker.finished.connect(self._on_worker_finished)
            
            # Start worker
            self.worker.start()
            
        except Exception as e:
            logger.error(f"Failed to start voice recognition: {e}")
            self.error_occurred.emit(f"فشل في بدء التعرف على الصوت: {e}")
    
    def stop_listening(self):
        """Stop voice recognition"""
        if self.worker and self.worker.isRunning():
            self.worker.stop_listening()
            self.worker.wait(3000)
        
        self.is_listening = False
        self.volume_timer.stop()
        self.status_changed.emit("تم إيقاف التسجيل")
    
    def toggle_listening(self):
        """Toggle voice recognition"""
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def set_enabled(self, enabled: bool):
        """Enable/disable voice recognition"""
        self.is_enabled = enabled
        self.config.set('voice.enabled', enabled)
        
        if not enabled and self.is_listening:
            self.stop_listening()
    
    def get_microphone_list(self) -> list:
        """Get list of available microphones"""
        try:
            return sr.Microphone.list_microphone_names()
        except Exception as e:
            logger.error(f"Failed to get microphone list: {e}")
            return []
    
    def test_microphone(self) -> bool:
        """Test microphone functionality"""
        try:
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()
            
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
            
            return True
            
        except Exception as e:
            logger.error(f"Microphone test failed: {e}")
            return False
    
    def _on_text_recognized(self, text: str):
        """Handle recognized text"""
        self.text_recognized.emit(text)
        self.status_changed.emit(f"تم التعرف على: {text}")
        logger.info(f"Voice recognized: {text}")
    
    def _on_error(self, error: str):
        """Handle recognition error"""
        self.error_occurred.emit(error)
        self.status_changed.emit(f"خطأ: {error}")
        logger.error(f"Voice recognition error: {error}")
    
    def _on_listening_started(self):
        """Handle listening started"""
        self.is_listening = True
        self.listening_started.emit()
        self.status_changed.emit("جاري الاستماع...")
        self.volume_timer.start(100)  # Update volume every 100ms
        logger.info("Voice listening started")
    
    def _on_listening_stopped(self):
        """Handle listening stopped"""
        self.is_listening = False
        self.listening_stopped.emit()
        self.status_changed.emit("تم إيقاف الاستماع")
        self.volume_timer.stop()
        logger.info("Voice listening stopped")
    
    def _on_worker_finished(self):
        """Handle worker finished"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
    
    def _monitor_volume(self):
        """Monitor microphone volume (simulated)"""
        # This is a simplified volume monitoring
        # In a real implementation, you would capture audio levels
        import random
        if self.is_listening:
            volume = random.uniform(0.1, 0.9) if random.random() > 0.7 else 0.0
            self.volume_changed.emit(volume)
    
    def get_status(self) -> dict:
        """Get voice service status"""
        return {
            'is_available': self.is_available(),
            'is_enabled': self.is_enabled,
            'is_listening': self.is_listening,
            'language': self.config.get('voice.language', 'ar-SA'),
            'microphones': self.get_microphone_list()
        }
    
    def update_settings(self, settings: dict):
        """Update voice settings"""
        for key, value in settings.items():
            self.config.set(f'voice.{key}', value)
        
        # Update enabled state
        if 'enabled' in settings:
            self.set_enabled(settings['enabled'])

