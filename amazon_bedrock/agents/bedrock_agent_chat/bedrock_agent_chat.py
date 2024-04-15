# Shell interaction with an Amazon Bedrock Agent.
# Pre-requisites: (1) Amazon Bedrock Agent configured and working
#                 (2) Required permissions - Refer https://docs.aws.amazon.com/bedrock/latest/userguide/security_iam_id-based-policy-examples-agent.html
#
import boto3
import botocore
import sys
import json
import uuid
import time
import datetime
import configparser
from pathlib import Path, PurePath
from termcolor import colored


# Create Bedrock clients
client = boto3.client('bedrock-agent')
runtime_client = boto3.client('bedrock-agent-runtime')

# Assign variables and parse configuration file
session_id = str(uuid.uuid4())
script_dir = Path((PurePath(sys.argv[0]).parent)).resolve(strict=True)
cfg_file = script_dir / f'{PurePath(sys.argv[0]).stem}.cfg'
trace_log = script_dir / f'{PurePath(sys.argv[0]).stem}_trace_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log'
config = configparser.ConfigParser()
config.read(cfg_file)
agent_config = config['AGENT_CONFIG']
model_id = agent_config.get('MODEL_ID') if agent_config.get('MODEL_ID') != "" else "anthropic.claude-instant-v1"
agent_id = agent_config.get('AGENT_ID')
agent_alias_id = agent_config.get('AGENT_ALIAS_ID') 
enable_trace = bool(agent_config.get('ENABLE_TRACE')) if agent_config.get('ENABLE_TRACE') != "" else False
agent_personna = agent_config.get('AGENT_PERSONNA') if agent_config.get('AGENT_PERSONNA') != "" else "Agent" 
chat_greeting = f"\nHello I'm the {agent_personna}. How may I help you?"
chat_end_instruction = f"To end the conversation, type bye and check traces in {trace_log}" if enable_trace else "To end the conversation, type bye"

# Check if required values are present in configuration file
if any(var == "" for var in (agent_id, agent_alias_id)):
     print(colored(f"\nError: Please check the configuration file ({cfg_file}) for required values\n", "red"))
     sys.exit(1)


def validate_bedrock_agent(agent_id: str) -> None:
        """Function to validate the bedrock agent"""
        try:
            global agent_details
            agent_details = client.get_agent(agentId=agent_id)
        except botocore.exceptions.ClientError as ce:
             print(colored(f"Error validating Bedrock Agent. Check AGENT_ID and AGENT_ALIAS_ID in the configuration file. \n{ce}", "red"))
             raise


def invoke_bedrock_agent(model_id:str,
                  agent_alias_id:str,
                  agent_id: str,
                  session_id: str,
                  prompt: str) -> str:
        """Function to invoke a bedrock agent"""

        # Get agent details
        agent_model_id = agent_details['agent']['foundationModel']
        agent_name = agent_details['agent']['agentName']
        agent_resource_role_arn = agent_details['agent']['agentResourceRoleArn']

        # Update agent configuration with modelid specified in config
        try:
            if model_id != agent_model_id:
                client.update_agent(
                        agentId=agent_id,
                        agentName=agent_name,
                        agentResourceRoleArn=agent_resource_role_arn,
                        foundationModel=model_id
                )
        except botocore.exceptions.ClientError as ce:
             print(colored(f"Error updating Bedrock Agent \n{ce}", "red"))
             raise
                        
        # Invoke the bedrock agent
        try:      
            response = runtime_client.invoke_agent(
                agentAliasId=agent_alias_id,
                agentId=agent_id,
                enableTrace=enable_trace,
                endSession=False,
                sessionId=session_id,
                inputText=prompt
            )
        except botocore.exceptions.ClientError as ce:
             print(colored(f"Error invoking Bedrock Agent \n{ce}", "red"))
             raise

        # Parse the EventStream object in the response
        try:
            event_stream = response['completion']
            eventstream_response = ""
            for event in event_stream:
                if 'chunk' in event:
                    data = event['chunk']['bytes']
                    eventstream_response += data.decode('utf8')
                elif 'trace' in event:
                                if enable_trace:  
                                     with open(trace_log, mode='a') as w:
                                        w.write(json.dumps(event['trace'], indent=2))
            return eventstream_response
        except botocore.exceptions.ClientError as ce:
            print(colored(f"Error parsing Bedrock Agent response. Check the values of AGENT_ID and AGENT_ALIAS_ID in the configuration file \n{ce}", "red"))
            raise

        
def main():
     validate_bedrock_agent(agent_id)
     print(chat_greeting)
     agent_execution_time = 0
     # Loop for an interactive conversation with the agent
     while True:
        user_input = input(f"\n{colored('You','blue','on_white', ['bold'])}: ")
        if user_input.lower() == "bye":
            print(f"\nBye! Have a great day!\n\n{'*'*80}\nFoundation model = {model_id} | Total Bedrock Agent execution time ~ {agent_execution_time:.2f} seconds.\n{'*'*80}")
            break
        else:
            start_time = time.time()
            agent_response = invoke_bedrock_agent(model_id, agent_alias_id, agent_id, session_id, user_input)
            end_time = time.time()
            agent_execution_time += float(f"{end_time - start_time:.2f}")
            print(f"""\n{colored(agent_personna,'red', 'on_white', ['bold'])}: \n{agent_response}\n\n{'*'*80}\nExecution time: {end_time - start_time:.2f} seconds\n{chat_end_instruction}\n{'*'*80}""")
    

if __name__ == "__main__":
     main()