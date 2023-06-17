from langchain.prompts import PromptTemplate

import pinecone
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
from langchain import LLMMathChain, SerpAPIWrapper
from langchain.agents import AgentType, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool, StructuredTool, Tool, tool
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
import openai
from pydantic import BaseModel, Field
import re
from jinja2 import Template
from dotenv import load_dotenv
from langchain.llms.openai import OpenAI
from langchain import LLMChain
from langchain.schema import  Document
from langchain.chains import SimpleSequentialChain
#from heuristic_experience_orchestrator.prompt_template_modification import PromptTemplate
# from langchain.retrievers import TimeWeightedVectorStoreRetriever
import os
from food_scrapers import wolt_tool
import json
from langchain.tools import GooglePlacesTool
import tiktoken
import asyncio
import logging
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI

from langchain.agents.agent_toolkits import ZapierToolkit
from langchain.agents import AgentType
from langchain.utilities.zapier import ZapierNLAWrapper
# redis imports for cache
from langchain.cache import RedisSemanticCache
import langchain
from langchain.callbacks import get_openai_callback
import redis

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
from langchain.llms import Replicate
from redis import Redis
from langchain.cache import RedisCache
import os
from langchain import llm_cache
REDIS_HOST = os.getenv("REDIS_HOST", "promethai-dev-backend-redis-repl-gr.60qtmk.ng.0001.euw1.cache.amazonaws.com")
langchain.llm_cache = RedisCache(redis_=Redis(host=REDIS_HOST, port=6379, db=0))
logging.info("Using redis cache")


class Agent():
    load_dotenv()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL") or "gpt-4"
    GPLACES_API_KEY = os.getenv("GPLACES_API_KEY", "")
    ZAPIER_NLA_API_KEY =  os.environ["ZAPIER_NLA_API_KEY"] = os.environ.get("ZAPIER_NLA_API_KEY", "")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.0))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_API_ENV = os.getenv("PINECONE_API_ENV", "")
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
    REDIS_HOST = os.getenv("REDIS_HOST", "promethai-dev-backend-redis-repl-gr.60qtmk.ng.0001.euw1.cache.amazonaws.com")

    def __init__(self, table_name=None, user_id: Optional[str] = "676", session_id: Optional[str] = None) -> None:
        # self.langchain = langchain  # initialize the Langchain object, modify this as per your requirement
        # self.langchain.llm_cache = RedisCache(redis_=Redis(host='0.0.0.0', port=6379, db=0))
        # langchain.llm_cache = RedisCache(redis_=Redis(host='0.0.0.0', port=6379, db=0))
        self.table_name = table_name
        self.user_id = user_id
        self.session_id = session_id
        # self.memory = None
        self.thought_id_timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]   #  Timestamp with millisecond precision
        self.last_message = ""
        self.openai_model35 = "text-davinci-003"
        self.openai_model4 = "gpt-4"
        self.llm = OpenAI(temperature=0.0,max_tokens = 600, openai_api_key = self.OPENAI_API_KEY, model_name="text-davinci-003")
        self.llm35_fast = OpenAI(temperature=0.0,max_tokens = 1050, openai_api_key = self.OPENAI_API_KEY, model_name=self.openai_model35)
        self.llm_fast = ChatOpenAI(temperature=0.0,max_tokens = 800, openai_api_key = self.OPENAI_API_KEY, model_name="gpt-4")
        self.llm35 = ChatOpenAI(temperature=0.0,max_tokens = 1500, openai_api_key = self.OPENAI_API_KEY, model_name=self.openai_model35)
        # self.llm = ChatOpenAI(temperature=0.0,max_tokens = 1500, openai_api_key = self.OPENAI_API_KEY, model_name="gpt-4")
        self.replicate_llm = Replicate(model="replicate/vicuna-13b:a68b84083b703ab3d5fbf31b6e25f16be2988e4c3e21fe79c2ff1c18b99e61c1", api_token=self.REPLICATE_API_TOKEN)
        self.verbose: bool = True

        # ... (other code here)
        #
        self.openai_temperature = 0.0
        self.index = "my-agent"


        # try:

            # langchain.llm_cache.clear()
        # except:
        #     langchain.llm_cache = RedisCache(redis_=Redis(host='localhost', port=6379, db=0))

    def clear_cache(self):
        langchain.llm_cache.clear()

    def set_user_session(self, user_id: str, session_id: str) -> None:
        self.user_id = user_id
        self.session_id = session_id

    def get_ada_embedding(self, text):
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model="text-embedding-ada-002",api_key =OPENAI_API_KEY)[
            "data"
        ][0]["embedding"]

    def init_pinecone(self, index_name):
            load_dotenv()
            PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
            PINECONE_API_ENV = os.getenv("PINECONE_API_ENV", "")
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_API_ENV)
            return pinecone.Index(index_name)

    def _simple_test(self):
        # langchain.llm_cache = RedisCache(redis_=Redis(host='0.0.0.0', port=6379, db=0))
        with get_openai_callback() as cb:
            # langchain.llm_cache = RedisCache(redis_=Redis(host='0.0.0.0', port=6379, db=0))
            prompt = """ How long does it take to go to the moon on foot """
            prompt = PromptTemplate.from_template(prompt)
            chain = LLMChain(llm=self.llm, prompt=prompt, verbose=self.verbose)
            chain_result = chain.run(prompt=prompt,  name=self.user_id).strip()
            print(cb)

            return chain_result
