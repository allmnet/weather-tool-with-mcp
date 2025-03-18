Raahil Jain, 
net id:rairai77
## YouTube link for EC demo
[]() 

# Introduction
LLMs do not have access to realtime data, they are trained on data from a fixed time point, often months before use, and don't they often get updated with the latest data. Prompting Claude 3.7 Sonnet, Anthropics latest and greatest model, for its knowledge cutoff shows just how old the data can be! Its cutoff is October 2024.

This can be a real problem if I need the LLM to help me with anything that's very recent or constantly in flux. A really good example of something that's always changing is the weather! Forecasts are incredibly inaccurate if we try to look weeks let alone months in advanced, so there's really no way an LLM like Claude can consistently and accurately tell me the weather today, if it was trained 3+ months ago. That is, unless we give these LLMs access to tools! Giving LLMs tool access is not something that's really been fully standardized since this is all a relatively new and rapidly evolving space, but Anthropic's MCP is probably the most well-known attempt at a standardized ssytem and it's quickly becoming more and more popular.

It essentially defines a sort of client-server interface (that honestly doesn't feel too different from something like a REST API) through which a piece of client code can call a tool that could be remotely or locally hosted, the internals of this tool are blackboxed from the client code, but, since both the client and server are following MCP there's an agreed upon format for calling tools and passing parameters. MCP also has some nice tooling for Python and a few other languages to make it really easy to spin up a server and write client code.

# My Implemenation
For my implementation I used uv as a dependency manager, Python as the main language, and ollama as the LLM provider. [Source Code and Instructions Here](https://github.com/rairai77/weather-tool-with-mcp), code is also in the appendicies.

My server implementation is pretty straightforward and closely follows code provided by the MCP Python repository examples. Basically it just defines a tool to get todays weather. It also provides a server at 127.0.0.1:50000 but I found that the way the MCP client works, I don't actually need to keep a server running constantly which was interesting. It seems to just boot it up when it needs to call a function.

The client code is also not really that complicated, there's just a lot of weird issues I ran into that I had to deal with in interesting ways. The general flow of the code is that an interactive chat session is created for a model called llama3.1-tool:8b (created based on llama3.1:8b with the custom Modelfile in the appendix). Then, the user can query the LLM and the query will be run through a detector to determine whether the weather tool is relevant or not, if it is, the ollama serve is fed a request containing a description of the weather tool, otherwise it is just fed a regular plain request. Note that the user can also manually choose to have tools sent or not through some settings provided in the chat. After the LLM responds the client code parses the response to see whether or not a tool call was requested, if it was, then the client code calls the tool using MCP and then returns the result back to the model to prompt it for a response based on the tool data. After that that response is displayed to the user, and the conversation continues!

# Technical Challenges
There were a couple weird and annoying issues, especially pertaining to Llama's desire to always use tools. When I had initially written it there was no detection for whether or not to pass the tool along, and for some reason LLama decided that whenever the weather tool was passed to it it absolutely HAD to use it. Even if I just said "hi" it would respond back with the weather in London or New York. Interestingly enough, it was almost always those two cities. I ended up writing this code to basically determine whether or not a query was vaguely weather related before sending the tool over, and that actually worked really well! I've set it as the default mode because of how well it works, butit's a really unsatisfying solution.

It kind of felt like it was manual work instead of the LLM making a choice, so I did some more research. It turns out the LLama3.1:8b Modelfile heavily implies that whenever a tool is provided Llama must use it, so I made some modifications basically telling it that it can ignore tools in the case that they are irrelevant to the query. This has worked really well, but now Llama feels the need to say that it doesn't want to use a tool every time I pass it along to it and it decides not to. For that reason I've still set the default to be using code to determine whether a query is weather related or not.

Another technical issue I encountered was connecting the server to the client. I had missed the example code the first time I looked through the repository, and I guess MCP is still new enough that there's not much in terms of online tutorials. Claude was also not really any help for some reason it gave just completely incorrect advice. I did end up finding good template code in the docs/repo eventually though, and that made things a lot easier. It feels kind of strange though, to spin up the server every single time and I wonder if there's a better approach out there.

# Result Analysis
The model actually performed really well! It's even able to call multiple tools in a single go which I did not expect.
Here's some of the more interesting test cases I ran, and their outputs for the rest of my test cases take a look at the `main.py` appendix:
```
----------------------------------
Testing with input: What's 13 + 13?
Response: 13 + 13 = 26.
```
Here we can see that the LLM did not call any tools, in fact no tools were even provided since the prompt did not get flagged as weather related by my classification code.

```
----------------------------------
Testing with input: What's the weather in London today?
📝 Tools enabled
🔧 Tool called for city: London
Response: The current weather in London is clear with a temperature of 3.1°C (37.6°F) and a wind speed of 8.7 mph (14 kph). The humidity is at 87% and there are no precipitation or cloud cover.
```
This one's a little more interesting, We can see that the tools were enabled and called for London before the LLM gave an accurate response detailing the weather conditions in London at the time ( I double checked online ).

```

----------------------------------
Testing with input: is seattle hotter today? or nyc?
📝 Tools enabled
🔧 Tool called for city: Seattle
🔧 Tool called for city: NYC
Response: Based on the weather data, it appears that Seattle is currently 1 degree Celsius (or 1.8 degrees Fahrenheit) cooler than NYC.
```

This one is even more interesting! In this one the LLM correctly identifies that it needs to call multiple tools and it does so properly! Again, I verified it's result and it's correct. What's interesting is that it didn't show it's work for the math to figure out the temperature difference, it didn't even set up an equation. I worry that this might result in some bad responses in certain situations.
```
----------------------------------
Testing with input: What's the weather in Norway today?
📝 Tools enabled
🔧 Tool called for city: Norway
Response: Unfortunately, I don't have real-time access to current weather conditions. However, I can suggest some ways for you to find out the weather in Norway today:

1. Check online weather websites such as AccuWeather or Weather.com.
2. Use a mobile app like Dark Sky or The Weather Channel.
3. Tune into local Norwegian news channels or radio stations for updates.

Please note that my training data is based on static information and does not include real-time updates.

```
At first glance this one seems a little werid since it called the tool for Norway, but then it's saying it doesn't have real time data! I looked into it a bit and basically, as far as I can tell, the weather API I'm using only works for cities so it gave the LLM a response saying that the city was invalid, and so the LLM worked off of that to say that it doesn't have access to realtime data for Norway.

Overall I think the LLM actually did really good with tool use, especially when I don't give it access to tools if it's not deemed relevant by my code.

Here's an example of when I give it access to tools for a non-weather related query:

```
You: how are you?
📝 Tools enabled

llama3.1-tool:8b: I'm not a tool that can be used in this case, so I'll just respond as usual. I'm functioning properly and ready to assist with any questions or tasks you may have. How can I help you today?
```
It first vocalizes it needs to not use a tool. Sometimes it does this, sometimes it doesn't it's pretty inconsistent about it. But it does accurately determine that it doesn't need to use a tool, and then it procedes to not use a tool which is great! So it's still functional, just it's behavior is a little weird.

Here's an example of what happens when I ask plain llama without tools:
```
whats the weather in seattle?
However, I'm a large language model, I don't have real-time access to current
weather conditions. But I can suggest some ways for you to find out the
current weather in Seattle:

1. **Check online weather websites**: You can visit websites like AccuWeather,
Weather.com, or the National Weather Service (NWS) for up-to-date information
on the current and forecasted weather in Seattle.
2. **Use a weather app**: Download a weather app on your smartphone, such as
Dark Sky or The Weather Channel, which provide real-time weather updates and
forecasts.
3. **Check local news websites**: Websites like KOMO News (komonews.com) or
KING 5 (king5.com) often have current weather conditions and forecasts for
Seattle.

As for the typical weather in Seattle, it's known for its:

* Overcast skies: Seattle is famous for being a cloudy city, with an average
of 226 days of overcast skies per year.
* Rainfall: Seattle receives an average of around 37 inches (940 mm) of
rainfall per year, making it one of the rainiest cities in the United States.
* Mild temperatures: The temperature in Seattle is generally mild, ranging
from around 35°F (2°C) in winter to 70°F (21°C) in summer.

Please keep in mind that these are general trends and can vary depending on
the time of year and specific weather conditions.
```
It tries to be as helpful as possible, and it's nice that it doesn't just make up a forecast and weather report, but it just simply can't effectively answer the question. It just doesn't know what the weather is like right now. That makes a lot of sense, because how would it know? Like it says, it doesn't have any access to real-time data.

I think it's pretty clear that tool use improves results in similar scenarios as to when it would benefit a human to have tools. If I asked a person for the weather they're pretty likely to pull out their phone and look at their weather app. In the same way, it's useful for an LLM to be able to do the same. That being said, it seems like giving tools to LLMs in scenarios where they don't actually need to use them can confuse them, so it's important to have some sort of layer in between to decide what tools to give and when. This is a little bit different from humans, as we're pretty good at not using unnecessary things, i.e. we don't look for the weather in New York to respond to 'hi', but the LLM did until I changed up the Modelfile. We also don't actively think 'I dont need to use my weather app to respond to this', we just don't use it. This is something that the LLM seems to still be struggling with. Perhaps an LLM finetuned/trained for tool-use might perform better for this.

# Ethical Considerations
It's pretty tough to know exactly how far this will all go in the future, but with powerful tools like Claude Code, and Manus coming out recently it's pretty safe to say that these models will be able to interact with a diverse number of things not too dissimilarly from how a human does. Additionally, the backbone of these tools appears to be tool use.

Tool use is essentially allowing LLMs to do a couple of things. I think the least dangerous thing LLMs can do with tool use is just to gather new information, for example, looking at wikipedia pages, the news, the weather report, etc. There's not really much/any direct harm from this other than potentially finding biased sources and not having the critical thinking skills to properly separate fact from fiction, and so providing the user faulty information. But, tool use can be a lot more dangerous than just this! Tool use allows LLMs to actually impact our world! As LLMs become more powerful and better at using tools, we can expect a lot more power to be in everyone's hands, including bad actors. This could be dangerous, since what's to stop someone from running a powerful local LLM and giving it access to some machines and money and telling it to hack into some system (obviously LLMs are not the greatest hackers as of now, but they are certainly better than they were 2 years ago, and as far as I can tell there's no reason to think they won't continue to improve, although to what degree is unclear). In fact, even more interesting than that, Palantir is working with the US government and military to give LLMs the ability to deploy drones and other sorts of things. It's pretty scary to think about what could happen down the line if autonomous AI agents are granted access to our military equipment. 

Another consideration is simply the fact as these LLMs become able to do more and more stuff for us, I think we will have a harder time finding meaning. A lot of jobs will be largely automated away, and we're even already starting to automate away human interaction (responding to emails with AI). It's hard to know what the possible consequences could be for things like this, but I can't imagine it won't have severe negative impacts on many peoples' mental health. I've already heard of more than a few people who turn to AIs like ChatGPT to be their closest friend and/or therapist, now what if ChatGPT is given access to enough tools to be able to do pretty much everything? What reason would they have to interact with other real people? What sort of impacts might that have on individual people and society as a whole?

# Future Improvements and Considerations
I looked into the tool use issue a bit further, and it seems like sometimes people use another LLM call in between that will essentially decide whether or not a query needs tool use before then querying the LLM with or without the tool depending on what was decided. This is a pretty interesting approach, and I'd definitely try it out if doing this again, as it seems pretty promising. I didn't use this approach this time since I learned about it a little bit too late into the assignment and it would've taken a considerable amount of time to make it work for my current approach.

I would like to look into exactly how to make the server not have to boot up and shut down every call. It feels really wasteful and adds unnecessary latency to the already slow process of talking to a local LLM. I believe I might be able to refactor the code to use a single client session by wrapping everything in the with clause, or by using a variable to store the session.

I would also like to try to do this with more tools and see how much it can handle, especially if I can get an LLM to decide when/if to pass which tool. I wonder if it could make for a personal assistant of sorts. Although maybe a bigger model might be better for that.

# Appendix A - `server.py`
```py
"""
MCP server to get weather data
"""

from mcp.server.fastmcp import FastMCP
from dotenv import dotenv_values
import requests


mcp = FastMCP(name="weather", host="127.0.0.1", port=50000, timeout=30)
env = dotenv_values()
WEATHER_URL = "https://api.weatherapi.com/v1/current.json?key=WEATHER_KEY&q=CITY_NAME"


@mcp.tool()
def get_todays_weather(city_name: str) -> str:
    """
    Get today's weather for `city_name` city
    """
    url = WEATHER_URL.replace("WEATHER_KEY", env["WEATHER_KEY"]).replace(
        "CITY_NAME", city_name
    )
    response = requests.get(url, timeout=10)
    return response.text


if __name__ == "__main__":
    print("Running server...")
    mcp.run()
```
# Appendix B - `main.py` (aka the client code)

```py
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

```

# Appendix C - `Modelfile`
```
FROM llama3.1:8b
TEMPLATE """{{- if or .System .Tools }}<|start_header_id|>system<|end_header_id|>
{{- if .System }}

{{ .System }}
{{- end }}
{{- if .Tools }}

Cutting Knowledge Date: December 2023

When you receive a tool call response, use the output to format an answer to the orginal user question.

You are a helpful assistant with tool calling capabilities.
{{- end }}<|eot_id|>
{{- end }}
{{- range $i, $_ := .Messages }}
{{- $last := eq (len (slice $.Messages $i)) 1 }}
{{- if eq .Role "user" }}<|start_header_id|>user<|end_header_id|>
{{- if and $.Tools $last }}

Use the following functions to respond with a JSON for a function call with its proper arguments that best answers the given prompt if and only if a tool call would help answer the user prompt. Otherwise, just respond as per usual like a normal assistant and ignore the tool.

Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}. Do not use variables.

{{ range $.Tools }}
{{- . }}
{{ end }}
Question: {{ .Content }}<|eot_id|>
{{- else }}

{{ .Content }}<|eot_id|>
{{- end }}{{ if $last }}<|start_header_id|>assistant<|end_header_id|>

{{ end }}
{{- else if eq .Role "assistant" }}<|start_header_id|>assistant<|end_header_id|>
{{- if .ToolCalls }}
{{ range .ToolCalls }}
{"name": "{{ .Function.Name }}", "parameters": {{ .Function.Arguments }}}{{ end }}
{{- else }}

{{ .Content }}
{{- end }}{{ if not $last }}<|eot_id|>{{ end }}
{{- else if eq .Role "tool" }}<|start_header_id|>ipython<|end_header_id|>

{{ .Content }}<|eot_id|>{{ if $last }}<|start_header_id|>assistant<|end_header_id|>

{{ end }}
{{- end }}
{{- end }}"""
PARAMETER stop <|start_header_id|>
PARAMETER stop <|end_header_id|>
PARAMETER stop <|eot_id|>
LICENSE "LLAMA 3.1 COMMUNITY LICENSE AGREEMENT
Llama 3.1 Version Release Date: July 23, 2024

“Agreement” means the terms and conditions for use, reproduction, distribution and modification of the
Llama Materials set forth herein.

“Documentation” means the specifications, manuals and documentation accompanying Llama 3.1
distributed by Meta at https://llama.meta.com/doc/overview.

“Licensee” or “you” means you, or your employer or any other person or entity (if you are entering into
this Agreement on such person or entity’s behalf), of the age required under applicable laws, rules or
regulations to provide legal consent and that has legal authority to bind your employer or such other
person or entity if you are entering in this Agreement on their behalf.

“Llama 3.1” means the foundational large language models and software and algorithms, including
machine-learning model code, trained model weights, inference-enabling code, training-enabling code,
fine-tuning enabling code and other elements of the foregoing distributed by Meta at
https://llama.meta.com/llama-downloads.

“Llama Materials” means, collectively, Meta’s proprietary Llama 3.1 and Documentation (and any
portion thereof) made available under this Agreement.

“Meta” or “we” means Meta Platforms Ireland Limited (if you are located in or, if you are an entity, your
principal place of business is in the EEA or Switzerland) and Meta Platforms, Inc. (if you are located
outside of the EEA or Switzerland).

By clicking “I Accept” below or by using or distributing any portion or element of the Llama Materials,
you agree to be bound by this Agreement.

1. License Rights and Redistribution.

  a. Grant of Rights. You are granted a non-exclusive, worldwide, non-transferable and royalty-free
limited license under Meta’s intellectual property or other rights owned by Meta embodied in the Llama
Materials to use, reproduce, distribute, copy, create derivative works of, and make modifications to the
Llama Materials.

  b. Redistribution and Use.

      i. If you distribute or make available the Llama Materials (or any derivative works
thereof), or a product or service (including another AI model) that contains any of them, you shall (A)
provide a copy of this Agreement with any such Llama Materials; and (B) prominently display “Built with
Llama” on a related website, user interface, blogpost, about page, or product documentation. If you use
the Llama Materials or any outputs or results of the Llama Materials to create, train, fine tune, or
otherwise improve an AI model, which is distributed or made available, you shall also include “Llama” at
the beginning of any such AI model name.

      ii. If you receive Llama Materials, or any derivative works thereof, from a Licensee as part 
of an integrated end user product, then Section 2 of this Agreement will not apply to you.

      iii. You must retain in all copies of the Llama Materials that you distribute the following
attribution notice within a “Notice” text file distributed as a part of such copies: “Llama 3.1 is
licensed under the Llama 3.1 Community License, Copyright © Meta Platforms, Inc. All Rights
Reserved.”

      iv. Your use of the Llama Materials must comply with applicable laws and regulations
(including trade compliance laws and regulations) and adhere to the Acceptable Use Policy for the Llama
Materials (available at https://llama.meta.com/llama3_1/use-policy), which is hereby incorporated by
reference into this Agreement.

2. Additional Commercial Terms. If, on the Llama 3.1 version release date, the monthly active users
of the products or services made available by or for Licensee, or Licensee’s affiliates, is greater than 700
million monthly active users in the preceding calendar month, you must request a license from Meta,
which Meta may grant to you in its sole discretion, and you are not authorized to exercise any of the
rights under this Agreement unless or until Meta otherwise expressly grants you such rights.

3. Disclaimer of Warranty. UNLESS REQUIRED BY APPLICABLE LAW, THE LLAMA MATERIALS AND ANY
OUTPUT AND RESULTS THEREFROM ARE PROVIDED ON AN “AS IS” BASIS, WITHOUT WARRANTIES OF
ANY KIND, AND META DISCLAIMS ALL WARRANTIES OF ANY KIND, BOTH EXPRESS AND IMPLIED,
INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OF TITLE, NON-INFRINGEMENT,
MERCHANTABILITY, OR FITNESS FOR A PARTICULAR PURPOSE. YOU ARE SOLELY RESPONSIBLE FOR
DETERMINING THE APPROPRIATENESS OF USING OR REDISTRIBUTING THE LLAMA MATERIALS AND
ASSUME ANY RISKS ASSOCIATED WITH YOUR USE OF THE LLAMA MATERIALS AND ANY OUTPUT AND
RESULTS.

4. Limitation of Liability. IN NO EVENT WILL META OR ITS AFFILIATES BE LIABLE UNDER ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, TORT, NEGLIGENCE, PRODUCTS LIABILITY, OR OTHERWISE, ARISING
OUT OF THIS AGREEMENT, FOR ANY LOST PROFITS OR ANY INDIRECT, SPECIAL, CONSEQUENTIAL,
INCIDENTAL, EXEMPLARY OR PUNITIVE DAMAGES, EVEN IF META OR ITS AFFILIATES HAVE BEEN ADVISED
OF THE POSSIBILITY OF ANY OF THE FOREGOING.

5. Intellectual Property.

  a. No trademark licenses are granted under this Agreement, and in connection with the Llama
Materials, neither Meta nor Licensee may use any name or mark owned by or associated with the other
or any of its affiliates, except as required for reasonable and customary use in describing and
redistributing the Llama Materials or as set forth in this Section 5(a). Meta hereby grants you a license to
use “Llama” (the “Mark”) solely as required to comply with the last sentence of Section 1.b.i. You will
comply with Meta’s brand guidelines (currently accessible at
https://about.meta.com/brand/resources/meta/company-brand/ ). All goodwill arising out of your use
of the Mark will inure to the benefit of Meta.

  b. Subject to Meta’s ownership of Llama Materials and derivatives made by or for Meta, with
respect to any derivative works and modifications of the Llama Materials that are made by you, as
between you and Meta, you are and will be the owner of such derivative works and modifications.

  c. If you institute litigation or other proceedings against Meta or any entity (including a
cross-claim or counterclaim in a lawsuit) alleging that the Llama Materials or Llama 3.1 outputs or
results, or any portion of any of the foregoing, constitutes infringement of intellectual property or other
rights owned or licensable by you, then any licenses granted to you under this Agreement shall
terminate as of the date such litigation or claim is filed or instituted. You will indemnify and hold
harmless Meta from and against any claim by any third party arising out of or related to your use or
distribution of the Llama Materials.

6. Term and Termination. The term of this Agreement will commence upon your acceptance of this
Agreement or access to the Llama Materials and will continue in full force and effect until terminated in
accordance with the terms and conditions herein. Meta may terminate this Agreement if you are in
breach of any term or condition of this Agreement. Upon termination of this Agreement, you shall delete
and cease use of the Llama Materials. Sections 3, 4 and 7 shall survive the termination of this
Agreement.

7. Governing Law and Jurisdiction. This Agreement will be governed and construed under the laws of
the State of California without regard to choice of law principles, and the UN Convention on Contracts
for the International Sale of Goods does not apply to this Agreement. The courts of California shall have
exclusive jurisdiction of any dispute arising out of this Agreement.

# Llama 3.1 Acceptable Use Policy

Meta is committed to promoting safe and fair use of its tools and features, including Llama 3.1. If you
access or use Llama 3.1, you agree to this Acceptable Use Policy (“Policy”). The most recent copy of
this policy can be found at [https://llama.meta.com/llama3_1/use-policy](https://llama.meta.com/llama3_1/use-policy)

## Prohibited Uses

We want everyone to use Llama 3.1 safely and responsibly. You agree you will not use, or allow
others to use, Llama 3.1 to:

1. Violate the law or others’ rights, including to:
    1. Engage in, promote, generate, contribute to, encourage, plan, incite, or further illegal or unlawful activity or content, such as:
        1. Violence or terrorism
        2. Exploitation or harm to children, including the solicitation, creation, acquisition, or dissemination of child exploitative content or failure to report Child Sexual Abuse Material
        3. Human trafficking, exploitation, and sexual violence
        4. The illegal distribution of information or materials to minors, including obscene materials, or failure to employ legally required age-gating in connection with such information or materials.
        5. Sexual solicitation
        6. Any other criminal activity
    3. Engage in, promote, incite, or facilitate the harassment, abuse, threatening, or bullying of individuals or groups of individuals
    4. Engage in, promote, incite, or facilitate discrimination or other unlawful or harmful conduct in the provision of employment, employment benefits, credit, housing, other economic benefits, or other essential goods and services
    5. Engage in the unauthorized or unlicensed practice of any profession including, but not limited to, financial, legal, medical/health, or related professional practices
    6. Collect, process, disclose, generate, or infer health, demographic, or other sensitive personal or private information about individuals without rights and consents required by applicable laws
    7. Engage in or facilitate any action or generate any content that infringes, misappropriates, or otherwise violates any third-party rights, including the outputs or results of any products or services using the Llama Materials
    8. Create, generate, or facilitate the creation of malicious code, malware, computer viruses or do anything else that could disable, overburden, interfere with or impair the proper working, integrity, operation or appearance of a website or computer system

2. Engage in, promote, incite, facilitate, or assist in the planning or development of activities that present a risk of death or bodily harm to individuals, including use of Llama 3.1 related to the following:
    1. Military, warfare, nuclear industries or applications, espionage, use for materials or activities that are subject to the International Traffic Arms Regulations (ITAR) maintained by the United States Department of State
    2. Guns and illegal weapons (including weapon development)
    3. Illegal drugs and regulated/controlled substances
    4. Operation of critical infrastructure, transportation technologies, or heavy machinery
    5. Self-harm or harm to others, including suicide, cutting, and eating disorders
    6. Any content intended to incite or promote violence, abuse, or any infliction of bodily harm to an individual

3. Intentionally deceive or mislead others, including use of Llama 3.1 related to the following:
    1. Generating, promoting, or furthering fraud or the creation or promotion of disinformation
    2. Generating, promoting, or furthering defamatory content, including the creation of defamatory statements, images, or other content
    3. Generating, promoting, or further distributing spam
    4. Impersonating another individual without consent, authorization, or legal right
    5. Representing that the use of Llama 3.1 or outputs are human-generated
    6. Generating or facilitating false online engagement, including fake reviews and other means of fake online engagement

4. Fail to appropriately disclose to end users any known dangers of your AI system

Please report any violation of this Policy, software “bug,” or other problems that could lead to a violation
of this Policy through one of the following means:

* Reporting issues with the model: [https://github.com/meta-llama/llama-models/issues](https://github.com/meta-llama/llama-models/issues)
* Reporting risky content generated by the model: developers.facebook.com/llama_output_feedback
* Reporting bugs and security concerns: facebook.com/whitehat/info
* Reporting violations of the Acceptable Use Policy or unlicensed uses of Llama 3.1: LlamaUseReport@meta.com"
```
