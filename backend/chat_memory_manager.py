from langchain_core.prompts import PromptTemplate

class ChatMemoryManager:
    def __init__(self, llm, max_recent=10):
        self.llm = llm
        self.messages = []
        self.max_recent = max_recent
        self.memory_summary = ""

    def add_message(self, message):
        self.messages.append(message)
        if len(self.messages) > self.max_recent:
            self.summarize_older_messages()

    def summarize_older_messages(self):
        old_messages = self.messages[:-self.max_recent]
        summary_prompt = PromptTemplate.from_template(
            "Summarize the following chat history such that important details should remain:\n{messages}"
        )
        text = "\n".join([f"{m.type.upper()}: {m.content}" for m in old_messages])
        summary_input = summary_prompt.format(messages=text)
        summary_output = self.llm.invoke(summary_input)
        self.memory_summary = str(summary_output)
        self.messages = self.messages[-self.max_recent:]  # Keep only recent ones

    def get_recent_messages(self):
        return [msg.content for msg in self.messages]

    def get_summary(self):
        return self.memory_summary
