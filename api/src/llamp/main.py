
import json
from pathlib import Path
from typing import Any, List

import openai
import pandas as pd
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import MessagesPlaceholder
from langchain.schema import ChatMessage
from langchain.tools import ArxivQueryRun, WikipediaQueryRun
from langchain.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from pydantic import BaseModel

from llamp.ase.tools import NoseHooverMD
from llamp.mp.tools import (
    MaterialsBonds,
    MaterialsDielectric,
    MaterialsElasticity,
    MaterialsMagnetism,
    MaterialsOxidation,
    MaterialsPiezoelectric,
    MaterialsRobocrystallographer,
    MaterialsSimilarity,
    MaterialsStructure,
    MaterialsSummary,
    MaterialsSynthesis,
    MaterialsTasks,
    MaterialsThermo,
)

wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper())

tools = [
    MaterialsSummary(),
    MaterialsSynthesis(),
    MaterialsThermo(),
    MaterialsElasticity(),
    MaterialsMagnetism(),
    MaterialsDielectric(),
    MaterialsPiezoelectric(),
    MaterialsRobocrystallographer(),
    MaterialsOxidation(),
    MaterialsBonds(),
    MaterialsSimilarity(),
    MaterialsTasks(),
    MaterialsStructure(return_direct=True),
    NoseHooverMD(return_direct=True),
    # StructureVis(),
    arxiv,
    wikipedia
] 

# MEMORY_KEY = "chat_history"

llm = ChatOpenAI(temperature=0, model='gpt-3.5-turbo-16k-0613',
                 openai_api_key="sk-xxxxxx")
# llm = ChatOpenAI(temperature=0, model='gpt-4')

memory = ConversationBufferMemory(memory_key="chat_history")

conversational_memory = ConversationBufferWindowMemory(
    memory_key='memory',
    k=5,
    return_messages=True
)
agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
}

agent_executor = initialize_agent(
    agent=AgentType.OPENAI_FUNCTIONS,
    tools=tools,
    llm=llm,
    verbose=True,
    max_iterations=3,
    early_stopping_method='generate',
    memory=conversational_memory,
    agent_kwargs=agent_kwargs,
)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageContent(BaseModel):
    content: str


class ChatMessage(BaseModel):
    role: str
    content: str


BASE_DIR = Path(__file__).resolve().parent

def load_json(file_path: Path) -> Any:
    with file_path.open('r') as file:
        data = json.load(file)
    return data

def load_structures(str: str) -> list[Any]:
    str = str.replace('[structures]', '')
    mp_list = str.split(',')
    res = []
    for mp in mp_list:
        res.append(load_json(BASE_DIR / f'mp/.tmp/{mp}.json'))
    return res

def load_simulations(str: str) -> list[Any]:
    str = str.replace('[simulations]', '')
    d = json.loads(str)

    df = pd.read_csv(  # noqa: PD901
        d['log'], 
        delim_whitespace=True, skiprows=1, header=None, 
        names=['Time[ps]', 'Etot/N[eV]', 'Epot/N[eV]', 'Ekin/N[eV]', 'T[K]', 'stress_xx', 'stress_yy', 'stress_zz', 'stress_yz', 'stress_xz', 'stress_xy']
        )
    
    log_json = df.to_json(orient='records', date_format='iso')

    res = []
    for j in d['jsons']:
        res.append(load_json(j))

    return res, log_json


class MessageInput(BaseModel):
    messages: list[ChatMessage]
    key: str


@app.post("/ask/")
async def ask(data: MessageInput):
    messages = data.messages
    key = data.key
    print(key)
    '''
    chat_history = [lambda x:
                    HumanMessage(content=x.content) if x.role == "user" else AIMessage(
                        content=x.content)
                    for x in messages[:-1]]
    '''
    chat_history = [
        {
            "role": x.role,
            "content": x.content
        } for x in messages[:-1]
    ]

    '''
    output = agent_executor.invoke({
        "input": messages[-1].content,
        'chat_history': chat_history,
    })
    '''
    # update the agent's key
    agent_executor.agent.llm.openai_api_key = key

    output = None
    structures = []
    try:
        output = agent_executor.run(input=messages[-1].content)
        if (output.startswith('[structures]')):
            structures = [*load_structures(output)]
            output = ""
    except openai.error.AuthenticationError:
        output = "[Error] Invalid API key"

    return {
        "responses": [{
            'role': 'assistant',
            'content': output,
        }],
        "structures": structures,
    }

if __name__ == "__main__":
    uvicorn.run(app="app", host="127.0.0.1", port=8000, reload=True)
