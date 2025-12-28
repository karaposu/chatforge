# siluetService with Chatforge:

  from chatforge import get_llm
  from chatforge.adapters.storage.models.models import Message, Participant
  from langchain_core.messages import HumanMessage

  class SiluetService:
      def __init__(self, user_id, chat_id, request, storage_session):
          self.llm = get_llm(provider="openai", model=request.model or "gpt-4o-mini")
          self.session = storage_session
          # ... rest of init

      def _process_request(self):
          # 1. Fetch history (Chatforge storage)
          messages = self.session.query(Message).filter(
              Message.chat_id == self.chat_id
          ).order_by(Message.created_at.desc()).limit(20).all()

          conversation_memory_str = "\n".join([
              f"{m.sender_name}: {m.content}" for m in reversed(messages)
          ])

          # 2. Build prompt (YOUR domain logic - keep this)
          context = StepContext(
              conversation_memory=conversation_memory_str,
              player_input=self.request.player_input,
              room_context=...,
              # ... all your game context
          )
          full_prompt = context.compile()  # ← Your code, unchanged

          # 3. Call LLM (Chatforge)
          response = self.llm.invoke([HumanMessage(content=full_prompt)])
          llm_response = response.content

          # 4. Save messages (Chatforge storage with metadata)
          player_msg = Message(
              chat_id=self.chat_id,
              role="user",
              content=self.request.player_input,
              sender_name="Player",
              metadata_={"siluet_request_data": self.request.dict()}  # Game data
          )
          self.session.add(player_msg)

          ai_msg = Message(
              chat_id=self.chat_id,
              role="assistant",
              content=llm_response,
              sender_name="Silüet"
          )
          self.session.add(ai_msg)
          self.session.commit()