#
    # create the length function
    def tiktoken_len(self, text):
        tokenizer = tiktoken.get_encoding('cl100k_base')
        tokens = tokenizer.encode(
            text,
            disallowed_special=()
        )
        return len(tokens)
    # class VectorDBInput(BaseModel):
    #     observation: str = Field(description="should be what we are inserting into the memory")
    #     namespace: str = Field(description="should be the namespace of the VectorDB")
    # @tool("_update_memories", return_direct=True, args_schema = VectorDBInput)
    def _update_memories(self, observation: str, namespace: str)-> None:
        """Update related characteristics, preferences or dislikes for a user."""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        self.init_pinecone(index_name=self.index)
        vectorstore: Pinecone = Pinecone.from_existing_index(
            index_name=self.index,
            embedding=OpenAIEmbeddings(),
            namespace=namespace
        )
        from datetime import datetime
        retriever = vectorstore.as_retriever()
        retriever.add_documents([Document(page_content=observation,
                                          metadata={'inserted_at': datetime.now(), "text": observation,
                                                    'user_id': self.user_id}, namespace=namespace)])

    class FetchMemories(BaseModel):
        observation: str = Field(description="observation we want to fetch from vectordb")
    def _fetch_memories(self, observation: str, namespace:str) -> dict[str, str] | str:
        """Fetch related characteristics, preferences or dislikes for a user."""

        self.init_pinecone(index_name=self.index)
        vectorstore: Pinecone = Pinecone.from_existing_index(
            index_name=self.index,
            embedding=OpenAIEmbeddings(),
            namespace=namespace
        )
        retriever = vectorstore.as_retriever()
        retriever.search_kwargs = {'filter': {'user_id': {'$eq': self.user_id}}}
        answer_response= retriever.get_relevant_documents(observation)

        answer_response.sort(key=lambda doc: doc.metadata.get('inserted_at') if 'inserted_at' in doc.metadata else datetime.min,reverse=True)
        try:
            answer_response = answer_response[0]
        except IndexError:
            return {"error": "No document found for this user. Make sure that a query is appropriate"}
        return answer_response.page_content


    def _compute_agent_summary(self, model_speed:str):
        """Computes summary for a person"""
        prompt = PromptTemplate.from_template(
            "How would you summarize {name}'s core characteristics given the"
            + " following statements:\n"
            + "{relevant_preferences}"
            + "{relevant_dislikes}"
            + "Do not embellish."
            + "\n\nSummary: "
        )
        print("Computing Agent Summary")
        self.init_pinecone(index_name=self.index)
        # The agent seeks to think about their core characteristics.

        relevant_preferences = self._fetch_memories(f"Users core preferences", namespace="PREFERENCES")
        relevant_dislikes = self._fetch_memories(f"Users core dislikes", namespace="PREFERENCES")
        print(relevant_dislikes)
        print(relevant_preferences)

        if model_speed =='fast':
            output = self.replicate_llm(prompt)
            return output

        else:
            chain = LLMChain(llm=self.llm, prompt=prompt, verbose=self.verbose)
            return chain.run(name= self.user_id, relevant_preferences=relevant_preferences.page_content, relevant_dislikes=relevant_dislikes.page_content).strip()



    def update_agent_preferences(self, preferences:str):
        """Serves to update agents preferences so that they can be used in summary"""

        prompt = """ The {name} has following {past_preference} and the new {preferences}
                Update user preferences and return a list of preferences
            Do not embellish.
            Summary: """
        self.init_pinecone(index_name=self.index)
        past_preference = self._fetch_memories(f"Users core preferences", namespace="PREFERENCE")
        prompt = PromptTemplate(input_variables=["name", "past_preference", "preferences"], template=prompt)

        # prompt = prompt.format(name=self.user_id, past_preference= past_preference, preferences=preferences)
        chain = LLMChain(llm=self.llm, prompt=prompt, verbose=self.verbose)
        chain_result = chain.run(prompt=prompt,  past_preference= past_preference, preferences=preferences, name=self.user_id).strip()
        return self._update_memories(chain_result, namespace="PREFERENCES")


    def update_agent_taboos(self, dislikes:str):
        """Serves to update agents taboos so that they can be used in summary"""
        prompt =""" The {name} has following {past_dislikes} and the new {dislikes}
                Update user taboos and return a list of dislikes
            Do not embellish.
            Summary: """
        self.init_pinecone(index_name=self.index)
        past_dislikes = self._fetch_memories(f"Users core dislikes", namespace="PREFERENCES")
        prompt = PromptTemplate(input_variables=["name", "past_dislikes", "dislikes"], template=prompt)
        # prompt = prompt.format(name=self.user_id, past_dislikes= past_dislikes, dislikes=dislikes)
        chain = LLMChain(llm=self.llm, prompt=prompt, verbose=self.verbose)
        chain_result = chain.run(prompt=prompt, name=self.user_id, past_dislikes= past_dislikes, dislikes=dislikes).strip()
        return self._update_memories(chain_result, namespace="PREFERENCES")
