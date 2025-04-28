from openai import AzureOpenAI
import tiktoken
import sys
import os

class LLMController:
    def __init__(self):
        self.max_context_tokens = 128000
        self.max_response_tokens = 4096
        
        # Load API key and endpoint from environment variables
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        
        if not self.api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is not set")
        if not self.azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set")
            
        self.api_version = "2023-07-01-preview"
        self.client = None

        self.system_prompt_control_list = \
          "The request will include a list of all controls on the screen, in the form of a JSON array.  Each control will have the following properties: " \
          "  - 'id': A unique identifier for the control" \
          "  - 'type': The type of control, can ONLY be 'icon' or 'text'" \
          "  - 'content': The content of the control" \
          "  - 'x': The x coordinate of the control" \
          "  - 'y': The y coordinate of the control" \

        self.system_prompt_actions_available = \
          "Action responses should be an action in the form of a JSON object with the following properties: " \
          "  - 'action': The action to take, can ONLY be 'click', 'type', 'keypress', or 'select'" \
          "  - 'id': The id of the control to act on, must be the integer value from the control list" \
          "  - 'text': The text to type, only used if action is 'type'" \
          "  - 'key': The key to press, only used if action is 'keypress'.  Available keys are 'windows' or 'enter'" \
          "If the task has been completed, return 'task_complete'." \

        self.system_prompt_task_hints = \
          "Here are some hints to know if you're in different states of the OS: " \
          "  - If you're in the login screen, you're looking for the username and password textboxes and the login button" \
          "  - If you're in an application, you're looking for the controls in the application" \
          "  - If you're in the start menu, you're looking for the assorted application names as well as pinned and recommended apps.  If start is up, press the Windows key to dismiss." \
          "  - If you're in the file explorer, you're looking for the files and the folders" \
          "  - If you're in the settings, you're looking for the options and the settings" \
          "  - If you're in the task manager, you're looking for the processes and the applications" \
          "  - If you're in the command prompt, you're looking for the command line and the options"

        self.system_prompt_task = \
          "You are an agent controlling a Windows computer. Each request will include a list of controls on the screen, and your job is determine the next action to take to complete the task." \
          "Only return actions in the specified action response format.  Return no additional text or comments."

        self.system_prompt_action = \
          "You are an agent controlling a Windows computer. Each request will include a list of controls on the screen, and your job is determine what action to take based on the request from the user." \
          "Only return a single action that is very close to the request from the user."

    def setup(self):
        """Initialize the Azure OpenAI client"""
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version="2023-09-01-preview"
        )

    def _process_control_list(self, control_list):
        """Process a control list into a JSON format with normalized screen coordinates.
        
        Args:
            control_list (list): List of controls on the screen

        Returns:
            list: List of processed controls with normalized coordinates
        """
        return [{"id": control["id"], 
                "type": control["type"], 
                "content": control["content"],
                "x": int(control["bbox"][0] * 1920),
                "y": int(control["bbox"][1] * 1080)} for control in control_list]

    def _call_model(self, system_prompt, context_prompt):
        """Call the OpenAI model with the given prompts.
        
        Args:
            system_prompt (str): The system prompt to use
            context_prompt (str): The context prompt containing the task and controls

        Returns:
            str: The model's response
        """
        print("Calling the model with the following context: " + context_prompt)

        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": system_prompt
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": context_prompt
                        }
                    ]
                }
            ],
            max_tokens=self.max_response_tokens,
            response_format={"type": "text"}
        )

        response = completion.choices[0].message.content
        print("Got response from the model:")
        print(response)
        return response

    def get_task_response(self, task_string, control_list):
        """Process an action string and get LLM analysis
        
        Args:
            task_string (str): String containing the action to process
            control_list (list): List of controls on the screen

        Returns:
            str: The task to accomplish or 'task_complete' if the task is complete
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Call setup() first.")

        control_json = self._process_control_list(control_list)

        system_prompt = self.system_prompt_task + "\n" + self.system_prompt_control_list + "\n" + self.system_prompt_actions_available + "\n" + self.system_prompt_task_hints

        context_prompt = "I'm trying to accomplish the following task: " + task_string + "\n"
        context_prompt += "The controls on the screen are:\n" + "\n".join(str(control) for control in control_json) + "\n"

        return self._call_model(system_prompt, context_prompt)

    def get_action_response(self, action_string, control_list):
        """Process a single action request and determine what action to take
        
        Args:
            action_string (str): String containing the single action to perform
            control_list (list): List of controls on the screen

        Returns:
            dict: A dictionary containing the action details (type, coordinates, text, etc.)
            or 'task_complete' if no action is needed
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Call setup() first.")

        control_json = self._process_control_list(control_list)

        system_prompt = self.system_prompt_action + "\n" + self.system_prompt_control_list + "\n" + self.system_prompt_actions_available

        context_prompt = "I need to perform this single action: " + action_string + "\n"
        context_prompt += "The controls on the screen are:\n" + "\n".join(str(control) for control in control_json) + "\n"
        context_prompt += "Please respond with the single action to take.  If you can't determine the action, respond with 'task_complete'."

        return self._call_model(system_prompt, context_prompt)


# Example usage
if __name__ == "__main__":
    controller = LLMController()
    controller.setup()
    # Assuming comment_file is defined somewhere
    if len(sys.argv) > 1:
        comment_file = sys.argv[1]
        controller.process_comments(comment_file)
    else:
        print("Please provide a comment file path as an argument.")
