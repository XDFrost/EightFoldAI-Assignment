from app.schemas.websocket_messages import StatusUpdate, AssistantChunk, PlanUpdate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from app.services.knowledge_base import KnowledgeBaseService
from app.services.research_service import ResearchService
from app.schemas.websocket_messages import MessageUpdate
from langchain_core.prompts import ChatPromptTemplate
from app.services.plan_service import PlanService
from app.Config.promptConfig import PromptConfig
from typing import TypedDict, List, Dict, Any
from app.schemas.intent import IntentAnalysis
from app.states.global_state import services
from langgraph.graph import StateGraph, END
from app.core.llm_client import LLMClient
from app.schemas.plan import AccountPlan
from pydantic import BaseModel, Field
from app.utils.logger import logger
import json
import uuid


class SearchQueries(BaseModel):
    tavily_query: str = Field(description="Concise query for Tavily")
    perplexity_query: str = Field(description="Detailed query for Perplexity")

class ListSectionUpdate(BaseModel):
    items: List[str] = Field(description="The updated list of items")

class AgentState(TypedDict):
    messages: List[BaseMessage]
    intent: str
    entities: Dict[str, Any]
    research_data: Dict[str, Any]
    plan_data: Dict[str, Any]
    session_id: str
    user_id: str
    # Pass send_callback as an argument to handle_message and then to nodes.