# ========
#         past_dislikes = self._fetch_memories(f"Users core dislikes", namespace="PREFERENCE")
#         prompt = PromptTemplate(input_variables=["name", "past_dislikes", "dislikes"], template=prompt)
#         prompt = prompt.format(name=self.user_id, past_dislikes= past_dislikes, dislikes=dislikes)
#         return self._update_memories(prompt, namespace="PREFERENCE")
# >>>>>>>> ffaa8fae584048339358bf02769341c5e4b70ef9:main_chains.py


    def update_agent_traits(self, traits:str):
        """Serves to update agent traits so that they can be used in summary"""
        prompt =""" The {name} has following {past_traits} and the new {traits}
                Update user traits and return a list of traits
            Do not embellish.
            Summary: """
        self.init_pinecone(index_name=self.index)

        past_traits = self._fetch_memories(f"Users core dislikes", namespace="PREFERENCES")
        prompt = PromptTemplate(input_variables=["name", "past_traits", "traits"], template=prompt)
        chain = LLMChain(llm=self.llm, prompt=prompt, verbose=self.verbose)
        chain_result = chain.run(prompt=prompt, past_traits= past_traits, traits=traits,name=self.user_id).strip()
        return self._update_memories(chain_result, namespace="PREFERENCES")
# ========
#         past_traits = self._fetch_memories(f"Users core dislikes", namespace="PREFERENCE")
#         prompt = PromptTemplate(input_variables=["name", "past_traits", "traits"], template=prompt)
#         prompt = prompt.format(name=self.user_id, past_traits= past_traits, traits=traits)
#         return self._update_memories(prompt, namespace="PREFERENCE")
# >>>>>>>> ffaa8fae584048339358bf02769341c5e4b70ef9:main_chains.py


    def update_agent_summary(self, model_speed):
        """Serves to update agent traits so that they can be used in summary"""
        summary = self._compute_agent_summary(model_speed=model_speed)
        return self._update_memories(summary, namespace="SUMMARY")


    def prompt_correction(self, prompt_source:str, model_speed:str):
        """Makes the prompt gramatically correct"""

        prompt = """ Gramatically correct sentence: {{prompt_source}} . Return only the corrected sentence.
        """
        template = Template(prompt)
        output = template.render(prompt_source=prompt_source)
        complete_query = PromptTemplate.from_template(output)

        chain = LLMChain(llm=self.llm35_fast, prompt=complete_query, verbose=self.verbose)
        chain_result = chain.run(prompt=complete_query, name=self.user_id).strip()
        json_data = json.dumps(chain_result)
        return json_data

    def recipe_generation(self, prompt:str, model_speed:str):
        """Generates a recipe solution in json"""

        json_example = """{"recipes":[{"title":"value","rating":"value","prep_time":"value","cook_time":"value","description":"value","ingredients":["value"],"instructions":["value"]}]}"""
        prompt_base = """ Create a food recipe based on the following prompt: '{{prompt}}'. Instructions and ingredients should have medium detail.
                 Answer a condensed valid JSON in this format: {{ json_example}}  Do not explain or write anything else."""
        json_example = json_example.replace("{", "{{").replace("}", "}}")
        template = Template(prompt_base)
        output = template.render(prompt=prompt, json_example=json_example)
        complete_query = output
        complete_query = PromptTemplate.from_template(complete_query)

        if model_speed =='fast':
            output = self.replicate_llm(output)
            return output
        else:
            chain = LLMChain(llm=self.llm35_fast, prompt=complete_query, verbose=self.verbose)
            chain_result = chain.run(prompt=complete_query, name=self.user_id).strip()
            #
            # vectorstore: Pinecone = Pinecone.from_existing_index(
            #     index_name=self.index,
            #     embedding=OpenAIEmbeddings(),
            #     namespace='RESULT'
            # )
            # from datetime import datetime
            # retriever = vectorstore.as_retriever()
            # retriever.add_documents([Document(page_content=chain_result,
            #                                   metadata={'inserted_at': datetime.now(), "text": chain_result,
            #                                             'user_id': self.user_id}, namespace="RESULT")])
            logging.info("HERE IS THE CHAIN RESULT", chain_result)
            return chain_result

    def extract_json(self, data):
        json_start = data.find('{')
        json_end = data.rfind('}') + 1
        json_data = data[json_start:json_end]
        try:
            return json.loads(json_data)  # if successful, return Python dict
        except json.JSONDecodeError:
            return None  # if unsuccessful, return None
    async def async_generate(self, prompt_template_base, base_category, base_value):
        """Generates an individual solution choice """
        json_example = """ {"category":"time","options":[{"category":"quick","options":[{"category":"1 min"},{"category":"10 mins"},{"category":"30 mins"}]},{"category":"slow","options":[{"category":"60 mins"},{"category":"120 mins"},{"category":"180 mins"}]}]}"""
        assistant_category = "food"
        # agent_summary = agent_summary.split('.', 1)[0]
        json_example = json_example.replace("{", "{{").replace("}", "}}")
        template = Template(prompt_template_base)
        output = template.render(base_category=base_category, base_value=base_value, json_example=json_example, assistant_category=assistant_category)
        complete_query = PromptTemplate.from_template(output)
        chain = LLMChain(llm=self.llm_fast, prompt=complete_query, verbose=self.verbose)
        chain_result = await chain.arun(prompt=complete_query, name=self.user_id)
        print("here it is",chain_result)
        json_o = json.loads(chain_result)
        value_list = [{"category": value} for value in base_value.split(',')]
        # json_o["options"].append({"category": "Your preferences", "options": value_list})
        chain_result = json.dumps(json_o)
        print("FINAL CHAIN",chain_result)
        return chain_result


    async def generate_concurrently(self, base_prompt):
        """Generates an async solution group"""
        list_of_items = [item.split("=") for item in base_prompt.split(";")]
        prompt_template_base =""" Decompose decision point '{{ base_category }}' into three relevant decision categories each that help when AI is helping person in choosing {{ assistant_category }}.Keep relevant to {{base_category}}, dont provide irrelevant values.
        For each of the options provide a mind map representation of four secondary nodes that can be used to narrow down the {{ assistant_category }} choice better. Generate very short json, do not write anything besides json, follow this json property structure : {{json_example}}"""
        # prompt_template_base = """  Decompose decision point '{{ base_category }}' statement into relatable base decision points that have to do with {{ assistant_category }}.
        #  For each of the  decisions points  provide a mind map representation of the three secondary nodes  related to {{ assistant_category }} that can be used to narrow down the choice better.
        #  The answer should be one line follow this property structure : {{json_example}}"""
        list_of_items = base_prompt.split(";")

        # If there is no ';', split on '=' instead
        if len(list_of_items) == 1:
            list_of_items = [list_of_items[0].split('=')]
        else:
            list_of_items = [item.split("=") for item in list_of_items]
        tasks = [self.async_generate( prompt_template_base, base_category, base_value) for base_category, base_value in list_of_items]
        results = await asyncio.gather(*tasks)

        if len(results) == 1:
            results_json = json.loads( results[0] )
            return results_json
        else:
            logging.info("HERE ARE THE valid RESULTS %s", len(results))
            print("HERE ARE THE valid RESULTS %s", len(results))
            # Parse each JSON string and add it to a list
            results = [result[result.find('{'):result.rfind('}') + 1] for result in results]
            results_list = [json.loads(result) for result in results]


            # Put the list of results in a dictionary under the "results" key
            combined_json = {"results": results_list}
            return combined_json
        # results_json = list(results_json)

        # print("here", results_json[0])

        # # Now you can concatenate these results into a single JSON
        # combined_json = {"results": results_json}
        # return combined_json

        # tasks = [self.async_generate(prompt_template_base, base_category, base_value) for base_category, base_value in
        #          list_of_items]
        #
        # for task in asyncio.as_completed(tasks):
        #     result = await task
        #     json_result = self.extract_json(result)
        #     if json_result is not None:
        #         yield json_result
    def prompt_to_choose_meal_tree(self, prompt: str, model_speed:str, assistant_category:str):
        """Serves to generate agent goals and subgoals based on a prompt"""
        json_example = '<category1>=<decision1><decision2>;<category2>=<decision2>...'
        prompt_template = """Known user summary: '{{ user_summary }} '.
        Decompose {{ prompt_str }} statement into decision points that include user summary information and related to {{ assistant_category }}.
        Find categories for the decisions points. Do not include personality or update time to categories.
        Present answer in one line and in property structure : {{json_example}}"""
        # prompt_template = """Summarize the user as '{{user_summary}}'.Breakdown '{{prompt_str}}' into decision points relevant to '{{assistant_category}}', excluding
        # personality and update time. Include info from user summary. Present findings in a single line
        # with this format: '{{json_example}}'."""
