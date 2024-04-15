# Agents for Bedrock

Agents for Bedrock are a capability of Amazon Bedrock that lets you orchestrate interactions between users, foundation models, data sources and software applications.

## bedrock_agent_chat

This demo application allows you to interact (chat) with a Bedrock agent via a shell (e.g. bash/CMD)

**Usage:**

**STEP 1:** Enter configuration in bedrock_agent_chat.cfg
- Ensure that you do *not* use quotes in the values
- Ensure that the required variables AGENT_ID and AGENT_ALIAS_ID have correct values
- By default, the FM used is anthropic.claude-instant-v1
- If you enable traces (ENABLE_TRACE = True), then traces will be logged in a trace logfile.

**STEP 2:** Install the required python modules
```
pip install -r requirements.txt
```

**STEP 3:** Execute script
```
python bedrock_agent_chat.py
```