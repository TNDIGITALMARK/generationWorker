from typing import Dict, Any
import logging
from .handlers.text2ImageHandler import Text2ImageHandler

logger = logging.getLogger(__name__)

class RoutingController:
    """Central routing controller that directs requests to appropriate handlers"""
    
    def __init__(self):
        # Initialize service handlers
        self.text2image_handler = Text2ImageHandler()
        
        # Service mapping
        self.service_handlers = {
            "text2Image": self.text2image_handler,
            "text2image": self.text2image_handler,  # Accept both variations
        }
    
    async def route_request(self, service: str, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate service handler"""
        try:
            # Normalize service name
            service_lower = service.lower()
            
            # Find appropriate handler
            handler = None
            for service_key, handler_instance in self.service_handlers.items():
                if service_lower == service_key.lower():
                    handler = handler_instance
                    break
            
            if not handler:
                raise ValueError(f"Unknown service: {service}")
            
            logger.info(f"Routing {service}:{task} to handler")
            
            # Route to handler
            result = await handler.handle_request(task, data)
            
            return result
            
        except Exception as e:
            logger.error(f"Routing failed for {service}:{task} - {e}")
            raise e
    
    def get_available_services(self) -> list:
        """Get list of available services"""
        return list(self.service_handlers.keys())
    
    def get_service_tasks(self, service: str) -> list:
        """Get available tasks for a specific service"""
        handler = self.service_handlers.get(service)
        if handler and hasattr(handler, 'get_available_tasks'):
            return handler.get_available_tasks()
        return []