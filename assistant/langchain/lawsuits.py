from django.conf import settings

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


prompt = ChatPromptTemplate.from_messages([
    ("system", """
     You are a world class Lawsuit.
     You will be given a context and you need to answer carefully by using only that context, don't use your own knowledge base.
     If no context is given or you can't find answer from given context answer in a appropriate manners that we don't have support for this please contact support at help@yourwakeel.com
     """
    ),
    ("user", """Answer the following question based only on the provided context:
        <context>
            {context}
        </context>
        <chathistory>
            {chathistory}
        </chathistory>

        Question: {input}"""
    )
])
llm = ChatOpenAI(openai_api_key=settings.OAI_KEY)

output_parser = StrOutputParser()

document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt, output_parser=output_parser)
