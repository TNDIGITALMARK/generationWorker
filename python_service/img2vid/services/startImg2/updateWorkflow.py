from typing import Dict, Any
import logging
import json
import os
import copy

logger = logging.getLogger(__name__)

class UpdateWorkflowService:
    """Service for updating workflow JSON with user parameters"""
    
    def __init__(self):
        # Path to workflow template
        self.template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'workflows',
            'workflow-wan22-image-2-video-nsfw-axtxs1ISH3F3mrVSCSyt-civet_flawless_61-openart.ai.json'
        )
    
    async def update_workflow_with_params(self, job_id: str, file_name: str, prompt: str) -> Dict[str, Any]:
        """Update workflow template with user parameters"""
        try:
            logger.info(f"Updating workflow for job: {job_id}")
            
            # Load workflow template
            workflow_template = await self._load_workflow_template()
            
            # Create deep copy to avoid modifying original
            workflow = copy.deepcopy(workflow_template)
            
            # Update workflow with user parameters
            self._update_image_node(workflow, file_name)
            self._update_prompt_node(workflow, prompt)
            
            logger.info(f"Workflow updated successfully for job: {job_id}")
            logger.info(f"Updated parameters - image: {file_name}, prompt: {prompt}")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to update workflow: {e}")
            raise e
    
    async def _load_workflow_template(self) -> Dict[str, Any]:
        """Load workflow template from file"""
        try:
            if not os.path.exists(self.template_path):
                raise FileNotFoundError(f"Workflow template not found: {self.template_path}")
            
            with open(self.template_path, 'r') as f:
                template = json.load(f)
            
            logger.info("Workflow template loaded successfully")
            return template
            
        except Exception as e:
            logger.error(f"Failed to load workflow template: {e}")
            raise e
    
    def _update_image_node(self, workflow: Dict[str, Any], file_name: str):
        """Update LoadImage node (137) with new filename"""
        try:
            # Node 137 is the LoadImage node
            nodes = workflow.get("nodes", [])
            node_found = False
            
            # Find node 137 in nodes array
            for node in nodes:
                if node.get("id") == 137:
                    node_found = True
                    if "widgets_values" in node and len(node["widgets_values"]) > 0:
                        node["widgets_values"][0] = file_name
                        logger.info(f"Updated LoadImage node with filename: {file_name}")
                    else:
                        logger.warning(f"LoadImage node (137) found but no widgets_values: {node}")
                    break
            
            if not node_found:
                logger.warning("LoadImage node (137) not found in workflow")
                
        except Exception as e:
            logger.error(f"Failed to update image node: {e}")
            raise e
    
    def _update_prompt_node(self, workflow: Dict[str, Any], prompt: str):
        """Update Textbox node (140) with new prompt"""
        try:
            # Node 140 is the Textbox node for prompt
            for node in workflow["nodes"]:
                if node.get("id") == 140:
                    if "widgets_values" in node and len(node["widgets_values"]) > 0:
                        node["widgets_values"][0] = prompt
                        logger.info(f"Updated Textbox node with prompt: {prompt[:100]}...")
                    break
            else:
                logger.warning("Textbox node (140) not found in workflow")
                
        except Exception as e:
            logger.error(f"Failed to update prompt node: {e}")
            raise e