import os 
from dotenv import load_dotenv

load_dotenv(dotenv_path="./config/.env")

def invoke(self, messages):
    # Extract user input and system message from messages
    user_input = ""
    system_prompt = ""
    
    if isinstance(messages, list) and len(messages) > 0:
        for msg in messages:
            if hasattr(msg, 'content'):
                if msg.__class__.__name__ == 'HumanMessage':
                    user_input = msg.content
                elif msg.__class__.__name__ == 'SystemMessage':
                    system_prompt = msg.content
    elif isinstance(messages, str):
        user_input = messages
    else:
        user_input = str(messages)
    
    if not user_input:
        return {"output": "No valid input provided."}
    
    # Combine system prompt with user input for better context
    if system_prompt:
        enhanced_input = f"SYSTEM INSTRUCTIONS: {system_prompt}\n\nUSER REQUEST: {user_input}"
    else:
        enhanced_input = user_input
    
    # Use the agent_executor with enhanced context
    try:
        print(f"🔄 Invoking agent with travel planning context...")
        result = self.agent_executor.invoke({
            "input": enhanced_input,
            "chat_history": []
        })
        print(f"✅ Agent invocation completed")
        return result
    except Exception as e:
        print(f"❌ Direct agent error: {e}")
        # Fallback: try with just user input
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result
        except Exception as e2:
            print(f"❌ Fallback agent error: {e2}")
            # Last resort: try with the user input directly
            try:
                result = self.agent_executor.invoke(user_input)
                return result
            except Exception as e3:
                print(f"❌ Final fallback error: {e3}")
                return {"output": f"Sorry, I encountered an error: {str(e3)}"}
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