class Orchestrator:
    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.llm = self.llm_client.get_llm()
        self.research_service = ResearchService()
        self.plan_service = PlanService()
        self.knowledge_base = KnowledgeBaseService()

    async def handle_message(
        self, 
        message_text: str, 
        session_id: str, 
        send_callback, 
        user_id: str = None, 
        selected_text: str = None, 
        source_message_id: str = None,
        save_messages: bool = True
    ) -> None:
        """
        Runs the LangGraph flow.
        """
        supabase = services.get_supabase()
        
        # Handle In-Place Edit
        if source_message_id:
            try:
                # Fetch original message
                orig_msg_res = await supabase.table("messages")\
                                .select("*")\
                                .eq("id", source_message_id)\
                                .single()\
                                .execute()
                
                if not orig_msg_res.data:
                    logger.error("Original message not found")
                    return

                original_content = orig_msg_res.data["content"]
                
                prompt = PromptConfig.InPlaceEdit.value.SYSTEM_PROMPT.format(
                    original_content=original_content,
                    selected_text=selected_text,
                    message_text=message_text
                )
                
                # generate fully then update for in place messages
                response = await self.llm.ainvoke(prompt)
                new_content = response.content
                
                # Update DB
                await supabase.table("messages").update({"content": new_content}).eq("id", source_message_id).execute()
                
                # Notify frontend
                await send_callback(MessageUpdate(payload={"message_id": source_message_id, "content": new_content}))
                return
            
            except Exception as e:
                logger.error(f"Failed to handle in-place edit: {e}")
                return

        # If selected_text is present but no source id, prepend it
        original_message = message_text
        if selected_text and not source_message_id:
             message_text = f"Context: {selected_text}\n\nInstruction: {message_text}"
        
        # Save user message
        if save_messages:
            try:
                await supabase.table("messages").insert({
                    "conversation_id": session_id,
                    "role": "user",
                    "content": original_message 
                }).execute()
            except Exception as e:
                logger.error(f"Failed to save user message: {e}")
        
        # Node Definitions
        
        async def analyze_intent(state: AgentState):
            structured_llm = self.llm.with_structured_output(IntentAnalysis)
            
            prompt = ChatPromptTemplate.from_template(
                PromptConfig.IntentAnalysis.value.SYSTEM_PROMPT
            )
            
            prev_ai_msg = ""
            if len(state["messages"]) > 1 and isinstance(state["messages"][-2], AIMessage):
                prev_ai_msg = state["messages"][-2].content
                
            chain = prompt | structured_llm
            
            try:
                result = await chain.ainvoke({
                    "message": state["messages"][-1].content,
                    "prev_ai_message": prev_ai_msg
                })
                if result is None:
                    logger.warning("LLM returned None for structured output. Defaulting to Chat.")
                    return {"intent": "chat", "entities": {}}
                
                entities_dict = result.entities.dict()
                
                # Broadcast detected intent
                mode_msg = "Chatting..."
                if result.intent == "research_company":
                    mode_msg = f"Researching {entities_dict.get('company', '')}..."
                elif result.intent == "generate_plan":
                    mode_msg = "Generating Plan..."
                elif result.intent == "edit_section":
                    mode_msg = "Editing Plan..."
                
                await send_callback(StatusUpdate(payload={"stage": "intent", "message": mode_msg}))
                
                # For now, assuming that clarification is mostly about research depth.
                if result.intent == "answer_clarification":
                    return {"intent": "research_company", "entities": entities_dict}
                    
                return {"intent": result.intent, "entities": entities_dict}
            except Exception as e:
                logger.error(f"Intent analysis failed: {e}")
                await send_callback(StatusUpdate(payload={"stage": "intent", "status": "Chatting..."}))
                return {"intent": "chat", "entities": {}}

        async def research_node(state: AgentState):
            company = state["entities"].get("company")
            region = state["entities"].get("region")
            if not region:
                region = "General"
            
            user_query = state["messages"][-1].content
            if not user_query:
                user_query = f"Research {company} {region}"
            
            # Check if this is a follow-up 
            is_followup = False
            if len(state["messages"]) > 1 and isinstance(state["messages"][-2], AIMessage):
                last_ai = state["messages"][-2].content
                if "?" in last_ai:
                    is_followup = True
                    # If a follow-up, we append the user's answer to the previous context for the query
                    user_query = f"Context: {last_ai} User Answer: {user_query}. Perform research based on this decision."

            query_gen_llm = self.llm.with_structured_output(SearchQueries)
            
            prev_history = ""
            if len(state["messages"]) > 1:
                prev_history = "\n".join([f"{m.type}: {m.content}" for m in state["messages"][-3:-1]])

            query_prompt = PromptConfig.QueryGeneration.value.SYSTEM_PROMPT.format(
                company=company,
                user_message=user_query,
                prev_history=prev_history
            )
            
            try:
                queries = await query_gen_llm.ainvoke(query_prompt)
                tavily_q = queries.tavily_query
                perplexity_q = queries.perplexity_query
                
                await send_callback(StatusUpdate(payload={"stage": "research", "message": f"Generated queries:\n1. {tavily_q}\n2. {perplexity_q}"}))
            except Exception as e:
                logger.error(f"Query generation failed: {e}")
                tavily_q = user_query
                perplexity_q = user_query

            await send_callback(
                StatusUpdate(
                    payload={"stage": "research", "message": f"Starting research on {company}..."}
                    )
                )
            
            data = await self.research_service.research_company(
                company, 
                region, 
                send_callback, 
                tavily_query=tavily_q, 
                perplexity_query=perplexity_q
            )
            
            # EVALUATION STEP: Check for ambiguity
            # Only do this if a question isn't just asked (to avoid infinite loops)
            # or if the user just answered one, we might want to summarize now.
            
            should_ask_user = False
            question_to_user = ""
            
            if not is_followup:
                eval_prompt = PromptConfig.ResearchEvaluation.value.SYSTEM_PROMPT.format(
                    company=company,
                    research_data=json.dumps(data)[:5000]
                )
                
                eval_response = await self.llm.ainvoke(eval_prompt)
                eval_content = eval_response.content.strip()
                
                if "QUESTION:" in eval_content: 
                    should_ask_user = True
                    # Extract question even if it's not at the start
                    question_to_user = eval_content.split("QUESTION:")[-1].strip()
            
            if should_ask_user:
                # Send question to user and STOP
                await send_callback(AssistantChunk(payload={"message_id": "q_1", "chunk": question_to_user}))
                return {"messages": state["messages"] + [AIMessage(content=question_to_user)]}
            
            # Synthesize Report
            await send_callback(StatusUpdate(payload={"stage": "research", "message": "Synthesizing comprehensive report..."}))
            
            summary_prompt = PromptConfig.ResearchSynthesis.value.SYSTEM_PROMPT.format(
                company=company,
                research_data=json.dumps(data)
            )
            
            # Generate ID for the message
            message_id = str(uuid.uuid4())
            
            full_summary = ""
            async for chunk in self.llm.astream(summary_prompt):
                content = chunk.content
                if content:
                    full_summary += content
                    await send_callback(AssistantChunk(payload={"message_id": message_id, "chunk": content}))
            
            summary_resp = AIMessage(content=full_summary, id=message_id)
            
            return {"research_data": data, "messages": state["messages"] + [summary_resp]}

        async def plan_node(state: AgentState):
            company = state["entities"].get("company")
            region = state["entities"].get("region")
            if not region:
                region = "General"
            
            if not company:
                await send_callback(
                    AssistantChunk(
                        payload={"message_id": "err_plan", "chunk": "I need to know the company name to generate a plan."}
                    )
                )
                return {"messages": state["messages"] + [AIMessage(content="I need to know the company name to generate a plan.")]}
            
            # Perform Research
            await send_callback(
                StatusUpdate(
                    payload={"stage": "research", "message": f"Gathering information on {company}..."}
                )
            )
            research_data = await self.research_service.research_company(company, region, send_callback)

            # Generate Plan
            await send_callback(
                StatusUpdate(
                    payload={"stage": "planning", "message": f"Generating plan for {company}..."}
                )
            )
            
            structured_llm = self.llm.with_structured_output(AccountPlan)

            # RAG retrieval
            existing_knowledge = ""
            try:
                docs = await self.knowledge_base.search(f"Overview and strategy for {company}", company=company)
                if docs:
                    existing_knowledge = "\n\n".join(docs)

            except Exception as e:
                logger.warning(f"Failed to search KB in plan_node: {e}")
            
            prompt = PromptConfig.PlanGeneration.value.SYSTEM_PROMPT.format(
                company=company,
                research_data=json.dumps(research_data),
                existing_knowledge=existing_knowledge
            )
            
            try:
                plan_obj = await structured_llm.ainvoke(prompt)
      
                plan_data = plan_obj.dict()
                
                plan_db_data = {"company": company, "sections": plan_data}
                if state.get("user_id"):
                    plan_db_data["user_id"] = state["user_id"]
                
                saved = await self.plan_service.create_plan(plan_db_data)
                
                if saved and isinstance(saved, dict) and "id" in saved:
                    plan_id = saved["id"]
                    # Save research data linked to plan
                    await self.research_service.save_research(company, research_data, plan_id, user_id=state.get("user_id"))
                    
                    # Stream the plan as markdown
                    markdown_plan = f"# Account Plan for {company}\n\n"
                    for section, content in plan_data.items():
                        await send_callback(
                            PlanUpdate(
                                payload={"plan_id": plan_id, "section": section, "content": content}
                            )
                        )
                        
                        # Format as markdown
                        markdown_plan += f"## {section.replace('_', ' ').title()}\n"
                        if isinstance(content, list):
                            for item in content:
                                markdown_plan += f"- {item}\n"
                        else:
                            markdown_plan += f"{content}\n"
                        markdown_plan += "\n"
                    
                    # Stream the markdown content
                    message_id = str(uuid.uuid4())
                    await send_callback(
                        AssistantChunk(
                            payload={"message_id": message_id, "chunk": markdown_plan}
                        )
                    )
                    
                else:
                    logger.error("Failed to save plan, skipping research save.")
                    await send_callback(AssistantChunk(payload={"message_id": "err_save", "chunk": "Failed to save the generated plan."}))
                
                return {"plan_data": plan_data, "messages": state["messages"] + [AIMessage(content=f"I have generated the account plan for {company}.")]}
            
            except Exception as e:
                logger.error(f"Plan generation failed: {e}")
                await send_callback(AssistantChunk(payload={"message_id": "err_1", "chunk": "Failed to generate plan."}))
                return {}

        async def edit_node(state: AgentState):
            company = state["entities"].get("company")
            section = state["entities"].get("section")
            
            if not company or not section:
                await send_callback(
                    AssistantChunk(
                        payload={"message_id": "err_edit", "chunk": "I need both the company name and the section to edit."}
                    )
                )
                return {}

            await send_callback(
                StatusUpdate(
                    payload={"stage": "planning", "message": f"Updating {section} for {company}..."}
                )
            )
            
            # Fetch existing plan
            plan = await self.plan_service.get_latest_plan_by_company(company, user_id=state.get("user_id"))
            if not plan:
                await send_callback(
                    AssistantChunk(
                        payload={"message_id": "err_edit", "chunk": f"No existing plan found for {company}."}
                    )
                )
                return {}
            
            current_content = plan.get("sections", {}).get(section, "")
            plan_id = plan["id"]
            
            # RAG retrieval
            existing_knowledge = ""
            try:
                # Use the user's instruction as the query
                query = state['messages'][-1].content
                docs = await self.knowledge_base.search(query, company=company)
                if docs:
                    existing_knowledge = "\n\n".join(docs)
            except Exception as e:
                logger.warning(f"Failed to search KB in edit_node: {e}")

            # Generate new content
            list_fields = ["strategic_priorities", "opportunities", "risks"]
            
            if section in list_fields:                
                structured_llm = self.llm.with_structured_output(ListSectionUpdate)
                
                prompt = PromptConfig.EditListSection.value.SYSTEM_PROMPT.format(
                    section=section,
                    company=company,
                    current_content=json.dumps(current_content),
                    existing_knowledge=existing_knowledge,
                    user_instruction=state['messages'][-1].content
                )
                
                try:
                    response = await structured_llm.ainvoke(prompt)
                    new_content = response.items
                except Exception as e:
                    logger.error(f"Failed to generate list update: {e}")
                    await send_callback(
                        AssistantChunk(
                            payload={"message_id": "err_edit", "chunk": "Failed to update list section."}
                        )
                    )
                    return {}
            else:
                # Text fields
                prompt = PromptConfig.EditTextSection.value.SYSTEM_PROMPT.format(
                    section=section,
                    company=company,
                    current_content=current_content,
                    existing_knowledge=existing_knowledge,
                    user_instruction=state['messages'][-1].content
                )
                
                response = await self.llm.ainvoke(prompt)
                new_content = response.content
            
            # Update DB
            updated_plan = await self.plan_service.update_section(plan_id, section, new_content)
            
            if updated_plan:
                await send_callback(
                    PlanUpdate(
                        payload={"plan_id": plan_id, "section": section, "content": new_content}
                    )
                )
                await send_callback(
                    AssistantChunk(
                        payload={"message_id": "edit_done", "chunk": f"Updated {section} section."}
                    )
                )
            else:
                await send_callback(
                    AssistantChunk(
                        payload={"message_id": "err_save", "chunk": "Failed to save updates."}
                    )
                )
                
            msg_content = f"Updated {section} section." if updated_plan else "Failed to save updates."
            return {"messages": state["messages"] + [AIMessage(content=msg_content)]}

        async def chat_node(state: AgentState):
            company = state["entities"].get("company")
            context_text = ""
            
            if company:
                # We assume the last message is the query
                last_msg = state["messages"][-1].content
                docs = await self.knowledge_base.search(last_msg, company=company)
                if docs:
                    context_text = "\n\n".join(docs)
            
            # Construct prompt with context
            messages = state["messages"]
            if context_text:
                system_msg = PromptConfig.ChatContext.value.SYSTEM_PROMPT.format(
                    company=company,
                    context_text=context_text
                )
                messages = [HumanMessage(content=system_msg)] + messages
            
            message_id = str(uuid.uuid4())
            
            full_response = ""
            async for chunk in self.llm.astream(messages):
                content = chunk.content
                if content:
                    full_response += content
                    await send_callback(
                        AssistantChunk(
                            payload={"message_id": message_id, "chunk": content}
                        )
                    )
            
            response = AIMessage(content=full_response, id=message_id)
            return {"messages": state["messages"] + [response]}

        # Graph construction
        
        workflow = StateGraph(AgentState)
        
        workflow.add_node("analyze_intent", analyze_intent)
        workflow.add_node("research_agent", research_node)
        workflow.add_node("plan_agent", plan_node)
        workflow.add_node("edit_agent", edit_node)
        workflow.add_node("chat_agent", chat_node)
        
        workflow.set_entry_point("analyze_intent")
        
        def route(state: AgentState):
            intent = state["intent"]
            if intent == "research_company":
                return "research_agent"
            elif intent == "generate_plan":
                return "plan_agent"
            elif intent == "edit_section":
                return "edit_agent"
            else:
                return "chat_agent"

        workflow.add_conditional_edges(
            "analyze_intent",
            route,
            {
                "research_agent": "research_agent",
                "plan_agent": "plan_agent",
                "edit_agent": "edit_agent",
                "chat_agent": "chat_agent"
            }
        )
        
        workflow.add_edge("research_agent", END)
        workflow.add_edge("plan_agent", END)
        workflow.add_edge("edit_agent", END)
        workflow.add_edge("chat_agent", END)
        
        app = workflow.compile()
        
        # Fetch chat history
        history_messages = []
        try:
            # Fetch last 10 messages for context
            hist_res = await supabase.table("messages")\
                .select("*")\
                .eq("conversation_id", session_id)\
                .order("created_at", desc=True)\
                .limit(10)\
                .execute()
            
            if hist_res.data:
                # Reverse to chronological order
                for msg in reversed(hist_res.data):
                    if msg["role"] == "user":
                        history_messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        history_messages.append(AIMessage(content=msg["content"]))
        except Exception as e:
            logger.error(f"Failed to fetch chat history: {e}")

        # check if the last message in history is the current one.
        
        current_msg_obj = HumanMessage(content=message_text)
        
        if history_messages and history_messages[-1].content == message_text:
            pass
        else:
            # It wasn't in the fetch, add it.
            history_messages.append(current_msg_obj)

        initial_state = {
            "messages": history_messages,
            "session_id": session_id,
            "intent": "",
            "entities": {},
            "research_data": {},
            "plan_data": {},
            "user_id": user_id
        }
        
        final_state = await app.ainvoke(initial_state)
        
        # Assume the last message in 'messages' is the ai's response if it's an AIMessage.
        
        last_msg = final_state["messages"][-1]
        if isinstance(last_msg, AIMessage) and save_messages:
            try:
                msg_data = {
                    "conversation_id": session_id,
                    "role": "assistant",
                    "content": last_msg.content
                }
                if last_msg.id:
                    msg_data["id"] = last_msg.id
                    
                await supabase.table("messages")\
                    .insert(msg_data)\
                    .execute()
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")

    async def aclose(self):
        if self.research_service:
            await self.research_service.aclose()
