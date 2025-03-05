import logging
import base64
import os
import tempfile
import traceback
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

class ChatHandler:
    """
    Handles text and voice interactions with the virtual patient.
    """
    def __init__(self, case_manager, session_manager, speech_processor):
        self.case_manager = case_manager
        self.session_manager = session_manager
        self.speech_processor = speech_processor
    
    def process_text_chat(self, user_message, include_voice_response=True):
        """
        Processes a text message from the student.
        
        Args:
            user_message (str): Message from the student
            include_voice_response (bool, optional): Whether to include voice in the response
            
        Returns:
            dict: Response data including text and optionally audio
        """
        try:
            if not user_message:
                logger.warning("Empty message received")
                return {"error": "No message provided"}, 400
                
            logger.info(f"Processing text message: {user_message[:30]}... (truncated)")
            
            # Get the current patient agent
            patient_agent = self.case_manager.get_patient_agent()
            if not patient_agent:
                logger.error("No active patient agent")
                return {"error": "No active patient case"}, 500
                
            # Safely record the interaction
            try:
                interaction_index = len(self.session_manager.get_patient_interactions())
                self.session_manager.add_patient_interaction(user_message)
            except Exception as e:
                logger.error(f"Error recording interaction: {str(e)}")
                # Continue anyway since this is not critical
            
            # Process the message with extra error handling
            try:
                result = patient_agent.process_interaction(user_message, include_voice=include_voice_response)
            except Exception as e:
                logger.error(f"Error in patient agent processing: {str(e)}", exc_info=True)
                return {"error": "Error processing your message"}, 500
            
            # Update the interaction with the response
            try:
                if hasattr(self.session_manager, 'update_patient_response'):
                    self.session_manager.update_patient_response(
                        interaction_index,
                        result["text"]
                    )
            except Exception as e:
                logger.error(f"Error updating interaction response: {str(e)}")
                # Continue anyway since this is not critical
            
            # Prepare the response
            response_data = {
                "text": result["text"],
                "timestamp": result["timestamp"]
            }
            
            # Add audio if requested
            if include_voice_response and "audio" in result:
                try:
                    audio_bytes = result["audio"].getvalue()
                    audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                    response_data["audio"] = audio_b64
            
                except Exception as e:
                    logger.error(f"Error processing audio: {str(e)}")
            return response_data, 200
            
        except Exception as e:
            logger.error(f"Unhandled error in text chat processing: {str(e)}", exc_info = True)
            return {"error": "An internal server error ocurred"}, 500
    
    def process_voice_chat(self, audio_file, include_voice_response=True, is_text_input=False, text_message=None):
        """
        Processes a voice message or text message via the voice endpoint.
        
        Args:
            audio_file: Audio file from the request (or None for text input)
            include_voice_response (bool): Whether to include voice in the response
            is_text_input (bool): Whether this is actually a text input via the voice endpoint
            text_message (str, optional): Text message if is_text_input is True
            
        Returns:
            dict: Response data including text and optionally audio
        """
        temp_path = None
        try:
            # Handle text input through voice endpoint
            if is_text_input:
                if not text_message:
                    logger.warning("No text message provided")
                    return {"error": "No message provided"}, 400
                    
                logger.info(f"Text via voice endpoint: {text_message[:30]}... (truncated)")
                return self.process_text_chat(text_message, include_voice_response)
            
            # Regular voice processing
            if not audio_file:
                logger.warning("No audio file provided")
                return {"error": "No audio file provided"}, 400
            
            # Save the audio file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                audio_file.save(temp_file.name)
                temp_path = temp_file.name
            
            try:
                # Transcribe the audio
                logger.info("Transcribing audio...")
                user_message = self.speech_processor.transcribe_audio(temp_path)
                
                if not user_message:
                    logger.warning("Could not transcribe audio")
                    return {"error": "Could not transcribe audio"}, 400
                
                logger.info(f"Transcribed message: {user_message[:30]}... (truncated)")
                
                # Process the transcribed message as text
                return self.process_text_chat(user_message, include_voice_response)
                
            finally:
                # Clean up temporary file
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            error_msg = f"Error processing voice message: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Clean up temporary file on exception
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
            return {"error": error_msg}, 500