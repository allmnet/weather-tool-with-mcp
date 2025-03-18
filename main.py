"""MCP with llama3.1 8b"""

import asyncio
import re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import ollama

# Set the model name to a custom modelfile version of Llama 3.1 8B
MODEL_NAME = "llama3.1-tool:8b"

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="uv",
    args=["run", "server.py"],
)


# Define the weather tool that will be registered
async def get_weather_mcp(city_name):
    """Get today's weather for a specific city using MCP"""
    # as per the example in the MCP Python repo
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
            # Call the tool
            result = await session.call_tool(
                "get_todays_weather", arguments={"city_name": city_name}
            )
            return result


# This function will be called when the tool is invoked
def get_todays_weather(city_name):
    """
    This is the tool function that gets registered.
    It calls our async MCP function and returns the result.
    """
    print(f"🔧 Tool called for city: {city_name}")
    if (
        city_name.lower() == "nowhere"
    ):  # for some reason it decides to call the tool with "nowhere" as the city name sometimes if it wants nothing to happen
        print("Tool call skipped - no city name provided")
        return ""

    # run the tool
    result = asyncio.run(get_weather_mcp(city_name))

    return result


def get_tools():
    """Get the tools in OpenAI-compatible format"""
    # this defines the tool for the LLM, as per the ollama function calling spec
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_todays_weather",
            "description": "Get the current real weather conditions for a specific city. ONLY USE THIS TOOL FOR WEATHER-RELATED QUERIES.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city_name": {
                        "type": "string",
                        "description": "The name of the city to get weather information for",
                    }
                },
                "required": ["city_name"],
            },
        },
    }
    # return the tool in a list (as per the ollama function calling spec, but also to make it easier in case I wanted to add another tool)
    return [weather_tool]


def is_weather_query(text):
    """
    Determine if a query is weather-related,
    I found this to be the best performing way of determining whether to call the tool or not,
    since llama tends to want to call the tool for everything until I made some modelfile changes,
    but after making the modelfile changes it feels the need to announce that it's NOT calling the tool for some reason.
    """
    # List of weather-related keywords
    weather_keywords = [
        "weather",
        "temperature",
        "forecast",
        "rain",
        "sunny",
        "cloudy",
        "snow",
        "storm",
        "humid",
        "humidity",
        "precipitation",
        "climate",
        "hot",
        "cold",
        "warm",
        "cool",
        "degrees",
        "celsius",
        "fahrenheit",
        "wind",
        "windy",
        "rainy",
        "foggy",
        "thunder",
        "lightning",
        "hail",
    ]

    # Check if any of the keywords are in the query
    text_lower = text.lower()
    for keyword in weather_keywords:
        if keyword in text_lower:
            return True

    # Check for patterns like "How is it in [location]" with weather context
    location_patterns = [
        r"how(?:'s| is) (?:it|the weather) in ([A-Za-z\s]+)",
        r"what(?:'s| is) (?:it|the weather) like in ([A-Za-z\s]+)",
        r"what(?:'s| is) the (?:forecast|temperature) (?:for|in) ([A-Za-z\s]+)",
    ]

    for pattern in location_patterns:
        if re.search(pattern, text_lower):
            return True

    # No weather-related keywords or patterns found
    return False


def process_tool_calls(message):
    """Process tool calls from the model message"""

    # Check if there are tool calls
    if not hasattr(message, "tool_calls") or not message.tool_calls:
        return []

    tool_results = []

    # Process each tool call
    for i, tool_call in enumerate(message["tool_calls"]):
        try:
            # Extract function information
            if not hasattr(tool_call, "function"):
                continue

            function = tool_call.function

            # Get function name
            if not (
                function_name := function.name if hasattr(function, "name") else None
            ):
                continue

            # Get arguments
            if not (
                arguments := (
                    function.arguments if hasattr(function, "arguments") else None
                )
            ):
                continue

            # Get city name
            city_name = None
            if isinstance(arguments, dict):
                city_name = arguments.get("city_name", arguments.get("city", None))

            if not city_name:
                continue

            # Call the function, note that right now the function is hardcoded to be get_todays_weather,
            # but in the future i can use the function name  parameter to call the correct function
            result = get_todays_weather(city_name)

            # Tool call ID
            tool_call_id = getattr(tool_call, "id", f"call_{i}")

            # Add to results as per llama's expectations for a tool call response - convert result to string
            tool_results.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": function_name,
                    "content": str(result),
                }
            )

        except Exception as e:
            print(f"Error processing tool call: {e}")

    return tool_results


