import os 
from dotenv import load_dotenv

load_dotenv(dotenv_path="./config/.env")

def invoke(self, messages):
    if self.session_id and self.agent_with_history:
        # Handling both message format and direct input
        # Extracting the last user message
        user_input = ""
        if isinstance(messages, list) and len(messages) > 0:
            for msg in messages:
                if hasattr(msg, 'content') and msg.__class__.__name__ == 'HumanMessage':
                    user_input = msg.content
                    break
        elif isinstance(messages, str):
            user_input = messages
        else:
            user_input = str(messages)
        
        if user_input:
            # Create run config with session_id and callbacks
            run_config = {
                "configurable": {"session_id": self.session_id},
                "callbacks": self.callbacks
            }
            
            print(f"🔄 Invoking agent with session: {self.session_id[:8]}...")
            result = self.agent_with_history.invoke(
                {"input": user_input},
                config=run_config,
            )
            print(f"✅ Agent invocation completed")
            return result
        else:
            return {"output": "No valid input provided."}
    else:
        # If no session_id is provided, using original existing buffer memory
        if isinstance(messages, list) and len(messages) > 0:
            user_input = ""
            chat_history = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    if msg.__class__.__name__ == 'HumanMessage':
                        user_input = msg.content
                    elif msg.__class__.__name__ == 'SystemMessage':
                        continue
                    else:
                        chat_history.append(msg)
            
            if user_input:
                return self.agent_executor.invoke({
                    "input": user_input,
                    "chat_history": chat_history
                }, config={"callbacks": self.callbacks})
            else:
                return {"output": "No valid input provided."}
        else:
            # Handle string input or other formats
            input_str = str(messages) if messages else ""
            if input_str:
                return self.agent_executor.invoke(
                    {"input": input_str}, 
                    config={"callbacks": self.callbacks}
                )
            else:
                return {"output": "No valid input provided."}      
          


def stream(self, messages):
    # For streaming, use the LLM directly with a simplified approach
    if isinstance(messages, list):
        # Convert messages to a single prompt
        prompt_parts = []
        for msg in messages:
            if hasattr(msg, 'content'):
                if msg.__class__.__name__ == 'SystemMessage':
                    prompt_parts.append(f"System: {msg.content}")
                elif msg.__class__.__name__ == 'HumanMessage':
                    prompt_parts.append(f"Human: {msg.content}")
                elif msg.__class__.__name__ == 'AIMessage':
                    prompt_parts.append(f"Assistant: {msg.content}")
        full_prompt = "\n\n".join(prompt_parts)
        full_prompt += "\n\nAssistant: "
        # Stream the response with callbacks
        print(f"🔄 Streaming response...")
        for chunk in self.llm.stream(full_prompt, config={"callbacks": self.callbacks}):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk
    else:
        # Fallback for non-list input
        for chunk in self.llm.stream(str(messages), config={"callbacks": self.callbacks}):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk