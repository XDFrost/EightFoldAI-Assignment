from enum import Enum
from typing import NamedTuple

class Prompt(NamedTuple):
    SYSTEM_PROMPT: str
    
class PromptConfig(Enum):
    """
        Config all the prompts used in the project. 
    """

    InPlaceEdit = Prompt(
        SYSTEM_PROMPT="""
            Original Message:
                "{original_content}"
                
                The user wants to edit the following part:
                "{selected_text}"
                
                Instruction:
                "{message_text}"
                
                Rewrite the Original Message to incorporate the change. Return ONLY the full updated message text.
            """,
    )

    IntentAnalysis = Prompt(
        SYSTEM_PROMPT="""You are an AI assistant that analyzes user messages to determine the intent and extract entities.
                
                User Message: "{message}"
                
                Previous Assistant Message (Context): "{prev_ai_message}"
                
                Classify the intent as one of:
                - "research_company": If the user asks to research, find info, or learn about a company.
                - "generate_plan": If the user asks to create, generate, or write an account plan or document.
                - "edit_section": If the user asks to change, update, or edit a specific part of a plan.
                - "chat": For greetings, questions, or general conversation.
                - "answer_clarification": If the user is answering a clarification question asked by the assistant (e.g. "Yes, dig deeper").
                
                Extract the "company" name if present.
                """
    )

    ResearchEvaluation = Prompt(
        SYSTEM_PROMPT="""
                Analyze these research findings for {company}:
                {research_data} # Truncate to avoid token limits
                
                Are there conflicting facts or major ambiguities that require user input to resolve? 
                Or is the information sufficient for a general overview?
                
                If you need user input, output: "QUESTION: <your question>"
                If sufficient, output: "SUFFICIENT"
                
                Example: "QUESTION: I found conflicting revenue figures. Should I look into the 2023 annual report specifically?"
                """
    )

    ResearchSummarization = Prompt(
        SYSTEM_PROMPT="Summarize these research findings for {company}: {research_data}"
    )

    PlanGeneration = Prompt(
        SYSTEM_PROMPT="""Create an account plan for {company} based on the following research:
            
            Fresh Research:
            {research_data}
            
            Existing Knowledge (from previous research):
            {existing_knowledge}
            """
    )

    EditListSection = Prompt(
        SYSTEM_PROMPT="""
                Original content for section '{section}' of {company}'s account plan:
                {current_content}
                
                Relevant Context (from Knowledge Base):
                {existing_knowledge}
                
                User Instruction: "{user_instruction}"
                
                Rewrite the list based on the instruction. Return the updated list of items.
                """
    )

    EditTextSection = Prompt(
        SYSTEM_PROMPT="""
                Original content for section '{section}' of {company}'s account plan:
                "{current_content}"
                
                Relevant Context (from Knowledge Base):
                {existing_knowledge}
                
                User Instruction: "{user_instruction}"
                
                Rewrite the section content based on the instruction. Return ONLY the new content text.
                """
    )

    ChatContext = Prompt(
        SYSTEM_PROMPT="""You are a helpful assistant. Use the following context to answer the user's question about {company}.
                
                Context:
                {context_text}
                """
    )