def chat_with_llama(messages, tools_enabled=None):
    """Utility function to chat with the model using tools"""

    # Get the last user message
    last_user_message = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )

    # Decide whether to use tools based on the message content
    # note that None is equivalent to auto
    if tools_enabled is None:
        tools_enabled = is_weather_query(last_user_message)

    if tools_enabled:
        print("📝 Tools enabled")  # Just to let the user know

    try:
        # Options for the model
        options = {
            "temperature": 0.7
        }  # Default for normal conversation, can be adjusted, but seems to work well

        if tools_enabled:
            options["temperature"] = (
                0.1  # Lower for tool calls, can be adjusted, but seems to work well
            )

            # First message to get response (may include tool calls)
            response = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                options=options,
                tools=get_tools(),
            )

            message = response["message"]

            # Check if there are tool calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                # Process the tool calls
                if tool_results := process_tool_calls(message):
                    # Create updated messages with the tool results
                    updated_messages = messages.copy()

                    # Add the assistant's message
                    message_dict = {"role": "assistant", "content": message.content}

                    # Add tool_calls if present in a way that can be serialized
                    if hasattr(message, "tool_calls"):
                        tool_calls_serialized = []
                        for tc in message.tool_calls:
                            if hasattr(tc, "function"):
                                tc_dict = {
                                    "id": getattr(tc, "id", "unknown_id"),
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments,
                                    },
                                }
                                tool_calls_serialized.append(tc_dict)

                        message_dict["tool_calls"] = tool_calls_serialized

                    updated_messages.append(message_dict)

                    # Add tool results to messages
                    for result in tool_results:
                        updated_messages.append(result)

                    # Get final response with the tool results
                    final_response = ollama.chat(
                        model=MODEL_NAME,
                        messages=updated_messages,
                        options={"temperature": 0.7},  # Higher for natural response
                    )

                    return final_response
        else:
            # Normal conversation without tools
            response = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                options=options,
            )
            return response

        # Either tools were not enabled or no tool calls were made
        return response

    except Exception as e:
        print(f"Error: {e}")

        # Create a simple response with error message so client code doesn't crash
        class SimpleResponse:
            """Simple response class for error handling"""

            def __init__(self, content):
                self.message = SimpleMessage(content)

        class SimpleMessage:
            """Simple message class for error handling"""

            def __init__(self, content):
                self.content = content

        return SimpleResponse(f"I encountered an error: {str(e)}")


def run_interactive_chat():
    """Run an interactive chat session"""
    messages = []
    print(f"\n=== Interactive Chat with {MODEL_NAME} ===")
    print("Type 'exit' to quit")
    print("Type 'tools on' to enable weather tools")
    print("Type 'tools off' to disable weather tools")
    print("Type 'tools auto' to automatically detect weather queries (default)")

    tools_mode = "auto"  # Default mode

    while True:
        user_input = input("\nYou: ")

        # Handle special commands
        if user_input.lower() == "exit":
            break
        elif user_input.lower() == "tools on":
            tools_mode = "on"
            print("🔧 Tools always enabled")
            continue
        elif user_input.lower() == "tools off":
            tools_mode = "off"
            print("🔧 Tools always disabled")
            continue
        elif user_input.lower() == "tools auto":
            tools_mode = "auto"
            print("🔧 Tools enabled for weather queries only")
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            # Determine if tools should be enabled
            tools_enabled = None  # Auto by default
            if tools_mode == "on":
                tools_enabled = True
            elif tools_mode == "off":
                tools_enabled = False

            # Get response from Llama 3.1
            response = chat_with_llama(messages, tools_enabled)

            # Get the message content safely
            content = ""
            if hasattr(response, "message") and hasattr(response.message, "content"):
                content = response.message.content
            else:
                content = "No response content"

            # Print the assistant's message content
            print(f"\n{MODEL_NAME}: {content}")

            # Add assistant response to conversation history
            messages.append({"role": "assistant", "content": content})

        except Exception as e:
            print(f"\nError: {e}")
            # Add a placeholder message to continue the conversation
            messages.append(
                {
                    "role": "assistant",
                    "content": "I'm having trouble processing that request.",
                }
            )


if __name__ == "__main__":
    # run tests or interactive chat
    if (
        input(
            "Please type test to enter the test mode instead of the interactive test session: \n"
        )
        == "test"
    ):
        tc_choice = input(
            "Would you like the tests to occur with tool calling on, off, or auto?: \n"
        )
        TC_MODE = None
        if tc_choice == "on":
            TC_MODE = True
        elif tc_choice == "off":
            TC_MODE = False
        input("Press Enter to start the tests...")
        print("Starting tests...")
        test_strings = [
            "What's 13 + 13?",  # shouldn't call a tool
            "What's the weather in London today?",  # should call tool on london
            "What's the weather in Paris today?",  # should call tool on paris
            "How's it in Seattle?",  # should call tool on seattle
            "is seattle hotter today? or nyc?",  # should call tool on seattle and nyc
            "What's a typical sauce for bread?",  # shouldn't call a tool
            "Pineapple on pizza?",  # shouldn't call a tool
            "Do you like quesadillas?",  # shouldn't call a tool
            "What's the weather in Norway today?",  # shouldn't call a tool
            "Where in the world is madagascar?",  # shouldn't call a tool
        ]

        for test_string in test_strings:
            print("\n\n----------------------------------")
            print(f"Testing with input: {test_string}")
            messages = [{"role": "user", "content": test_string}]
            response = chat_with_llama(messages, tools_enabled=TC_MODE)
            print(f"Response: {response.message.content}")
        print("Testing Tool Use Model Finished")
        print("Testing regular ollama")
        for test_string in test_strings:
            print("\n\n----------------------------------")
            print(f"Testing with input: {test_string}")
            messages = [{"role": "user", "content": test_string}]
            response = ollama.chat(model="llama3.1:8b", messages=messages)
            print(f"Response: {response["message"].content}")
    else:
        print("\nStarting interactive chat session...")
        run_interactive_chat()