#         json_str = json_str.replace("{", "{{").replace("}", "}}")
#         prompt_template=""" Decompose {{ prompt_str }} statement into four decision points that are
#         relevant to statement above, personal to the user if possible and that he should apply to optimize his decision choices related to food.
#          Also, help me decompose the decision points into five categories each, starting with the default option provided in the statement exactly as it is.
#          For each of the four options  provide a mind map representation of the four secondary nodes that can be used to narrow down the choice better. Don't leave options blank.
#          Please provide the response in JSON format with proper syntax, ensuring that all strings are enclosed in double quotes,in maximum three lines with no whitespaces. The structure should follow this structure : {{json_str}}
#         """

        self.init_pinecone(index_name=self.index)
        try:
            agent_summary = self._fetch_memories(f"Users core summary", namespace="SUMMARY")
            print("HERE IS THE AGENT SUMMARY", agent_summary)

            agent_summary=str(agent_summary)

            if str(agent_summary) == "{'error': 'No document found for this user. Make sure that a query is appropriate'}":
                agent_summary = "None."
        except:
            pass
        agent_summary = agent_summary.split('.', 1)[0]
        template = Template(prompt_template)

        output = template.render(prompt_str = prompt, json_example=json_example, user_summary=agent_summary,assistant_category= assistant_category)
        complete_query =  output
        print("HERE IS THE COMPLETE QUERY", complete_query)
        complete_query = PromptTemplate.from_template(complete_query)

        if model_speed =='fast':
            output = self.replicate_llm(output)
            json_data = json.dumps(output)
            return json_data
        else:
            chain = LLMChain(llm=self.llm_fast, prompt=complete_query, verbose=self.verbose)
            chain_result = chain.run(prompt=complete_query, name=self.user_id).strip()
            # end = time.time()
            #
            # # logging.info("HERE IS THE CHAIN RESULT %s", chain_result)

            vectorstore: Pinecone = Pinecone.from_existing_index(
                index_name=self.index,
                embedding=OpenAIEmbeddings(),
                namespace='GOAL',
            )
            from datetime import datetime
            retriever = vectorstore.as_retriever()
            logging.info(str(chain_result))
            retriever.add_documents([Document(page_content=chain_result,
                                            metadata={'inserted_at': datetime.now(), "text": chain_result,
                                                        'user_id': self.user_id}, namespace="GOAL")])
            return chain_result.replace("'", '"')


    async def prompt_decompose_to_meal_tree_categories(self, prompt: str, model_speed:str):
        """Serves to generate agent goals and subgoals based on a prompt"""
        import time

        start = time.time()
        combined_json = await self.generate_concurrently(prompt)
        end = time.time()

        logging.info(f"Execution time: {end - start} seconds")

        return combined_json
        # async for result in self.generate_concurrently(prompt):
        #     yield result

    def prompt_to_update_meal_tree(self,  category:str, from_:str, to_:str, model_speed:str):

        self.init_pinecone(index_name=self.index)
        vectorstore: Pinecone = Pinecone.from_existing_index(
            index_name=self.index,
            embedding=OpenAIEmbeddings(),
            namespace="GOAL"
        )

        retriever = vectorstore.as_retriever()
        retriever.search_kwargs = {'filter': {'user_id': {'$eq': self.user_id}}}  # filter by user_id
        answer_response = retriever.get_relevant_documents("prompt")
        answer_response.sort(
            key=lambda doc: doc.metadata.get('inserted_at') if 'inserted_at' in doc.metadata else datetime.min,
            reverse=True)

        # The most recent document is now the first element of the list.
        try:
            most_recent_document = answer_response[0]
        except IndexError:
            return {"error": "No document found for this user. Make sure that a query is appropriate"}
        doc = most_recent_document.page_content
        json_str = doc.replace("'", '"')
        document = json.loads(json_str)
        matching_items = [item for item in document['tree'] if item['category'] == category]
        sub_tree = matching_items[0] if matching_items else None
        sub_tree = json.dumps(sub_tree)
        escaped_content = sub_tree.replace("{", "{{").replace("}", "}}")
        logging.info(escaped_content)

        optimization_prompt = """Change the category: {{category}} based on {{from_}} to {{to_}}  change and update appropriate of the following original inluding the preference: {{results}}
         """

        optimization_prompt = Template(optimization_prompt)
        optimization_output = optimization_prompt.render(category=category, from_=from_, to_=to_,  results=escaped_content)
        complete_query = PromptTemplate.from_template(optimization_output)
        # prompt_template = PromptTemplate(input_variables=["query"], template=optimization_output)
        review_chain = LLMChain(llm=self.llm35, prompt=complete_query)
        review_chain_result = review_chain.run(prompt=complete_query, name=self.user_id).strip()
        return review_chain_result.replace("'", '"')



     # def goal_generation(self, factors: dict, model_speed:str):
     #
     #     """Serves to optimize agent goals"""
     #
     #     prompt = """
     #          Based on all the history and information of this user, suggest mind map that would have four decision points that are personal to him that he should apply to optimize his decision choices related to food. It must be food and nutrition related.
     #          The cuisine should be one of the points, and goal should contain one or maximum three words. If user preferences don't override it, and if it includes time elemeent, it should be called "Time to make", if it descibes complexity of the dish, it should be  "Complexity", and if descibing food content it should be called "Macros"
     #          Answer a condensed JSON with no whitespaces. The structure should only contain a list of goals under field "goals". After the JSON output, don't explain or write anything.
     #        """
     #
     #     self.init_pinecone(index_name=self.index)
     #     agent_summary = self._fetch_memories(f"Users core summary", namespace="SUMMARY")
     #     template = Template(prompt)
     #     output = template.render(factors=factors)
     #     complete_query = str(agent_summary) + output
     #     complete_query = PromptTemplate.from_template(complete_query)
     #     if model_speed =='fast':
     #        output = self.replicate_llm(output)
     #        return output
     #     else:
     #        chain = LLMChain(llm=self.llm,  prompt=complete_query, verbose=self.verbose)
     #        chain_result = chain.run(prompt=complete_query).strip()
     #        vectorstore: Pinecone = Pinecone.from_existing_index(
     #            index_name=self.index,
     #            embedding=OpenAIEmbeddings(),
     #            namespace='GOAL'
     #        )
     #        from datetime import datetime
     #        retriever = vectorstore.as_retriever()
     #        retriever.add_documents([Document(page_content=chain_result,
     #                                          metadata={'inserted_at': datetime.now(), "text": chain_result,
     #                                                    'user_id': self.user_id}, namespace="GOAL")])
     #        return chain_result

    # def sub_goal_generation(self, factors: dict, model_speed:str):
    #     """Serves to generate sub goals for the user and drill down into it"""
    #
    #     prompt = """
    #         Base
    #         d on all the history and information of this user, GOALS PROVIDED HERE  {% for factor in factors %} '{{ factor['name'] }}'{% if not loop.last %}, {% endif %}{% endfor %}
    #          provide a mind map representation of the secondary nodes that can be used to narrow down the choice better.It needs to be food and nutrition related. Each of the results should have 4 sub nodes.
    #         Answer a condensed JSON with no whitespaces. The strucuture should only contain the list of subgoal items under field "sub_goals".
    #         Every subgoal should have a "goal_name" refers to the goal and the list of subgoals with "name" and a "amount" should be shown as a range from 0 to 100, with a value chosen explicilty and shown based on the personal preferences of the user.
    #         After the JSON output, don't explain or write anything
    #         """
    #
    #     self.init_pinecone(index_name=self.index)
    #     agent_summary = self._fetch_memories(f"Users core summary", namespace="SUMMARY")
    #     template = Template(prompt)
    #     output = template.render(factors=factors)
    #     print("HERE IS THE AGENT SUMMARY", agent_summary)
    #     print("HERE IS THE TEMPLATE", output)
    #     complete_query = str(agent_summary) + output
    #     complete_query = PromptTemplate.from_template(complete_query)
    #     if model_speed =='fast':
    #         output = self.replicate_llm(output)
    #         return output
    #     else:
    #         chain = LLMChain(llm=self.llm,  prompt=complete_query, verbose=self.verbose)
    #         chain_result = chain.run( prompt=complete_query).strip()
    #         vectorstore: Pinecone = Pinecone.from_existing_index(
    #             index_name=self.index,
    #             embedding=OpenAIEmbeddings(),
    #             namespace='SUBGOAL'
    #         )
    #         from datetime import datetime
    #         retriever = vectorstore.as_retriever()
    #         retriever.add_documents([Document(page_content=chain_result,
    #                                           metadata={'inserted_at': datetime.now(), "text": chain_result,
    #                                                     'user_id': self.user_id}, namespace="SUBGOAL")])
    #         print("RESULT IS ", chain_result)
    #         return chain_result

    def extract_info(self, s:str):
        lines = s.split('\n')
        name = lines[0]
        address = lines[1].replace('Address: ', '')
        phone = lines[2].replace('Phone: ', '')
        website = lines[3].replace('Website: ', '')
        return {
            'name': name,
            'address': address,
            'phone': phone,
            'website': website,
        }
    async def restaurant_generation(self, prompt: str, model_speed:str):
        """Serves to suggest a restaurant to the agent"""

        prompt = """
              Based on the following prompt {{prompt}} and all the history and information of this user,
                Determine the type of restaurant you should offer to a customer. Make the recomendation very short and to a point, as if it is something you would type on google maps
            """

        self.init_pinecone(index_name=self.index)
        agent_summary = self._fetch_memories(f"Users core summary", namespace="SUMMARY")
        template = Template(prompt)
        output = template.render(prompt=prompt)
        complete_query = str(agent_summary) + output
        complete_query = PromptTemplate.from_template(complete_query)
        chain = LLMChain(llm=self.llm, prompt=complete_query, verbose=self.verbose)
        chain_result = chain.run(prompt=complete_query).strip()
        GPLACES_API_KEY = self.GPLACES_API_KEY
        places = GooglePlacesTool()
        output = places.run(chain_result)
        restaurants = re.split(r'\d+\.', output)[1:3]
        # Create a list of dictionaries for each restaurant
        restaurant_list = [self.extract_info(r) for r in restaurants]
        print('HERE IS THE OUTPUT', restaurant_list)
        return restaurant_list
    # async def run_wolt_tool(self, zipcode, chain_result):
    #     from food_scrapers import  wolt_tool
    #     return wolt_tool.main(zipcode, chain_result)
    async def delivery_generation(self, prompt: str, zipcode:str, model_speed:str):
        """Serves to optimize agent delivery recommendations"""

        prompt = """
              Based on the following prompt {{prompt}}
                Determine the type of food you would want to recommend to the user, that is commonly ordered online. It should of type of food offered on a delivery app similar to burger or pizza, but it doesn't have to be that.
                The response should be very short
            """

        self.init_pinecone(index_name=self.index)
        agent_summary = self._fetch_memories(f"Users core summary", namespace="SUMMARY")
        template = Template(prompt)
        output = template.render(prompt=prompt)
        complete_query = str(agent_summary) + output
        complete_query = PromptTemplate.from_template(complete_query)
        chain = LLMChain(llm=self.llm, prompt=complete_query, verbose=self.verbose)
        chain_result = chain.run(prompt=complete_query).strip()
        from food_scrapers import wolt_tool
        output = await wolt_tool.main( zipcode=zipcode, prompt=chain_result)
        return output



    def add_zapier_calendar_action(self, context=None):


        zapier = ZapierNLAWrapper()
        toolkit = ZapierToolkit.from_zapier_nla_wrapper(zapier)
        agent = initialize_agent(toolkit.get_tools(), self.llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
        agent.run("Search for and play easy cooking music on Spotify, where rock is search term and Spotify is the app")

        #'https://api.spotify.com/v1/search?q=easy+cooking+music&type=playlist&limit=1'
    def voice_text_input(self, query: str, model_speed: str):

        """Serves to generate sub goals for the user and or update the user's preferences"""
        from langchain.agents import initialize_agent, AgentType
        from pydantic import BaseModel, Field
        from langchain import PromptTemplate
        from langchain.llms.openai import OpenAI
        from langchain.tools import BaseTool, StructuredTool, Tool, tool
        llm=self.llm

        class GoalWrapper(BaseModel):
            observation: str = Field(description="observation we want to fetch from vectordb")

        @tool("goal_update_wrapper", args_schema=GoalWrapper, return_direct=True)
        def goal_update_wrapper(observation,  args_schema=GoalWrapper):
            """Fetches data from the VectorDB and returns it as a python dictionary."""
            query =  self._fetch_memories(observation, "GOAL")
            loop = asyncio.get_event_loop()
            res = loop.run_until_complete(self.prompt_decompose_to_meal_tree_categories(query,  "slow"))
            loop.close()
            return res
        class UpdatePreferences(BaseModel):
            observation: str = Field(description="observation we want to fetch from vectordb")
            # namespace: str = Field(description="namespace of the VectorDB")

        @tool("preferences_wrapper", args_schema=UpdatePreferences, return_direct=True)
        def preferences_wrapper(observation,  args_schema=FetchMemories):
            """Updates user preferences in the VectorDB."""
            return self._update_memories(observation, "PREFERENCES")


        agent = initialize_agent(llm=llm, tools=[goal_update_wrapper, preferences_wrapper], agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

        prompt = """

            Based on all the history and information of this user, classify the following query: {query} into one of the following categories:
            1. Goal update , 2. Preference change,  3. Result change 4. Subgoal update  If the query is not any of these, then classify it as 'Other'
            Return the classification and a very short summary of the query as a python dictionary. Update or replace or remove the original factors with the new factors if it is specified.
            with following python dictionary format 'Result_type': 'Goal', "Result_action": "Goal changed", "value": "Diet added", "summary": "The user is updating their goal to lose weight"
            Make sure to include the factors in the summary if they are provided
            """

        template = Template(prompt)
        output = template.render(query=query)
        complete_query =  output
        complete_query = PromptTemplate(input_variables=["query"], template=complete_query)
        summary_chain = LLMChain(llm=self.llm, prompt=complete_query, verbose=self.verbose)
        from langchain.chains import SimpleSequentialChain


        overall_chain = SimpleSequentialChain(
            chains=[summary_chain, agent],
            verbose=True)
        output = overall_chain.run(query=query)
        return output


    def fetch_user_summary(self, model_speed:str):
        """Serves to retrieve agent summary"""
        self.init_pinecone(index_name=self.index)
        agent_summary = self._fetch_memories(f"Users core summary", namespace="SUMMARY")
        return agent_summary
    def solution_evaluation_test(self):
        """Serves to update agent traits so that they can be used in summary"""
        return


    def solution_implementation(self):
        """Serves to update agent traits so that they can be used in summary"""
        return

    def _retrieve_summary(self):
        """Serves to retrieve agent summary"""
        self.init_pinecone(index_name=self.index)
        result = self._fetch_memories('Users core prompt', "GOAL")
        print(result)
        return result




if __name__ == "__main__":
    agent = Agent()
    # agent._simple_test()
    # agent.goal_optimization(factors={}, model_speed="slow")
    # agent._update_memories("lazy, stupid and hungry", "TRAITS")
    # agent.update_agent_traits("His personality is greedy")
    # agent.update_agent_preferences("Alergic to corn")
    # agent.update_agent_taboos("Dislike is brocolli")
    #agent.update_agent_summary(model_speed="slow")
    #agent.recipe_generation(prompt="I would like a healthy chicken meal over 125$", model_speed="slow")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(agent.prompt_decompose_to_meal_tree_categories("allergy=corn, gluten", "slow"))
    loop.close()
    # agent.prompt_to_choose_meal_tree(prompt="I would like a quick veggie meal under 25 near me. No peanuts I am allergic", model_speed="slow")

    #print(result)
    # agent._test()
    # agent._retrieve_summary()
    #agent.voice_text_input_imp("Core prompt ", model_speed="slow")
