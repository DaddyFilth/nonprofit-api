import os
from typing import Optional, List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class OutreachEngine:
    """Generates outreach and donation marketing emails using a fixed system prompt.

    The system prompt encodes brand identity, mission, required materials list, impact & tax language,
    and a mandatory signature block. It must always be applied as the system message.
    """

    def __init__(self, prompt_path: str = "app/prompts/outreach_system_prompt.txt", model: Optional[str] = None):
        self.prompt_path = prompt_path
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o")
        self.llm = ChatOpenAI(model=self.model, temperature=0)
        self.system_text = self._load_prompt()

    def _load_prompt(self) -> str:
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    async def generate_email(
        self,
        company_name: Optional[str] = None,
        contact_name: Optional[str] = None,
        project_context: Optional[str] = None,
        materials: Optional[List[Dict[str, str]]] = None,
        call_to_action: Optional[str] = None,
    ) -> str:
        """Generate a ready-to-send outreach email body.

        Args:
            company_name: The organization we are contacting.
            contact_name: The recipient’s name.
            project_context: Brief context about upcoming projects or neighborhoods served.
            materials: Optional explicit materials list. Each item is a dict with keys:
                - name: item name
                - use: short explanation how it restores safe living conditions
            call_to_action: Specific next step or timeline to request.
        """

        # Build a simple human prompt payload; the system prompt enforces formatting & signature
        lines = []
        if contact_name:
            lines.append(f"Recipient: {contact_name}")
        if company_name:
            lines.append(f"Company: {company_name}")
        if project_context:
            lines.append(f"Project context: {project_context}")

        if materials:
            lines.append("Materials to request (override or expand as appropriate):")
            for m in materials:
                name = m.get("name", "").strip()
                use = m.get("use", "").strip()
                if name:
                    if use:
                        lines.append(f"- {name} — {use}")
                    else:
                        lines.append(f"- {name}")

        if call_to_action:
            lines.append(f"Call to action: {call_to_action}")

        human = "\n".join(lines).strip() or "Generate an initial outreach email."

        messages = [
            SystemMessage(content=self.system_text),
            HumanMessage(content=human),
        ]

        resp = await self.llm.ainvoke(messages)
        return resp.content
